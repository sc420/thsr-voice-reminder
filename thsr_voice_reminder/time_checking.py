import bisect
import calendar
import datetime
import time

from thsr_voice_reminder.base import Base
from thsr_voice_reminder.thsr_api import ThsrApi


class TimeChecking(Base):
    # 30 minutes
    UPDATE_API_INTERVAL = 30 * 60

    def __init__(self, args, sound):
        self.args = args
        self.sound = sound

        self.logger = Base.create_logger('check', verbose=self.args.verbose)

        self.api = ThsrApi(self.args)

        self.init_stations_list()
        self.init_update_status()
        self.init_cached_api_data()

    # --------------------------------------------------------------------------
    # Initialization
    # --------------------------------------------------------------------------

    def init_stations_list(self):
        self.stations_list = None

    def init_update_status(self):
        self.last_update = time.time()

    def init_cached_api_data(self):
        self.timetable = None
        self.alert_info = None
        self.is_new_alert_info = False

    # --------------------------------------------------------------------------
    # Public Functions
    # --------------------------------------------------------------------------

    def check_and_get_actions(self):
        try:
            self.logger.info('Check and get action')

            self.api.init_api()
            self.update_api_data()

            self.update_stations_list()

            actions = []

            # Check train reminders
            for train in self.settings['trains']:
                enabled = train['enabled']

                if enabled:
                    repeat = train['repeat']

                    (weekday, short_weekday) = self.get_cur_weekday()

                    if weekday in repeat or short_weekday in repeat:
                        action = self.check_reminder_time(train)
                        if action is not None:
                            actions.append(action)

            # Check alert info
            alert_action = self.check_alert_info()
            if alert_action is not None:
                actions.append(alert_action)

            return actions
        except:
            self.logger.exception('Unable to check and get action')
            self.sound.notify_error()
            raise

    # --------------------------------------------------------------------------
    # Checking
    # --------------------------------------------------------------------------

    def check_reminder_time(self, train):
        station_orig = train['orig']
        station_dest = train['dest']
        time = train['time']
        where = train['target']['where']
        when = train['target']['when']
        reminders = train['reminders']

        # Sort the timetable based on where and when
        target_timetable = self.timetable[(station_orig, station_dest)]
        timetable_num = self.convert_timetable_to_num(target_timetable)
        sorted_timetable = self.sort_timetable(timetable_num, where, when)

        # Extract the times
        extracted_times = self.extract_times(sorted_timetable, where, when)

        # Find the train to remind
        train_index = self.find_train_to_remind(time, extracted_times)

        # Check whether the latest train is found
        if train_index >= 0:
            target_train = sorted_timetable[train_index]
            target_time = extracted_times[train_index]

            # Check each reminder
            for reminder in reminders:
                if self.is_time_to_remind(target_train, target_time, reminder):
                    return self.generate_reminder_action(
                        train, target_train, reminder)

        return None

    def find_train_to_remind(self, time, extracted_times):
        # Convert the time to number
        time_num = self.time_to_num(time)

        # Search the latest train
        return self.binary_search(extracted_times, time_num)

    def is_time_to_remind(self, train, time, reminder):
        now_num = self.get_cur_time_num()
        reminder_time = time - reminder['before_min']

        return now_num == reminder_time

    def check_alert_info(self):
        if self.is_new_alert_info:
            self.is_new_alert_info = False
            return self.generate_alert_action()
        else:
            return None

    # --------------------------------------------------------------------------
    # Action Generation
    # --------------------------------------------------------------------------

    def generate_reminder_action(self, train, target_train, reminder):
        m = {}

        # Cache the objects
        api_obj = target_train['_api_obj']
        where = train['target']['where']
        when = train['target']['when']

        now_num = self.get_cur_time_num()

        m['before_min'] = target_train[where][when] - now_num

        m['orig_arrival_hour'] = self.get_hour(
            target_train['orig']['arrival'], fixed=True)
        m['orig_arrival_min'] = self.get_minute(
            target_train['orig']['arrival'], fixed=True)
        m['orig_departure_hour'] = self.get_hour(
            target_train['orig']['departure'], fixed=True)
        m['orig_departure_min'] = self.get_minute(
            target_train['orig']['departure'], fixed=True)
        m['dest_arrival_hour'] = self.get_hour(
            target_train['dest']['arrival'], fixed=True)
        m['dest_arrival_min'] = self.get_minute(
            target_train['dest']['arrival'], fixed=True)
        m['dest_departure_hour'] = self.get_hour(
            target_train['dest']['departure'], fixed=True)
        m['dest_departure_min'] = self.get_minute(
            target_train['dest']['departure'], fixed=True)

        m['min_to_orig_arrival'] = target_train['orig']['arrival'] - now_num
        m['min_to_orig_departure'] = target_train['orig']['departure'] - now_num
        m['min_to_dest_arrival'] = target_train['dest']['arrival'] - now_num
        m['min_to_dest_departure'] = target_train['dest']['departure'] - now_num

        direction = api_obj['DailyTrainInfo']['Direction']
        m['direction_name'] = ['North', 'South'][direction]
        m['direction_name_tw'] = ['南下', '北上'][direction]

        m['train_number'] = api_obj['DailyTrainInfo']['TrainNo']

        orig_station_name = api_obj['OriginStopTime']['StationName']
        m['orig_station_name'] = orig_station_name['En']
        m['orig_station_name_tw'] = orig_station_name['Zh_tw']
        dest_station_name = api_obj['DestinationStopTime']['StationName']
        m['dest_station_name'] = dest_station_name['En']
        m['dest_station_name_tw'] = dest_station_name['Zh_tw']

        return {
            'sound_before': reminder['sound_before'],
            'voice': {
                'message': reminder['voice']['message'].format_map(m),
                'lang': reminder['voice']['lang'],
            },
        }

    def generate_alert_action(self):
        message = ''

        for alert in self.alert_info:
            message += '。'.join([
                '請注意高鐵有異常營運狀態',
                '狀態: {}'.format(alert['status']),
                '標題: {}'.format(alert['title']),
                '描述: {}'.format(alert['description']),
                '影響狀態: {}'.format(alert['effects']),
                '運行方向: {}'.format(alert['direction']),
                '運行區間: {}'.format(alert['effected_section']),
            ])

        return {
            'sound_before': self.settings['alert']['sound'],
            'voice': {
                'message': message,
                'lang': 'zh-tw',
            }
        }

    # --------------------------------------------------------------------------
    # Data Caching
    # --------------------------------------------------------------------------

    def update_stations_list(self):
        old_stations_list = self.stations_list
        new_stations_list = set()

        for train in self.settings['trains']:
            station_orig = train['orig']
            station_dest = train['dest']

            new_stations_list.add((station_orig, station_dest))

        self.stations_list = new_stations_list

        # Check whether the old stations list is outdated
        if new_stations_list != old_stations_list:
            # Need to update API data because the stations list has changed
            self.update_api_data(force=True)

    # --------------------------------------------------------------------------
    # API
    # --------------------------------------------------------------------------

    def update_api_data(self, force=False):
        now = time.time()
        date = datetime.datetime.today()

        old_alert_info = self.alert_info

        if force or (now - self.last_update > self.UPDATE_API_INTERVAL):
            self.logger.info('Update API data')

            # Update timetables for all station pair
            self.timetable = {}
            for (station_orig, station_dest) in self.stations_list:
                station_timetable = self.api.read_timetable(
                    station_orig, station_dest, date)
                self.timetable[(station_orig, station_dest)
                               ] = station_timetable

            new_alert_info = self.api.read_alert_info()
            self.alert_info = new_alert_info

            # Check for new alert info
            if new_alert_info != old_alert_info and old_alert_info is not None:
                self.is_new_alert_info = True

            self.last_check_timetable = time.time()

    # --------------------------------------------------------------------------
    # Time
    # --------------------------------------------------------------------------

    def get_cur_weekday(self):
        date = datetime.datetime.today()
        weekday = calendar.day_name[date.weekday()]
        short_weekday = weekday[:3]
        return (weekday, short_weekday)

    def get_cur_time_num(self):
        date = datetime.datetime.today()
        hour = date.hour
        minute = date.minute
        return self.hour_min_to_num(hour, minute)

    def get_hour(self, time_num, fixed=False):
        hour = time_num // 60
        if fixed:
            return '{:02d}'.format(hour)
        else:
            return hour

    def get_minute(self, time_num, fixed=False):
        minute = time_num % 60
        if fixed:
            return '{:02d}'.format(minute)
        else:
            return minute

    # --------------------------------------------------------------------------
    # Data Processing
    # --------------------------------------------------------------------------

    def convert_timetable_to_num(self, the_timetable):
        return map(lambda x: {
            'orig': {
                'arrival': self.time_to_num(x['orig']['arrival']),
                'departure': self.time_to_num(x['orig']['departure']),
            },
            'dest': {
                'arrival': self.time_to_num(x['dest']['arrival']),
                'departure': self.time_to_num(x['dest']['departure']),
            },
            '_api_obj': x['_api_obj'],
        }, the_timetable)

    def time_to_num(self, time):
        parts = time.split(':')
        return self.hour_min_to_num(int(parts[0]), int(parts[1]))

    def hour_min_to_num(self, hour, minute):
        return 60 * hour + minute

    def sort_timetable(self, timetable_num, where, when):
        return sorted(timetable_num, key=lambda x: x[where][when])

    def extract_times(self, timetable_num, where, when):
        return list(map(lambda x: x[where][when], timetable_num))

    def binary_search(self, lst, elem):
        """
        Perform binary search.

        References:
        * https://www.geeksforgeeks.org/binary-search-bisect-in-python/
        """
        i = bisect.bisect_left(lst, elem)
        if i:
            return i - 1
        else:
            return -1
