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
            self.logger.info('Initialize API')

            self.init_auth()
            self.read_station()

            self.has_init = True

    def init_auth(self):
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                           ' AppleWebKit/537.36 (KHTML, like Gecko)'
                           ' Chrome/74.0.3729.169 Safari/537.36')}

    def read_station(self):
        self.logger.info('Read station')

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

    def read_timetable(self, station_orig, station_dest, date):
        self.logger.info('Read timetable, orig: {}, dest: {}, date: {}'.format(
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
                'orig': {
                    'arrival': orig_arrive_time,
                    'departure': orig_depart_time,
                },
                'dest': {
                    'arrival': dest_arrive_time,
                    'departure': dest_depart_time,
                },
                '_api_obj': timetable_obj,
            })

        return timetable

    def read_alert_info(self):
        self.logger.info('Read alert info')

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
