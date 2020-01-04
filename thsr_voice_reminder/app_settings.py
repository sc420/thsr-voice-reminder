import yaml

from thsr_voice_reminder.base import Base


class AppSettings(Base):
    def __init__(self, args):
        super().__init__(self, args)

        self._init_settings_state()

    def has_settings_changed(self):
        return self._has_settings_changed

    def iterate_schedule_items(self):
        for schedule_item in self._schedule_items:
            yield schedule_item

    def get_alert_sound(self):
        alert = self._settings.get('alert', {})
        return alert.get('sound', None)

    def load(self):
        with open(self._args.settings, 'r', encoding='utf-8') as stream:
            try:
                self._settings = yaml.safe_load(stream)
            except yaml.YAMLError:
                self._logger.exception('Unable to read the settings file')
                raise

        self._update_settings_change()
        self._build_schedule_items()

    def _init_settings_state(self):
        self._last_settings = None
        self._has_settings_changed = False

    def _update_settings_change(self):
        self._has_settings_changed = (self._settings != self._last_settings)
        if self._has_settings_changed:
            self._logger.info('The settings have been changed')
        self._last_settings = self._settings

    def _build_schedule_items(self):
        obj_list = self._settings.get('schedule', [])
        self._schedule_items = [ScheduleItem(index, obj)
                                for index, obj in enumerate(obj_list)]

    def __eq__(self, other):
        if other is None:
            return False
        return self._schedule_items == other._schedule_items


class ScheduleItem:
    def __init__(self, index, obj):
        self._index = index
        self._obj = obj

        self._build_reminders()

    def get_index(self):
        return self._index

    def iterate_reminders(self):
        for reminder in self._reminders:
            yield reminder

    def get_orig_dest(self):
        return (self._obj['orig'], self._obj['dest'])

    def get_time(self):
        return self._obj['time']

    def get_occasion_target(self):
        return (self._obj['target']['where'], self._obj['target']['when'])

    def is_enabled(self):
        return self._obj['enabled']

    def get_active_weekday(self):
        return self._obj['active_weekday']

    def get_reminders(self):
        return self._reminders

    def _build_reminders(self):
        obj_list = self._obj.get('reminders', [])
        self._reminders = [Reminder(index, obj)
                           for index, obj in enumerate(obj_list)]

    def __eq__(self, other):
        if other is None:
            return False
        return self._obj == other._obj

    def __str__(self):
        return 'obj={}, reminders={}'.format(self._obj, self._reminders)


class Reminder:
    def __init__(self, index, obj):
        self._index = index
        self._obj = obj

    def get_index(self):
        return self._index

    def get_remind_time_range(self, target_time):
        first_before_min = self._obj['before_min']
        last_before_min = self._obj.get('last_before_min', 0)
        first_remind_time = target_time - first_before_min
        last_remind_time = target_time - last_before_min
        return (first_remind_time, last_remind_time)

    def get_repeat(self):
        return self._obj.get('repeat', 1)

    def get_sound_before(self):
        return self._obj.get('sound_before', None)

    def get_formatted_voice_message(self, m):
        voice = self._obj.get('voice', {})
        message = voice.get('message', None)
        if message is None:
            return None
        else:
            return message.format_map(m)

    def get_voice_lang(self):
        voice = self._obj.get('voice', {})
        return voice.get('lang', None)

    def __eq__(self, other):
        if other is None:
            return False
        return self._obj == other._obj

    def __str__(self):
        return 'obj={}'.format(self._obj)
