import json
import requests

from thsr_voice_reminder.base import Base


class ThsrApi(Base):
    def __init__(self, args):
        self.args = args

        self.logger = Base.create_logger('api', verbose=self.args.verbose)

        # Mark the API uninitialized
        self.has_init = False

    def init_api(self):
        if not self.has_init:
            self.init_auth()
            self.read_station()

            self.has_init = True

    def init_auth(self):
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                           ' AppleWebKit/537.36 (KHTML, like Gecko)'
                           ' Chrome/74.0.3729.169 Safari/537.36')}

    def read_station(self):
        params = {'format': 'JSON'}
        station_list = self.get_data(
            'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/Station',
            params=params)

        # Build the mapping from name to ID
        self.name_to_id = {}
        for station in station_list:
            station_id = station['StationID']
            station_name = station['StationName']
            name_en = station_name['En']
            name_tw = station_name['Zh_tw']

            self.name_to_id[name_en] = station_id
            self.name_to_id[name_tw] = station_id

    def read_timetable(self, station_from, station_to, date):
        # Map the station name to IDs
        id_from = self.name_to_id.get(station_from, station_from)
        id_to = self.name_to_id.get(station_to, station_to)

        url = ('https://ptx.transportdata.tw'
               '/MOTC/v2/Rail/THSR/DailyTimetable/OD/{}/to/{}/{}').format(
            id_from, id_to, date)
        params = {'format': 'JSON'}
        timetable_list = self.get_data(url, params=params)

        # Build a list of timetable data
        timetable = []
        for timetable_obj in timetable_list:
            orig_stop_time = timetable_obj['OriginStopTime']
            dest_stop_time = timetable_obj['DestinationStopTime']

            orig_arrive_time = orig_stop_time['ArrivalTime']
            orig_depart_time = orig_stop_time['DepartureTime']
            dest_arrive_time = dest_stop_time['ArrivalTime']
            dest_depart_time = dest_stop_time['DepartureTime']

            timetable.append({
                'from': {
                    'arrival': orig_arrive_time,
                    'departure': orig_depart_time,
                },
                'to': {
                    'arrival': dest_arrive_time,
                    'departure': dest_depart_time,
                },
            })

        return timetable

    def read_alert_info(self):
        params = {'format': 'JSON'}
        alert_list = self.get_data(
            'https://ptx.transportdata.tw/MOTC/v2/Rail/THSR/AlertInfo',
            params=params)

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

    def get_data(self, url, params={}):
        try:
            r = requests.get(url, headers=self.headers, params=params)
            r.raise_for_status()
            text = r.text
            return json.loads(text)
        except:
            self.logger.exception('Failed to get station data')
            raise
