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


class ArrayManager:

    @staticmethod
    def split_array(array: list, count: int):
        returnable = []
        for i in range(len(array) // count if len(array) % count == 0 else int(len(array) / count) + 1):
            returnable.append(array[count * i:count * (i + 1)])
        return returnable

