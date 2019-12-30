import tempfile

from gtts import gTTS

from thsr_voice_reminder.base import Base


class Voice(Base):
    def __init__(self, args, sound):
        super().__init__(self, args)

        self._sound = sound

    def make_voice(self, actions):
        for action in actions:
            self._logger.info('Take action: {}'.format(action))

            sound_before = action['sound_before']
            message = action['voice']['message']
            lang = action['voice']['lang']

            self._sound.play_sound(sound_before)
            self.play_voice(message, lang)

    def play_voice(self, message, lang):
        # Create a temporary file
        f = tempfile.NamedTemporaryFile(delete=False)

        # Convert speech to sound and save to the temporary file
        tts = gTTS(message, lang=lang)
        tts.save(f.name)

        # Close the temporary file
        f.close()

        # Play the speech
        self._sound.play_sound_and_delete(f.name)
