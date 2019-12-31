import bisect

from thsr_voice_reminder.action_generator import ActionGenerator
from thsr_voice_reminder.api_controller import ApiController
from thsr_voice_reminder.base import Base
from thsr_voice_reminder.time_utils import TimeUtils


class MainController(Base):
    MAX_NUM_ERRORS = 6

    def __init__(self, args):
        super().__init__(self, args)

        self._action_generator = ActionGenerator(self._args)
        self._api_controller = ApiController(self._args)

        self._init_settings_state()
        self._init_stations_set()
        self._init_remind_state()
        self._init_log_state()
        self._init_error_state()

    def update_settings(self, settings):
        super().update_settings(settings)
        self._action_generator.update_settings(settings)

    def run_and_get_actions(self):
        self._logger.info('Run and get actions')

        self._check_settings_changes()
        self._update_stations_set()
        if not self._try_update_api():
            return []

        reminder_actions = self._generate_reminder_actions()
        alert_actions = self._generate_alert_info()
        return reminder_actions + alert_actions

    def _init_settings_state(self):
        self._last_settings = None
        self._has_settings_changed = False

    def _init_stations_set(self):
        self._stations_set = None

    def _init_remind_state(self):
        self._last_remind_time = {}

    def _init_log_state(self):
        self._last_targets = None

    def _init_error_state(self):
        self._num_errors = 0

    def _check_settings_changes(self):
        if self._settings == self._last_settings:
            self._has_settings_changed = False
        else:
            self._logger.info('The settings have been changed')
            self._last_settings = self._settings
            self._has_settings_changed = True

    def _update_stations_set(self):
        if not self._has_settings_changed:
            return

        new_stations_set = set()
        for schedule_item in self._settings.iterate_schedule_items():
            orig_and_dest = schedule_item.get_orig_dest()
            new_stations_set.add(orig_and_dest)

        self._stations_set = new_stations_set

        self._api_controller.update(self._stations_set, force=True)

    def _try_update_api(self):
        try:
            self._api_controller.update(self._stations_set)
        except:
            self._num_errors += 1
            if self._num_errors <= self.MAX_NUM_ERRORS:
                self._logger.warning('Unable to update API, will retry later')
                return False
            else:
                self._logger.exception('Failed to update API')
                raise
        else:
            self._num_errors = 0
            return True

    def _generate_reminder_actions(self):
        actions = []
        targets = []
        for schedule_item in self._settings.iterate_schedule_items():
            if self._check_active_target(schedule_item):
                target = self._find_train_to_remind(schedule_item)
                targets.append(target)
                reminders_actions = self._check_reminder_time(
                    schedule_item, target)
                actions.extend(reminders_actions)

        self._log_trains_to_remind(targets)

        return actions

    def _check_active_target(self, schedule_item):
        if schedule_item.is_enabled():
            active_weekday = schedule_item.get_active_weekday()
            return TimeUtils.check_active_weekday(active_weekday)
        else:
            return False

    def _find_train_to_remind(self, schedule_item):
        orig_and_dest = schedule_item.get_orig_dest()
        remind_time = schedule_item.get_time()
        occasion_target = schedule_item.get_occasion_target()

        # Sort the timetable based on where and when
        trains = self._api_controller.get_timetable(orig_and_dest)
        sorted_timetable = self._sort_timetable(trains, occasion_target)

        # Extract the times
        extracted_times = self._extract_times(
            sorted_timetable, occasion_target)

        # Find the latest train to remind
        remind_index = self._find_latest_train(remind_time, extracted_times)
        if remind_index >= 0:
            target_train = sorted_timetable[remind_index]
            target_time = extracted_times[remind_index]
            return (target_train, target_time)
        else:
            return None

    def _check_reminder_time(self, schedule_item, target):
        if target is None:
            return None

        (target_train, target_time) = target

        # Check each reminder
        reminders_actions = []
        for reminder in schedule_item.iterate_reminders():
            remind_key = (schedule_item.get_index(), reminder.get_index())
            if ((not self._has_reminded(target_time, remind_key, reminder))
                    and self._is_time_to_remind(target_time, reminder)):
                self._update_last_remind_time(remind_key)
                action = self._action_generator.generate_reminder_action(
                    schedule_item, target_train, reminder)
                reminder_actions = [action] * reminder.get_repeat()
                reminders_actions.extend(reminder_actions)
        return reminders_actions

    def _find_latest_train(self, remind_time, extracted_times):
        time_num = TimeUtils.time_to_num(remind_time)

        # Search the latest train
        return self._binary_search(extracted_times, time_num)

    def _has_reminded(self, target_time, remind_key, reminder):
        if self._has_settings_changed:
            self._last_remind_time = {}
            return False

        (first_remind_time, last_remind_time) = reminder.get_remind_time_range(
            target_time)
        last_time = self._last_remind_time.get(remind_key, None)
        if last_time is None:
            return False
        else:
            return (first_remind_time <= last_time
                    and last_time <= last_remind_time)

    def _is_time_to_remind(self, target_time, reminder):
        now_num = TimeUtils.get_cur_time_num()
        (first_remind_time, last_remind_time) = reminder.get_remind_time_range(
            target_time)
        self._logger.debug(
            'now_num={}, first_remind_time={}, last_remind_time={}'.format(
                now_num, first_remind_time, last_remind_time))
        return first_remind_time <= now_num and now_num <= last_remind_time

    def _update_last_remind_time(self, remind_key):
        now_num = TimeUtils.get_cur_time_num()
        self._last_remind_time[remind_key] = now_num

    def _log_trains_to_remind(self, targets):
        if targets != self._last_targets:
            for target in targets:
                (target_train, _) = target
                self._logger.info(
                    'Train to remind: ...\n{}'.format(target_train))
            self._last_targets = targets

    def _generate_alert_info(self):
        actions = []
        alert_action = self._check_alert_info()
        if alert_action is not None:
            actions.append(alert_action)
        return actions

    def _check_alert_info(self):
        if self._api_controller.check_new_alert_info():
            alert_info = self._api_controller.get_alert_info()
            return self._action_generator.generate_alert_action(alert_info)
        else:
            return None

    def _sort_timetable(self, trains, occasion_target):
        return sorted(trains, key=lambda t: t.get_occasion_num(occasion_target))

    def _extract_times(self, trains, occasion_target):
        return list(map(lambda t: t.get_occasion_num(occasion_target), trains))

    def _binary_search(self, lst, elem):
        """
        Performs binary search.

        References:
        * https://www.geeksforgeeks.org/binary-search-bisect-in-python/
        """
        i = bisect.bisect_left(lst, elem)
        if i:
            return i - 1
        else:
            return -1
