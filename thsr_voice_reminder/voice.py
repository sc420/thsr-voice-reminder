import os
import tempfile

from gtts import gTTS

from thsr_voice_reminder.base import Base


class Voice(Base):
    def __init__(self, args, sound):
        # Save the arguments
        self.args = args
        self.sound = sound

        # Create the logger
        self.logger = Base.create_logger('voice', verbose=self.args.verbose)

    def make_voice(self, actions):
        for action in actions:
            self.logger.info('Take action: {}'.format(action))

            sound_before = action['sound_before']
            message = action['voice']['message']
            lang = action['voice']['lang']

            self.sound.play_sound(sound_before)
            self.play_voice(message, lang)

    def play_voice(self, message, lang):
        # Create a temporary file
        f = tempfile.NamedTemporaryFile(delete=False)

        # Convert speech to sound and save to the temporary file
        tts = gTTS(message, lang=lang)
        tts.save(f.name)

        # Play the speech
        self.sound.play_sound(f.name)

        # Close the temporary file
        f.close()

        # Remove the temporary file
        os.unlink(f.name)
