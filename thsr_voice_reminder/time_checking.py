from thsr_voice_reminder.base import Base
from thsr_voice_reminder.thsr_api import ThsrApi


class TimeChecking(Base):
    def __init__(self, args, sound):
        self.args = args
        self.sound = sound

        self.logger = Base.create_logger('time', verbose=self.args.verbose)

        self.api = ThsrApi(self.args)

    def check_and_get_action(self):
        try:
            self.api.init_api()

            # TODO: Add logic
        except:
            self.logger.exception('Unable to check and get action')
            self.sound.notify_error()
            raise
