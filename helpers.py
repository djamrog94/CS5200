from datetime import datetime, timezone
from enum import Enum

def convert_string_to_timestamp(date_string):
    dt = datetime.strptime(date_string, '%Y-%m-%d')
    return dt.replace(tzinfo=timezone.utc).timestamp()

def convert_timestamp_to_date(r):
    return datetime.utcfromtimestamp(float(r[0]))

def convert_timestamp_to_date_single(ts):
    return datetime.utcfromtimestamp(ts)


def convert_string_to_date(date):
    format = '%Y-%m-%d'
    return datetime.strptime(date, format)


class ResponseType(Enum):
    ONE = 1
    ALL = 2
    NONE = 3