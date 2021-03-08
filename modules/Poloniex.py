# coding=utf-8
import sys
import hashlib
import hmac
import json
import socket
import time
import urllib
import threading
from urllib.error import HTTPError

import modules.Configuration as Config
from modules.RingBuffer import RingBuffer
from modules.ExchangeApi import ExchangeApi
from modules.ExchangeApi import ApiError


def post_process(before):
    after = before

    # Add timestamps if there isnt one but is a datetime
    if 'return' in after:
        if isinstance(after['return'], list):
            for x in xrange(0, len(after['return'])):
                if isinstance(after['return'][x], dict):
                    if 'datetime' in after['return'][
                            x] and 'timestamp' not in after['return'][x]:
                        after['return'][x]['timestamp'] = float(
                            ExchangeApi.create_time_stamp(
                                after['return'][x]['datetime']))

    return after


class Poloniex(ExchangeApi):
    def __init__(self, cfg, log):
        super(Poloniex, self).__init__(cfg, log)
        self.cfg = cfg
        self.log = log
        self.APIKey = self.cfg.get("API", "apikey", None)
        self.Secret = self.cfg.get("API", "secret", None)
        self.req_per_period = 6
        self.default_req_period = 1000  # milliseconds
        self.req_period = self.default_req_period
        self.req_time_log = RingBuffer(self.req_per_period)
        self.lock = threading.RLock()
        socket.setdefaulttimeout(int(Config.get("BOT", "timeout", 30, 1, 180)))
        self.api_debug_log = self.cfg.getboolean("BOT", "api_debug_log")

    def limit_request_rate(self):
        super(Poloniex, self).limit_request_rate()

    def increase_request_timer(self):
        super(Poloniex, self).increase_request_timer()

    def decrease_request_timer(self):
        super(Poloniex, self).decrease_request_timer()

    def reset_request_timer(self):
        super(Poloniex, self).reset_request_timer()

    @ExchangeApi.synchronized
    def api_query(self, command, req=None):
        # keep the 6 request per sec limit
        self.limit_request_rate()

        if req is None:
            req = {}

        def _read_response(resp):
            resp_data = json.loads(resp.read())
            if 'error' in resp_data:
                raise ApiError(resp_data['error'])
            return resp_data

        try:
            if command == "returnTicker" or command == "return24hVolume":
                ret = urllib.request.urlopen(
                    f'https://poloniex.com/public?command={command}')
                return _read_response(ret)
            elif command == "returnOrderBook":
                ret = urllib.request.urlopen(
                         'https://poloniex.com/public?command=' +
                         command + '&currencyPair=' +
                         str(req['currencyPair']))
                return _read_response(ret)
            elif command == "returnMarketTradeHistory":
                ret = urllib.request.urlopen(
                          'https://poloniex.com/public?command=' +
                          "returnTradeHistory" + '&currencyPair=' +
                          str(req['currencyPair']))
                return _read_response(ret)
            elif command == "returnLoanOrders":
                req_url = ('https://poloniex.com/public?command=' +
                           "returnLoanOrders" + '&currency=' +
                           str(req['currency']))
                if req['limit'] > 0:
                    req_url += ('&limit=' + str(req['limit']))
                ret = urllib.request.urlopen(req_url)
                return _read_response(ret)
            else:
                req['command'] = command
                req['nonce'] = int(time.time() * 1000)
                post_data = urllib.parse.urlencode(req).encode('utf8')

                sign = hmac.new(self.Secret.encode('utf8'),
                                post_data,
                                hashlib.sha512).hexdigest()
                headers = {'Sign': sign, 'Key': self.APIKey}

                ret = urllib.request.urlopen(
                    urllib.request.Request('https://poloniex.com/tradingApi',
                                   post_data, headers))
                json_ret = _read_response(ret)
                return post_process(json_ret)

            # Check in case something has gone wrong and the timer is too big
            self.reset_request_timer()

        except HTTPError as ex:
            raw_polo_response = ex.read()
            try:
                data = json.loads(raw_polo_response)
                polo_error_msg = data['error']
            except:
                if hasattr(ex, 'code') and (ex.code == 502
                                            or ex.code in range(520, 527, 1)):
                    # 502 and 520-526 Bad Gateway so response is likely HTML from Cloudflare
                    polo_error_msg = 'API Error ' + str(ex.code) + \
                                     ': The web server reported a bad gateway or gateway timeout error.'
                elif hasattr(ex, 'code') and (ex.code == 429):
                    self.increase_request_timer()
                else:
                    polo_error_msg = raw_polo_response
            tt, vv, tb = sys.exc_info()
            raise RuntimeError(f'{str(ex)} - requesting {command} - Poloniex reports {polo_error_msg}')

              
        except Exception as ex:
            tt, vv, tb = sys.exc_info()
            raise RuntimeError(f'{str(ex)} - Requesting {request}')

    def return_ticker(self):
        return self.api_query("returnTicker")

    def return24h_volume(self):
        return self.api_query("return24hVolume")

    def return_order_book(self, currency_pair):
        return self.api_query("returnOrderBook",
                              {'currencyPair': currency_pair})

    def return_market_trade_history(self, currency_pair):
        return self.api_query("returnMarketTradeHistory",
                              {'currencyPair': currency_pair})

    def transfer_balance(self, currency, amount, from_account, to_account):
        return self.api_query(
            "transferBalance", {
                'currency': currency,
                'amount': amount,
                'fromAccount': from_account,
                'toAccount': to_account
            })

    # Returns all of your balances.
    # Outputs:
    # {"BTC":"0.59098578","LTC":"3.31117268", ... }
    def return_balances(self):
        return self.api_query('returnBalances')

    def return_available_account_balances(self, account):
        balances = self.api_query('returnAvailableAccountBalances',
                                  {"account": account})
        if isinstance(
                balances, list
        ):  # silly api wrapper, empty dict returns a list, which breaks the code later.
            balances = {}
        return balances

    # Returns your open orders for a given market, specified by the "currencyPair" POST parameter, e.g. "BTC_XCP"
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # orderNumber   The order number
    # type          sell or buy
    # rate          Price the order is selling or buying at
    # Amount        Quantity of order
    # total         Total value of order (price * quantity)
    def return_open_orders(self, currency_pair):
        return self.api_query('returnOpenOrders',
                              {"currencyPair": currency_pair})

    def return_open_loan_offers(self):
        loan_offers = self.api_query('returnOpenLoanOffers')
        if isinstance(
                loan_offers, list
        ):  # silly api wrapper, empty dict returns a list, which breaks the code later.
            loan_offers = {}
        return loan_offers

    def return_active_loans(self):
        return self.api_query('returnActiveLoans')

    def return_lending_history(self, start, stop, limit=500):
        return self.api_query('returnLendingHistory', {
            'start': start,
            'end': stop,
            'limit': limit
        })

    # Returns your trade history for a given market, specified by the "currencyPair" POST parameter
    # Inputs:
    # currencyPair  The currency pair e.g. "BTC_XCP"
    # Outputs:
    # date          Date in the form: "2014-02-19 03:44:59"
    # rate          Price the order is selling or buying at
    # amount        Quantity of order
    # total         Total value of order (price * quantity)
    # type          sell or buy
    def return_trade_history(self, currency_pair):
        return self.api_query('returnTradeHistory',
                              {"currencyPair": currency_pair})

    # Places a buy order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
    # If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is buying at
    # amount        Amount of coins to buy
    # Outputs:
    # orderNumber   The order number
    def buy(self, currency_pair, rate, amount):
        return self.api_query('buy', {
            "currencyPair": currency_pair,
            "rate": rate,
            "amount": amount
        })

    # Places a sell order in a given market. Required POST parameters are "currencyPair", "rate", and "amount".
    # If successful, the method will return the order number.
    # Inputs:
    # currencyPair  The curreny pair
    # rate          price the order is selling at
    # amount        Amount of coins to sell
    # Outputs:
    # orderNumber   The order number
    def sell(self, currency_pair, rate, amount):
        return self.api_query('sell', {
            "currencyPair": currency_pair,
            "rate": rate,
            "amount": amount
        })

    def create_loan_offer(self, currency, amount, duration, auto_renew,
                          lending_rate):
        return self.api_query(
            'createLoanOffer', {
                "currency": currency,
                "amount": amount,
                "duration": duration,
                "autoRenew": auto_renew,
                "lendingRate": lending_rate,
            })

    # Cancels an order you have placed in a given market. Required POST parameters are "currencyPair" and "orderNumber".
    # Inputs:
    # currencyPair  The curreny pair
    # orderNumber   The order number to cancel
    # Outputs:
    # succes        1 or 0
    def cancel(self, currency_pair, order_number):
        return self.api_query('cancelOrder', {
            "currencyPair": currency_pair,
            "orderNumber": order_number
        })

    def cancel_loan_offer(self, currency, order_number):
        return self.api_query('cancelLoanOffer', {
            "currency": currency,
            "orderNumber": order_number
        })

    # Immediately places a withdrawal for a given currency, with no email confirmation.
    # In order to use this method, the withdrawal privilege must be enabled for your API key.
    # Required POST parameters are "currency", "amount", and "address". Sample output: {"response":"Withdrew 2398 NXT."}
    # Inputs:
    # currency      The currency to withdraw
    # amount        The amount of this coin to withdraw
    # address       The withdrawal address
    # Outputs:
    # response      Text containing message about the withdrawal
    def withdraw(self, currency, amount, address):
        return self.api_query('withdraw', {
            "currency": currency,
            "amount": amount,
            "address": address
        })

    def return_loan_orders(self, currency, limit=0):
        return self.api_query('returnLoanOrders', {
            "currency": currency,
            "limit": limit
        })

    # Toggles the auto renew setting for the specified orderNumber
    def toggle_auto_renew(self, order_number):
        return self.api_query('toggleAutoRenew', {"orderNumber": order_number})
