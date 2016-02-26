import re

from NotiCentr.poller import WeatherPoller

poller = None
weather_temp_alert_text_pattern = ("Temperature change alert:"
                                   "item: [a-z]+, today:-?[0-9]+(.[0-9]+)?, "
                                   "tomorrow:-?[0-9]+(.[0-9]+)?")
pattern = re.compile(weather_temp_alert_text_pattern)


def setup():
    global poller
    print "SETUP!"
    poller = WeatherPoller(city='kitchener')


def teardown():
    print "TEAR DOWN!"


def test_send_and_receive():
    global poller
    global pattern
    print "RUN"

    WeatherPoller.temperature_change_threshold = 0.0
    poller.poll_data()
    temperature_change_alert_list = poller.check_temperature_change()
    print "Temperature alert threshold:", \
        WeatherPoller.temperature_change_threshold
    print "Returned alert list:", temperature_change_alert_list
    for alert_text in temperature_change_alert_list:
        if not pattern.match(alert_text):
            raise Exception("poller.check_temperature_change() returns "
                            "text not matching alert pattern.\n"
                            "return text: %s" % alert_text)
