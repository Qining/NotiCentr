import logging

from openexchangerates import OpenExchangeRatesClient
from datetime import datetime
from datetime import timedelta

logging.basicConfig(level=logging.DEBUG)


class ExchangeRatesPoller(object):

    API_key = '7cf21b8b9b8f4b7a887a5cde5ae85949'
    API_fetch_interval = timedelta(hours=1)

    def __init__(self):
        self.client = OpenExchangeRatesClient(ExchangeRatesPoller.API_key)
        self.currencies = self.client.currencies()
        logging.info(
            "ExchangeRatesPoller initialized.\nSupported currencies:\n" +
            "\n".join([c + ": " + self.currencies[c] for c in self.currencies
                       ]))
        self.last_api_fetch_time = None

    def poll_data(self):
        if self.client is None or self.last_api_fetch_time is None \
                or (datetime.utcnow() - self.last_api_fetch_time >
                    ExchangeRatesPoller.API_fetch_interval):
            self.lastest = self.client.latest()
            self.rates = self.lastest['rates']
            self.last_api_fetch_time = datetime.utcnow()
            logging.info(' '.join(
                [self.__class__.__name__, ": poll_data() fetched new data at:",
                 self.last_api_fetch_time.isoformat()]))
        else:
            logging.info(' '.join([self.__class__.__name__, (
                ": poll_data() called within fetch "
                "interval threshold, use previous "
                "fetched data at:"), self.last_api_fetch_time.isoformat()]))

    def trigger_notification(self, message):
        print message

    def check_exchange_rates(self, currencies):
        rates = {}
        for c in currencies:
            if c.upper() not in self.rates:
                logging.error(' '.join([self.__class__.__name__, ": currency:",
                                        c, "not found in self.rates dict."]))
                raise Exception("Currency: %s Not recognized!" % c)
            rates[c] = float(self.rates[c.upper()])
            rates_str_lst = [
                "USD exchange rate to " + rc.upper() + ": " + str(rates[rc])
                for rc in rates
            ]
        rates_str = '\n'.join(rates_str_lst)

        logging.debug(' '.join([self.__class__.__name__,
                                ": check_exchange_rates()\n", rates_str]))

        return rates_str_lst
