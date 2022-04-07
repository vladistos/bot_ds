class TimeManager:

    @staticmethod
    def normalize(number):
        if len(str(number)) < 2:
            number = '0' + str(number)
            return number
        else:
            return number

    @staticmethod
    def get_formatted_time(seconds):
        minutes = seconds // 60
        hours = minutes // 60
        seconds = seconds - minutes * 60
        minutes = minutes - hours*60
        return f'{TimeManager.normalize(hours)}:{TimeManager.normalize(minutes)}:{TimeManager.normalize(seconds)}'
