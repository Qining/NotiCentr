import re

from NotiCentr.poller import ExchangeRatesPoller

poller = None
exchange_rates_text_pattern = ("USD exchange rate to "
                               "[A-Z]{3}: [0-9]+(.[0-9]+)?")
pattern = re.compile(exchange_rates_text_pattern)


def setup():
    global poller
    print "SETUP!"
    poller = ExchangeRatesPoller()


def teardown():
    print "TEAR DOWN!"


def test_usd_rate_equals_one():
    global poller
    global pattern
    print "RUN"

    poller.poll_data()
    rates_msg_lst = poller.check_exchange_rates(['usd'])
    for rate_text in rates_msg_lst:
        if not pattern.match(rate_text):
            raise Exception("poller.check_exchange_rates() returns "
                            "text not matching pattern.\n"
                            "return text: %s" % rate_text)
