import datetime
import time

from thsr_voice_reminder.base import Base
from thsr_voice_reminder.thsr_api import ThsrApi


class ApiController(Base):
    # 60 minutes
    UPDATE_API_INTERVAL = 60 * 60

    def __init__(self, args):
        super().__init__(self, args)

        self._api = ThsrApi(self._args)

        self._init_update_status()
        self._init_cached_api_data()

    def update(self, stations_set, force=False):
        now = time.time()
        if force or (now - self._last_update > self.UPDATE_API_INTERVAL):
            self._logger.info('Update API data')

            self._api.init_api()
            self._update_api_data(stations_set)

            self._last_update = time.time()

    def get_timetable(self, orig_and_dest):
        return self._timetable[orig_and_dest]

    def get_alert_info(self):
        return self._alert_info

    def check_new_alert_info(self):
        has_new_alert_info = self._has_new_alert_info
        self._has_new_alert_info = False
        return has_new_alert_info

    def _init_update_status(self):
        self._last_update = time.time()

    def _init_cached_api_data(self):
        self._timetable = None
        self._alert_info = None
        self._has_new_alert_info = False

    def _update_api_data(self, stations_set):
        self._update_timetables(stations_set)
        self._update_alert_info()

    def _update_timetables(self, stations_set):
        date = datetime.datetime.today()
        self._timetable = {}
        for orig_and_dest in stations_set:
            (station_orig, station_dest) = orig_and_dest
            trains = self._api.read_timetable(station_orig, station_dest, date)
            self._timetable[orig_and_dest] = trains

    def _update_alert_info(self):
        new_alert_info = self._api.read_alert_info()

        # Check for new alert info
        if new_alert_info != self._alert_info and self._alert_info is not None:
            self._logger.debug('New alert info: {}'.format(self._alert_info))
            self._has_new_alert_info = True

        self._alert_info = new_alert_info
