import argparse
import time

from thsr_voice_reminder.app_settings import AppSettings
from thsr_voice_reminder.base import Base
from thsr_voice_reminder.main_controller import MainController
from thsr_voice_reminder.sound import Sound
from thsr_voice_reminder.voice import Voice


class ThsrVoiceReminder(Base):
    def __init__(self):
        self._args = self._parse_args()

        super().__init__(self, self._args)

    def run(self):
        self._app_settings = AppSettings(self._args)

        self._main_controller = MainController(self._args, self._app_settings)
        self._sound = Sound(self._args)
        self._voice = Voice(self._args, self._sound)

        self._run_forever()

    def _parse_args(self):
        parser = argparse.ArgumentParser(description='Run THSR voice reminder')

        parser.add_argument('--settings', type=str, help='Path of settings')
        parser.add_argument('--verbose', action='store_true',
                            help='Turn on verbose logging')

        return parser.parse_args()

    def _run_forever(self):
        self._logger.info('Start running forever')

        while True:
            self._check_time_and_make_sound()

            time.sleep(10)

    def _check_time_and_make_sound(self):
        try:
            self._app_settings.load()

            actions = self._main_controller.run_and_get_actions()

            self._voice.make_voice(actions)
        except:
            self._logger.exception('Unable to check time and make sound')
            self._sound.notify_error()
            raise


def main():
    reminder = ThsrVoiceReminder()
    reminder.run()


if __name__ == '__main__':
    main()
