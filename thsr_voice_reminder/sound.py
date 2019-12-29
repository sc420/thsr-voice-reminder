import time

import vlc

from thsr_voice_reminder.base import Base


class Sound(Base):
    def __init__(self, args):
        super().__init__(self, args)

        self._init_vlc()

    def notify_error(self):
        self.play_sound('sound/Error Signal 2.mp3')
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
            self._logger.exception('Unable to play the sound')
            raise

    def _init_vlc(self):
        self.vlc_instance = vlc.Instance()
