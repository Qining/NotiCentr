import logging

from pyowm import OWM
from datetime import datetime
from datetime import timedelta

logging.basicConfig(level=logging.DEBUG)


class WeatherPoller(object):

    API_key = '9ef86a5c847ad6a5c67d09dd9b72e9a6'
    API_fetch_interval = timedelta(days=1)
    map_city_id = {'kitchener': 5992996}
    temperature_change_threshold = 5.0

    def __init__(self, city='kitchener'):
        if city in WeatherPoller.map_city_id:
            self.city_id = WeatherPoller.map_city_id[city]
        else:
            logging.error(' '.join([self.__class__.__name__, ": city:", city,
                                    "not found in map_city_id dict."]))
            raise Exception("city:", city, " not found in map_city_id dict.")

        self.owm = None
        self.last_api_fetch_time = None

    def poll_data(self):
        if self.owm is None or self.last_api_fetch_time is None \
                or self.forecast is None or \
                (datetime.utcnow() - self.last_api_fetch_time >
                 WeatherPoller.API_fetch_interval):
            self.owm = OWM(WeatherPoller.API_key)
            self.forecast = self.owm.daily_forecast_at_id(self.city_id)
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

    def check_temperature_change(self):
        weather_lst = self.forecast.get_forecast().get_weathers()
        today = datetime.utcnow()
        tomorrow = today + timedelta(days=1)
        today_temp = weather_lst[0].get_temperature(unit='celsius')
        tomorrow_temp = self.forecast.get_weather_at(tomorrow).get_temperature(
            unit='celsius')

        logging.debug(' '.join(
            [self.__class__.__name__, ": check_temperature_change", "\ntoday:",
             str(today_temp), "\ntomorrow", str(tomorrow_temp)]))

        alert_lst = []
        for item in today_temp:
            if abs(today_temp[item] - tomorrow_temp[
                    item]) >= WeatherPoller.temperature_change_threshold:
                alert_lst.append(
                    "Temperature change alert:"
                    "item: {key}, today:{today}, tomorrow:{tomorrow}".format(
                        key=item,
                        today=today_temp[item],
                        tomorrow=tomorrow_temp[item]))
        return alert_lst
