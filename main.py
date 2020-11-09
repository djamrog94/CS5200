import krakenex
from sqlalchemy import create_engine
import psycopg2
import psycopg2.extras
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import pytz
import time
import pandas as pd
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

UTC_TZ = pytz.timezone('UTC')
EST_TZ = pytz.timezone('America/New_York')


class DataGatherer:
    def __init__(self):
        self.k = krakenex.API()
        self.conn = None
        self.cur = None
        self.start, self.end = 0, 0
        self.data = []
        self.engine = ''
        self.columns = ['time', 'close']

        with open('db_cred.txt', 'r') as f:
            creds = f.readlines()
        self.db_name = creds[0].rstrip()
        self.username = creds[1].rstrip()
        self.password = creds[2].rstrip()

    def first_time(self):   
        self.connect_to_db()
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur.execute("CREATE DATABASE paperTrader")
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def convert_string_to_timestamp(self, date_string):
        dt = datetime.strptime(date_string, '%Y-%m-%d')
        return dt.replace(tzinfo=timezone.utc).timestamp()

    def convert_timestamp_to_date(self, date):
        return datetime.utcfromtimestamp(date)

    def convert_string_to_date(self, date):
        format = '%Y-%m-%d'
        return datetime.strptime(date, format)

    def create_db_engine(self):
        port = '5432'
        return create_engine(f'postgresql+psycopg2://{self.username}:{self.password}@localhost:{port}/{self.db_name}')

    def connect_to_db(self):
        self.conn = psycopg2.connect(f'dbname={self.db_name} user={self.username} password={self.password}')
        self.cur = self.conn.cursor()

    def collect_data(self, start, end, pair):
        """
        this function collects data, either from scratch or updates
        saves to postgresql
        EVERYTHING GOING IN MUST BE UTC!!! kraken returns all dates in utc TZ
        :param start str YYYY-MM-DD
        :param end str YYYY-MM-DD
        :return: N/A
        """
        self.pair = pair.uppper()
        print(f"Gathering data for {self.pair} for the time period of {start} - {end}.")
        print("-----------------------------------------------------------------------\n")
        # convert string to utc timestamp, for api
        self.start = self.convert_string_to_timestamp(start)
        self.end = self.convert_string_to_timestamp(end)

        last_param = str(int(self.start * (10 ** 9)))
        last = self.start

        while last < self.end:
            params = {'pair': self.pair,
             'interval': 1440,
              'since': last_param
              }
            resp = self.k.query_public('OHLC', params)
            while len(resp) < 2:
                print("Timed out... Sleeping for 30 seconds.")
                time.sleep(30)
                resp = self.k.query_public('OHLC', params)

            last_param = resp['result']['last']
            last = int(last_param) / (10 ** 9)
            self.data.extend(resp['result'][f'X{self.pair[:3]}Z{self.pair[3:]}'])
            print(f'{self.convert_timestamp_to_date(last)} | {datetime.now()}')
            time.sleep(1)

        # remove last row because next run will include this data
        for i in range(1, len(self.data)):
            if self.data[-i][2] < self.end:
                cut_off = i
                break
        self.data = self.data[:-cut_off + 1]

    def create_table(self):
        command = f'CREATE TABLE {self.pair} (price REAL, volume REAL, time VARCHAR(255),' \
                  f' BS VARCHAR(1), ML VARCHAR(1), misc VARCHAR(255))'
        self.connect_to_db()
        self.cur.execute(command)
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def insert_data_to_db(self):
        self.engine = self.create_db_engine()
        self.connect_to_db()
        
        df = pd.DataFrame(self.data)

        if len(df) > 0:
            # create (col1,col2,...)
            columns = ",".join(self.columns)

            # create VALUES('%s', '%s",...) one '%s' per column
            values = "VALUES({})".format(",".join(["%s" for _ in self.columns]))

            # create INSERT INTO table (columns) VALUES('%s',...)
            insert_stmt = f"INSERT INTO {self.pair} ({columns}) {values}"

            psycopg2.extras.execute_batch(self.cur, insert_stmt, df.values)
            self.conn.commit()
            self.cur.close()
            self.conn.close()
            # reset data for next collection
            self.data = []

    def get_asset_pairs(self):
        pairs = self.k.query_public('AssetPairs')
        return pairs['result'].keys()

def convert_timestamp_to_date(timestamp):
    temp = datetime.fromtimestamp(timestamp)
    return temp.replace(hour=0, minute=0, second=0, microsecond=0)


def convert_string_to_date(str_date):
    d = datetime.strptime(str_date, "%Y-%m-%d")
    return d.astimezone(UTC_TZ)


def convert_date_to_string(date):
    return datetime.strftime(date, "%Y-%m-%d")

def main():
    dg = DataGatherer()
    try:
        dg.first_time()
    except:
        'DB already exists'


if __name__ == '__main__':
    main()
