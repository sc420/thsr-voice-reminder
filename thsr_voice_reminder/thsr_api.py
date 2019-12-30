import json
import requests

from thsr_voice_reminder.base import Base
from thsr_voice_reminder.train import Train


class ThsrApi(Base):
    def __init__(self, args):
        super().__init__(self, args)

        self._has_init = False

    def init_api(self):
        if not self._has_init:
            self._logger.debug('Initialize API')

            self._init_auth()
            self._read_station()

            self._has_init = True

    def read_timetable(self, station_orig, station_dest, date):
        self._logger.debug('Read timetable, orig={}, dest={}, date={}'.format(
            station_orig, station_dest, date))

        # Map the station name to IDs
        id_orig = self.name_to_id.get(station_orig, station_orig)
        id_dest = self.name_to_id.get(station_dest, station_dest)

        # Convert date to string (YYYY-MM-DD)
        date_str = date.strftime('%Y-%m-%d')

        url = ('https://ptx.transportdata.tw'
               '/MOTC/v2/Rail/THSR/DailyTimetable/OD/{}/to/{}/{}').format(
            id_orig, id_dest, date_str)
        params = {'format': 'JSON'}
        timetable_list = self._get_data(url, params=params)
        self._logger.debug('timetable_list={}'.format(timetable_list))

        trains = []
        for timetable_obj in timetable_list:
            train = Train(timetable_obj)
            trains.append(train)

        return trains

    def read_alert_info(self):
        self._logger.debug('Read alert info')

        params = {'format': 'JSON'}
        alert_list = self._get_data(
            'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/AlertInfo',
            params=params)
        self._logger.debug('alert_list={}'.format(alert_list))

        # Check the alert info
        alert_info = []
        for alert in alert_list:
            level = alert['Level']

            if level != 1:
                alert_info.append({
                    'status': alert.get('Status', ''),
                    'title': alert.get('Title', ''),
                    'description': alert.get('Description', ''),
                    'effects': alert.get('Effects', ''),
                    'direction': alert.get('Direction', ''),
                    'effected_section': alert.get('EffectedSection', ''),
                })

        return alert_info

    def _init_auth(self):
        self._headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                           ' AppleWebKit/537.36 (KHTML, like Gecko)'
                           ' Chrome/74.0.3729.169 Safari/537.36')}

    def _read_station(self):
        self._logger.debug('Read station')

        params = {'format': 'JSON'}
        station_list = self._get_data(
            'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/Station',
            params=params)
        self._logger.debug('station_list={}'.format(station_list))

        # Build the mapping from name to ID
        self.name_to_id = {}
        for station in station_list:
            station_id = station['StationID']
            station_name = station['StationName']
            name_en = station_name['En']
            name_tw = station_name['Zh_tw']

            self.name_to_id[name_en] = station_id
            self.name_to_id[name_tw] = station_id

    def _get_data(self, url, params={}):
        try:
            r = requests.get(url, headers=self._headers, params=params)
            r.raise_for_status()
            text = r.text
            return json.loads(text)
        except:
            self._logger.exception('Failed to get station data')
            raise
