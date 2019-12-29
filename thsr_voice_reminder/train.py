from thsr_voice_reminder.time_utils import TimeUtils


class Train:
    def __init__(self, api_obj):
        self._api_obj = api_obj

    def get_occasion(self, where, when):
        occasion = {
            'orig': {
                'arrival': self.get_orig_arrival_time(),
                'departure': self.get_orig_depart_time(),
            },
            'dest': {
                'arrival': self.get_dest_arrival_time(),
                'departure': self.get_dest_depart_time(),
            },
        }

        occasion_where = occasion.get(where, None)
        if not occasion_where:
            raise ValueError('Unknown target where "{}"'.format(where))
        occasion_when = occasion_where.get(when, None)
        if not occasion_when:
            raise ValueError('Unknown target when "{}"'.format(when))
        return occasion_when

    def get_occasion_num(self, where, when):
        occassion = self.get_occasion(where, when)
        return TimeUtils.time_to_num(occassion)

    def get_daily_direction(self):
        return self._api_obj['DailyTrainInfo']['Direction']

    def get_daily_train_no(self):
        return self._api_obj['DailyTrainInfo']['TrainNo']

    def get_orig_station_name(self):
        return self._api_obj['OriginStopTime']['StationName']

    def get_orig_arrival_time(self):
        return self._api_obj['OriginStopTime']['ArrivalTime']

    def get_orig_depart_time(self):
        return self._api_obj['OriginStopTime']['DepartureTime']

    def get_dest_station_name(self):
        return self._api_obj['DestinationStopTime']['StationName']

    def get_dest_arrival_time(self):
        return self._api_obj['DestinationStopTime']['ArrivalTime']

    def get_dest_depart_time(self):
        return self._api_obj['DestinationStopTime']['DepartureTime']

    def __str__(self):
        texts = [
            'Train Number: {}'.format(self.get_daily_train_no()),
            'Origin Station Name: {}'.format(self.get_orig_station_name()),
            'Origin Arrival Time: {}'.format(self.get_orig_arrival_time()),
            'Origin Departure Time: {}'.format(self.get_orig_depart_time()),
            'Destination Station Name: {}'.format(
                self.get_dest_station_name()),
            'Destination Arrival Time: {}'.format(
                self.get_dest_arrival_time()),
            'Destination Departure Time: {}'.format(
                self.get_dest_depart_time()),
        ]
        return '\n'.join(texts)
