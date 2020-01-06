import datetime

from thsr_voice_reminder.base import Base
from thsr_voice_reminder.time_utils import TimeUtils


class ActionGenerator(Base):
    def __init__(self, args, app_settings):
        super().__init__(self, args)

        self._app_settings = app_settings

    def generate_reminder_action(self, schedule_item, target_train, reminder):
        self._logger.debug(
            'schedule_item={}, target_train={}, reminder={}'.format(
                schedule_item, target_train, reminder))

        m = {}

        occasion_target = schedule_item.get_occasion_target()

        now_num = TimeUtils.get_cur_time_num()

        m['before_min'] = TimeUtils.calc_time_diff(
            target_train.get_occasion(occasion_target), now_num)

        m['orig_arrival_hour'] = TimeUtils.get_hour(
            target_train.get_orig_arrival_time(), fixed=True)
        m['orig_arrival_min'] = TimeUtils.get_minute(
            target_train.get_orig_arrival_time(), fixed=True)
        m['orig_departure_hour'] = TimeUtils.get_hour(
            target_train.get_orig_depart_time(), fixed=True)
        m['orig_departure_min'] = TimeUtils.get_minute(
            target_train.get_orig_depart_time(), fixed=True)
        m['dest_arrival_hour'] = TimeUtils.get_hour(
            target_train.get_dest_arrival_time(), fixed=True)
        m['dest_arrival_min'] = TimeUtils.get_minute(
            target_train.get_dest_arrival_time(), fixed=True)
        m['dest_departure_hour'] = TimeUtils.get_hour(
            target_train.get_dest_depart_time(), fixed=True)
        m['dest_departure_min'] = TimeUtils.get_minute(
            target_train.get_dest_depart_time(), fixed=True)

        m['min_to_orig_arrival'] = TimeUtils.calc_time_diff(
            target_train.get_orig_arrival_time(), now_num)
        m['min_to_orig_departure'] = TimeUtils.calc_time_diff(
            target_train.get_orig_depart_time(), now_num)
        m['min_to_dest_arrival'] = TimeUtils.calc_time_diff(
            target_train.get_dest_arrival_time(), now_num)
        m['min_to_dest_departure'] = TimeUtils.calc_time_diff(
            target_train.get_dest_depart_time(), now_num)

        direction = target_train.get_daily_direction()
        m['direction_name'] = ['North', 'South'][direction]
        m['direction_name_tw'] = ['南下', '北上'][direction]

        m['train_number'] = target_train.get_daily_train_no()

        orig_station_name = target_train.get_orig_station_name()
        m['orig_station_name'] = orig_station_name['En']
        m['orig_station_name_tw'] = orig_station_name['Zh_tw']
        dest_station_name = target_train.get_dest_station_name()
        m['dest_station_name'] = dest_station_name['En']
        m['dest_station_name_tw'] = dest_station_name['Zh_tw']

        return {
            'sound_before': reminder.get_sound_before(),
            'voice': {
                'message': reminder.get_formatted_voice_message(m),
                'lang': reminder.get_voice_lang(),
            },
        }

    def generate_alert_action(self, alert_info):
        self._logger.debug('alert_info={}'.format(alert_info))

        message = ''

        for alert in alert_info:
            message += '。'.join([
                '請注意高鐵有異常營運狀態',
                '標題: {}'.format(alert['title']),
                '描述: {}'.format(alert['description']),
                '影響狀態: {}'.format(alert['effects']),
                '運行方向: {}'.format(alert['direction']),
                '運行區間: {}'.format(alert['effected_section']),
            ])

        return {
            'sound_before': self._app_settings.get_alert_sound(),
            'voice': {
                'message': message,
                'lang': 'zh-tw',
            }
        }
