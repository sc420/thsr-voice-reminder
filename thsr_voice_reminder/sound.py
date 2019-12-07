import time

import vlc

from thsr_voice_reminder.base import Base


class Sound(Base):
    def __init__(self, args):
        # Save the arguments
        self.args = args

        # Create the logger
        self.logger = Base.create_logger('sound', verbose=self.args.verbose)

        self.init_vlc()

    def init_vlc(self):
        self.vlc_instance = vlc.Instance()

    def notify_error(self):
        path = self.settings['error_handling']['sound']
        self.play_sound(path)

        self.play_sound('voices/error_occurred.mp3')

    def play_sound(self, path):
        try:
            media = self.vlc_instance.media_new(path)
            player = self.vlc_instance.media_player_new()

            player.set_media(media)
            player.play()

            # Wait until the player state changes to ended
            while player.get_state() != vlc.State.Ended:
                time.sleep(0.1)

            # Sleep for extra 1 second
            time.sleep(1)
        except:
            self.logger.exception('Unable to play the sound')
            raise
