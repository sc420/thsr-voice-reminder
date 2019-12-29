import datetime
import calendar


class TimeUtils:
    @staticmethod
    def calc_time_diff(time_obj1, time_obj2):
        time_num1 = TimeUtils.time_to_num(time_obj1)
        time_num2 = TimeUtils.time_to_num(time_obj2)
        return time_num1 - time_num2

    @staticmethod
    def check_active_weekday(repeat):
        date = datetime.datetime.today()
        full_weekday = date.strftime('%A')
        short_weekday = date.strftime('%a')
        return full_weekday in repeat or short_weekday in repeat

    @staticmethod
    def get_cur_time_num():
        date = datetime.datetime.today()
        hour = date.hour
        minute = date.minute
        return TimeUtils.hour_min_to_num(hour, minute)

    @staticmethod
    def get_hour(time_obj, fixed=False):
        time_num = TimeUtils.time_to_num(time_obj)
        hour = time_num // 60
        if fixed:
            return '{:02d}'.format(hour)
        else:
            return hour

    @staticmethod
    def get_minute(time_obj, fixed=False):
        time_num = TimeUtils.time_to_num(time_obj)
        minute = time_num % 60
        if fixed:
            return '{:02d}'.format(minute)
        else:
            return minute

    @staticmethod
    def hour_min_to_num(hour, minute):
        return 60 * hour + minute

    @staticmethod
    def time_to_num(time_obj):
        if type(time_obj) is str:
            parts = time_obj.split(':')
            return TimeUtils.hour_min_to_num(int(parts[0]), int(parts[1]))
        elif type(time_obj) is int:
            return time_obj
        else:
            raise ValueError('Unknown type')
