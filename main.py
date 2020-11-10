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

START_DATE = '2015-01-01'
END_DATE = '2020-08-19'

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
        self.columns = ['assetID', 'Time', 'Close']

        with open('db_cred.txt', 'r') as f:
            creds = f.readlines()
        self.db_name = creds[0].rstrip()
        self.username = creds[1].rstrip()
        self.password = creds[2].rstrip()

    def first_time(self):   
        self.connect_to_db()
        self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        self.cur.execute("CREATE DATABASE papertrader")
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def convert_string_to_timestamp(self, date_string):
        dt = datetime.strptime(date_string, '%Y-%m-%d')
        return dt.replace(tzinfo=timezone.utc).timestamp()

    def convert_timestamp_to_date(self, r):
        return datetime.utcfromtimestamp(r[0])

    def convert_string_to_date(self, date):
        format = '%Y-%m-%d'
        return datetime.strptime(date, format)

    def create_db_engine(self):
        port = '5432'
        return create_engine(f'postgresql+psycopg2://{self.username}:{self.password}@localhost:{port}/{self.db_name}')

    def connect_to_db(self):
        self.conn = psycopg2.connect(f'dbname={self.db_name} user={self.username} password={self.password}')
        self.cur = self.conn.cursor()

    def collect_data(self, pair):
        """
        this function collects data, either from scratch or updates
        saves to postgresql
        EVERYTHING GOING IN MUST BE UTC!!! kraken returns all dates in utc TZ
        :param start str YYYY-MM-DD
        :param end str YYYY-MM-DD
        :return: N/A
        """
        self.pair = pair.upper()
        
        params = {'pair': self.pair,
            'interval': 1440,
            }
        
        resp = self.k.query_public('OHLC', params)
        while len(resp) < 2:
                print("Timed out... Sleeping for 30 seconds.")
                time.sleep(30)
                resp = self.k.query_public('OHLC', params)
        #data = resp['result'][f'X{self.pair[:3]}Z{self.pair[3:6]}']
        data = resp['result'][self.pair]
        df = pd.DataFrame(data)
        df['assetid'] = self.pair
        df = df[['assetid', 0,4]]
        df['Time'] = df.apply(self.convert_timestamp_to_date, axis=1)
        df = df[['assetid','Time', 4]]
        return df

    def create_table(self):
        command = "CREATE TABLE IF NOT EXISTS public.Assets (assetID VARCHAR(255) PRIMARY KEY)"
        command1 = "CREATE TABLE IF NOT EXISTS public.History (assetID VARCHAR(255), Time VARCHAR(255), Close REAL, FOREIGN KEY (assetID) REFERENCES public.Assets (assetID), PRIMARY KEY (assetID, time))"
        self.connect_to_db()
        self.cur.execute(command)
        self.cur.execute(command1)
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def insert_data_to_db(self, data):
        self.engine = self.create_db_engine()
        self.connect_to_db()
        
        df = data

        if len(df) > 0:
            # create (col1,col2,...)
            columns = ",".join(self.columns)

            # create VALUES('%s', '%s",...) one '%s' per column
            values = "VALUES({})".format(",".join(["%s" for _ in self.columns]))

            # create INSERT INTO table (columns) VALUES('%s',...)
            insert_stmt = f"INSERT INTO public.History ({columns}) {values}"

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
    df = dg.collect_data('ETHUSDT')
    dg.insert_data_to_db(df)


if __name__ == '__main__':
    main()
