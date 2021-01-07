# coding=utf-8
import datetime
import threading
import time

from plugins.Plugin import Plugin
import os
import json


class Rates(Plugin):
    def on_bot_init(self):
        super(Rates, self).on_bot_init()
        self.log.addSectionLog("plugins", "rates", { 'navbar': True })

        self.gap_bottom = int(self.config.get("BOT", "gapbottom", 40))
        self.gap_top = int(self.config.get("BOT", "gaptop", 200))
        self.activeCurrencies = self.config.get_all_currencies()
        self.currencies = self.config.get("RATES", "Currencies", "BTC")
        self.currencies = self.currencies.split(',')
        self.keep_days = int(self.config.get("RATES", "KeepDays", 10))

        self.rates_file = "www/rates.json"
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            try:
                self.dump_rates()
            finally:
                time.sleep(60*10)

    def before_lending(self):
        return

    def after_lending(self):
        return

    def dump_rates(self):
        for currency in self.currencies:
            loan_order = self.api.return_loan_orders(currency, 10000)

            btc_offer = 0
            gap_botom_offer = 0
            gap_top_offer = 0

            offer_sum = 0
            for offer in loan_order['offers']:
                offer_sum += float(offer['amount'])
                if btc_offer > 1 and gap_botom_offer == 0:
                    btc_offer = float(offer['rate'])
                if offer_sum > self.gap_bottom and gap_botom_offer == 0:
                    gap_botom_offer = float(offer['rate'])

                gap_top_offer = float(offer['rate'])
                if offer_sum > self.gap_top and gap_top_offer != 0:
                    break

            file_data = {}
            if os.path.isfile(self.rates_file):
                with open(self.rates_file, "r") as file:
                    file_data = json.loads(file.read())

            data = {}
            data[currency] = []
            d = datetime.datetime.utcnow()
            epoch = datetime.datetime(1970, 1, 1)
            t = (d - epoch).total_seconds()
            for row in file_data[currency]:
                if t-row[0] < self.keep_days*24*60*60:
                    data[currency].append(row)

            # update
            data[currency].append([int(t), btc_offer*100, gap_botom_offer*100])

            # Dump data to file
            with open(self.rates_file, "w") as file:
                file.write(json.dumps(data))

        # self.log.log("Rates Plugin: Rates updated.")
