# coding=utf-8
import argparse
import os
import sys
import time
import traceback
import socket
import logging
from decimal import Decimal
from http.client import BadStatusLine
from urllib.error import URLError

import modules.Configuration as Config
import modules.Data as Data
import modules.Lending as Lending
import modules.MaxToLend as MaxToLend
from modules.Logger import Logger
import modules.PluginsManager as PluginsManager
from modules.ExchangeApiFactory import ExchangeApiFactory
from modules.ExchangeApi import ApiError


try:
    open('lendingbot.py', 'r')
except IOError:
    os.chdir(os.path.dirname(sys.argv[0]))  # Allow relative paths

parser = argparse.ArgumentParser()  # Start args.
parser.add_argument("-cfg", "--config", help="Location of custom configuration file, overrides settings below")
parser.add_argument("-dry", "--dryrun", help="Make pretend orders", action="store_true")
args = parser.parse_args()  # End args.

# Start handling args.
dry_run = bool(args.dryrun)
if args.config:
    config_location = args.config
else:
    config_location = 'default.cfg'
# End handling args.

# Config format: Config.get(category, option, default_value=False, lower_limit=False, upper_limit=False)
# A default_value "None" means that the option is required and the bot will not run without it.
# Do not use lower or upper limit on any config options which are not numbers.
# Define the variable from the option in the module where you use it.

Config.init(config_location)

output_currency = Config.get('BOT', 'outputCurrency', 'BTC')
end_date = Config.get('BOT', 'endDate')
exchange = Config.get_exchange()

json_output_enabled = Config.has_option('BOT', 'jsonfile') and Config.has_option('BOT', 'jsonlogsize')
jsonfile = Config.get('BOT', 'jsonfile', '')

# Configure web server
web_server_enabled = Config.getboolean('BOT', 'startWebServer')
if web_server_enabled:
    if json_output_enabled is False:
        # User wants webserver enabled. Must have JSON enabled. Force logging with defaults.
        json_output_enabled = True
        jsonfile = Config.get('BOT', 'jsonfile', 'www/botlog.json')

    import modules.WebServer as WebServer
    WebServer.initialize_web_server(Config)

# Configure logging
log = Logger(jsonfile, Decimal(Config.get('BOT', 'jsonlogsize', 200)), exchange)

# initialize the remaining stuff
api = ExchangeApiFactory.createApi(exchange, Config, log)
MaxToLend.init(Config, log)
Data.init(api, log)
Config.init(config_location, Data)
notify_conf = Config.get_notification_config()
if Config.has_option('MarketAnalysis', 'analyseCurrencies'):
    from modules.MarketAnalysis import MarketAnalysis
    # Analysis.init(Config, api, Data)
    analysis = MarketAnalysis(Config, api)
    analysis.run()
else:
    analysis = None
Lending.init(Config, api, log, Data, MaxToLend, dry_run, analysis, notify_conf)

# load plugins
PluginsManager.init(Config, api, log, notify_conf)
# Start dns cache managing
prv_getaddrinfo = socket.getaddrinfo
dns_cache = {}  # or a weakref.WeakValueDictionary()


def new_getaddrinfo(*urlargs):
    """Overloads the default socket dns resolution to have a cache,
    resets at the beginning of each loop.
    https://stackoverflow.com/questions/2236498/tell-urllib2-to-use-custom-dns"""
    try:
        return dns_cache[urlargs]
    except KeyError:
        res = prv_getaddrinfo(*urlargs)
        dns_cache[urlargs] = res
        return res


socket.getaddrinfo = new_getaddrinfo

print('Welcome to ' + Config.get("BOT", "label", "Lending Bot") + ' on ' + exchange)

try:
    while True:
        try:
            dns_cache = {}  # Flush DNS Cache
            Data.update_conversion_rates(output_currency, json_output_enabled)
            PluginsManager.before_lending()
            Lending.transfer_balances()
            Lending.cancel_all()
            Lending.lend_all()
            PluginsManager.after_lending()
            log.refreshStatus(Data.stringify_total_lent(*Data.get_total_lent()),
                              Data.get_max_duration(end_date, "status"))
            log.persistStatus()
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())
        except KeyboardInterrupt:
            # allow existing the main bot loop
            raise
        except Exception as ex:
            logging.error(ex)
            # log.persistStatus()
            if 'Invalid API key' in str(ex):
                print( "!!! Troubleshooting !!!")
                print("Are your API keys correct? No quotation. Just plain keys.")
                exit(1)
            elif 'Nonce must be greater' in str(ex):
                print( "!!! Troubleshooting !!!")
                print("Are you reusing the API key in multiple applications? Use a unique key for every application.")
                exit(1)
            elif 'Permission denied' in str(ex):
                print("!!! Troubleshooting !!!")
                print("Are you using IP filter on the key? Maybe your IP changed?")
                exit(1)
            elif 'timed out' in str(ex):
                print("Timed out, will retry in " + str(Lending.get_sleep_time()) + "sec")
            elif isinstance(ex, BadStatusLine):
                print("Caught BadStatusLine exception from Poloniex, ignoring.")
            elif 'Error 429' in str(ex):
                additional_sleep = max(130.0-Lending.get_sleep_time(), 0)
                sum_sleep = additional_sleep + Lending.get_sleep_time()
                logging.error('IP has been banned due to many requests. Sleeping for {} seconds'.format(sum_sleep))
                if Config.has_option('MarketAnalysis', 'analyseCurrencies'):
                    if api.req_period <= api.default_req_period * 1.5:
                        api.req_period += 1000
                    if Config.getboolean('MarketAnalysis', 'ma_debug_log'):
                        print("Caught ERR_RATE_LIMIT, sleeping capture and increasing request delay. Current"
                              " {0}ms".format(api.req_period))
                        log.log_error('Expect this 130s ban periodically when using MarketAnalysis, it will fix itself')
                time.sleep(additional_sleep)
            # Ignore all 5xx errors (server error) as we can't do anything about it (https://httpstatuses.com/)
            elif isinstance(ex, URLError):
                print("Caught {0} from exchange, ignoring.".format(ex.message))
            elif isinstance(ex, ApiError):
                print("Caught {0} reading from exchange API, ignoring.".format(ex.message))
            else:
                print(traceback.format_exc())
                print("v{0} Unhandled error, please open a Github issue so we can fix it!".format(Data.get_bot_version()))
                if notify_conf['notify_caught_exception']:
                    log.notify("{0}\n-------\n{1}".format(ex, traceback.format_exc()), notify_conf)
            sys.stdout.flush()
            time.sleep(Lending.get_sleep_time())


except KeyboardInterrupt:
    if web_server_enabled:
        WebServer.stop_web_server()
    PluginsManager.on_bot_exit()
    logging.debug('bye')
    print('bye')
    os._exit(0)  # Ad-hoc solution in place of 'exit(0)' TODO: Find out why non-daemon thread(s) are hanging on exit
