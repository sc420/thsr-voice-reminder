from concurrent.futures import ThreadPoolExecutor
from queue import Queue
import os
import time

import vlc

from thsr_voice_reminder.base import Base


class Sound(Base):
    def __init__(self, args):
        super().__init__(self, args)

        self._init_process_state()

    def notify_error(self):
        self.play_sound('sound/Error Signal 2.mp3')
        self.play_sound('voices/error_occurred.mp3')

    def play_sound(self, path):
        if path is None:
            return

        self._path_queue.put((path, False))

    def play_sound_and_delete(self, path):
        self._path_queue.put((path, True))

    def _init_process_state(self):
        self._executor = ThreadPoolExecutor()
        self._executor.submit(self._play)
        self._path_queue = Queue()

    def _play(self):
        while True:
            try:
                if not self._path_queue.empty():
                    (path, delete) = self._path_queue.get()

                    vlc_instance = vlc.Instance()

                    media = vlc_instance.media_new(path)
                    player = vlc_instance.media_player_new()

                    player.set_media(media)
                    player.play()

                    # Wait until the player state changes to ended
                    while player.get_state() != vlc.State.Ended:
                        time.sleep(0.1)

                    if delete:
                        os.unlink(path)

                # Sleep for an extra 1 second
                time.sleep(1)
            except:
                pass
