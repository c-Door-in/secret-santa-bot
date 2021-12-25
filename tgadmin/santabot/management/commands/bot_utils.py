import re
from datetime import datetime
from pytz import timezone

def datetime_from_str(date_str='', time_str='00:00:00'):
    """Parse date in string in %d.%m.%Y format and return datetime object."""

    if not date_str:
        return None

    res = re.search('\s*(\d{1,2}.\d{2}.\d{4})', date_str)
    if res is None:
        return None

    date_str_parsed = res.group(1)
    # TODO: вынести
    localtz = timezone('Europe/Moscow')

    return localtz.localize(
        datetime.strptime(
            f'{date_str_parsed} {time_str}',
            '%d.%m.%Y %H:%M:%S'
        )
    )
