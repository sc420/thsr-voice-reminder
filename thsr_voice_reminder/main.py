import argparse
import time

import yaml

from thsr_voice_reminder.base import Base
from thsr_voice_reminder.sound import Sound
from thsr_voice_reminder.time_checking import TimeChecking
from thsr_voice_reminder.voice import Voice


class ThsrVoiceReminder(Base):
    def run(self):
        self.args = self.parse_args()

        self.logger = Base.create_logger('main', verbose=self.args.verbose)

        self.sound = Sound(self.args)

        self.time_checking = TimeChecking(self.args, self.sound)
        self.voice = Voice(self.args, self.sound)

        self.run_forever()

    def parse_args(self):
        # Create an argument parser
        parser = argparse.ArgumentParser(description='Run THSR voice reminder')

        # Add arguments
        parser.add_argument('--settings', type=str, help='Path of settings')
        parser.add_argument('--verbose', action='store_true',
                            help='Turn on verbose logging')

        # Parse the arguments and return
        return parser.parse_args()

    def run_forever(self):
        self.logger.info('Start running forever')

        while True:
            # Check the time and make sound
            self.check_time_and_make_sound()

            # Sleep for 10 seconds
            time.sleep(10)

    def check_time_and_make_sound(self):
        # Read the settings file
        settings = self.read_settings()

        # Update the settings
        self.update_settings(settings)
        self.sound.update_settings(settings)
        self.time_checking.update_settings(settings)
        self.voice.update_settings(settings)

        # Check the time and get the action
        action = self.time_checking.check_and_get_action()

        # Make the voice
        self.voice.make_voice(action)

    def read_settings(self):
        with open(self.args.settings, 'r', encoding='utf8') as stream:
            try:
                settings = yaml.safe_load(stream)
            except yaml.YAMLError:
                self.logger.exception('Unable to read the settings file')
                raise

            return settings


def main():
    # Create a voice reminder
    reminder = ThsrVoiceReminder()

    # Run the reminder
    reminder.run()


if __name__ == "__main__":
    main()
