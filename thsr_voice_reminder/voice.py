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

    def make_voice(self, action):
        self.play_voice('測試', 'zh-tw')
        self.play_voice('This is a test', 'en')

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
