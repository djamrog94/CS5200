from sqlalchemy import create_engine
import psycopg2
import psycopg2.extras
from datetime import datetime
from datetime import timezone
import pytz
import pandas as pd
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import dash_bootstrap_components as dbc
import cryptowatch as cw


START_DATE = '2015-01-01'
END_DATE = '2020-08-19'

UTC_TZ = pytz.timezone('UTC')
EST_TZ = pytz.timezone('America/New_York')

EXCHANGE = 'KRAKEN'


class DataGatherer:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.start, self.end = 0, 0
        self.data = []
        self.engine = ''
        self.columns = ['assetID', 'Timestamp', 'Open', 'High', 'Low', 'Close']

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
        return datetime.utcfromtimestamp(float(r[0]))

    def convert_timestamp_to_date_single(self, ts):
        return datetime.utcfromtimestamp(float(ts))
    

    def convert_string_to_date(self, date):
        format = '%Y-%m-%d'
        return datetime.strptime(date, format)

    def create_db_engine(self):
        port = '5432'
        return create_engine(f'postgresql+psycopg2://{self.username}:{self.password}@localhost:{port}/{self.db_name}')

    def connect_to_db(self):
        self.conn = psycopg2.connect(f'dbname={self.db_name} user={self.username} password={self.password}')
        self.cur = self.conn.cursor()

    def create_asset(self, id, pair):
        self.connect_to_db()
        insert_st = f"INSERT INTO public.Assets VALUES ({id}, '{pair.upper()}')"
        self.cur.execute(insert_st)
    
    def collect_data(self, pair):
        """
        this function collects data, either from scratch or updates
        saves to postgresql
        EVERYTHING GOING IN MUST BE UTC!!! kraken returns all dates in utc TZ
        :param start str YYYY-MM-DD
        :param end str YYYY-MM-DD
        :return: N/A
        """
        data = cw.markets.get(f'{EXCHANGE}:{pair.upper()}', ohlc=True, periods=['1d'])
        df = pd.DataFrame(data.of_1d)
        id = self.get_asset_id(pair)
        df['assetID'] = id
        df = df[['assetID', 0, 1, 2, 3, 4]]
        df.drop_duplicates(subset=['assetID', 0], keep = False, inplace=True)
        if len(df) > 0:
            # create (col1,col2,...)
            columns = ",".join(self.columns)

            # create VALUES('%s', '%s",...) one '%s' per column
            values = "VALUES({})".format(",".join(["%s" for _ in self.columns]))

            # create INSERT INTO table (columns) VALUES('%s',...)
            insert_stmt = f"INSERT INTO public.History ({columns}) {values}"

            psycopg2.extras.execute_batch(self.cur, insert_stmt, df.values)

    def get_history(self, pair):
        self.connect_to_db()
        self.cur.execute(f"SELECT assetID FROM public.Assets WHERE name='{pair}'")
        id = self.cur.fetchone()
        self.cur.execute(f"SELECT Timestamp, Close FROM public.History WHERE assetID='{id[0]}'")
        data = self.cur.fetchall()
        df = pd.DataFrame(data)
        df['Time'] = df.apply(self.convert_timestamp_to_date, axis = 1)
        df = df[['Time', 1]]
        df.columns = ['Time', 'Close']
        return df
    
    def create_order(self, pair, open, close, amount):
        open = self.convert_string_to_timestamp(open)
        close = self.convert_string_to_timestamp(close)
        id = self.get_asset_id(pair)
        self.connect_to_db()
        insert_st = f"INSERT INTO public.Orders (assetID, openDate, closeDate, Quantity) VALUES ({id},'{open}', '{close}', {float(amount)})"
        self.cur.execute(insert_st)
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def get_order_details(self):
        self.connect_to_db()
        self.cur.execute(f"SELECT * FROM public.Orders")
        data = self.cur.fetchall()
        df = pd.DataFrame(data)
        df.columns = ['OrderID', 'AssetID', 'OpenDate', 'CloseDate', 'Quantity']
        return df

    def get_orders(self, pair):
        id = self.get_asset_id(pair)
        self.connect_to_db()
        self.cur.execute(f"SELECT openDate, closeDate FROM public.Orders WHERE assetID='{id}'")
        data = self.cur.fetchall()
        if len(data) == 0:
            return None, None
        open = [[],[]]
        close = [[],[]]
        for trade in data:
            self.cur.execute(f"SELECT Close FROM public.History WHERE Timestamp='{trade[0]}' AND assetID='{id}'")
            o_price = self.cur.fetchone()
            open[0].append(trade[0])
            open[1].append(o_price[0])
            self.cur.execute(f"SELECT Close FROM public.History WHERE Timestamp='{trade[1]}' AND assetID='{id}'")
            c_price = self.cur.fetchone()
            close[0].append(trade[1])
            close[1].append(c_price[0])
        open_df = pd.DataFrame({'Timestamp': open[0], 'Price': open[1]})
        close_df = pd.DataFrame({'Timestamp': close[0], 'Price': close[1]})
        open_df['Time'] = open_df.apply(self.convert_timestamp_to_date, axis = 1)
        open_df = open_df[['Time', 'Price']]
        open_df.columns = ['Time', 'Close']
        close_df['Time'] = close_df.apply(self.convert_timestamp_to_date, axis = 1)
        close_df = close_df[['Time', 'Price']]
        close_df.columns = ['Time', 'Close']

        return open_df, close_df

    def calc_profit(self, pair):
        start = 10_000
        date = '2015-01-01'
        if pair == 'port':
            sql_stmt1 = f"SELECT * FROM public.Orders ORDER BY closeDate"
        else:
            id = self.get_asset_id(pair)
            sql_stmt = f"SELECT * FROM public.Orders WHERE assetID='{id}' ORDER BY closeDate"
        # self.cur.execute(f"SELECT Timestamp, assetID, Close FROM public.History WHERE Timestamp='{o}' AND assetID='{id}'")
        self.connect_to_db()
        self.cur.execute(sql_stmt1)
        data = self.cur.fetchall()
        dates = []
        pl = []
        pl.append(start)
        dates.append(date)
        for d in data:
            id = d[1]
            o = d[2]
            c = d[3]
            q = d[4]
            self.cur.execute(f"SELECT Close FROM public.History WHERE Timestamp='{o}' AND assetID='{id}'")
            o_price = self.cur.fetchone()[0]
            self.cur.execute(f"SELECT Close FROM public.History WHERE Timestamp='{c}' AND assetID='{id}'")
            c_price = self.cur.fetchone()[0]
            dates.append(self.convert_timestamp_to_date([d[3]]))
            pl.append(((c_price / o_price - 1) * q) + q)
        pl = [sum(pl[:i]) for i in range(1,len(pl)+1)]
        return pd.DataFrame({'Time': dates, 'Balance': pl})

    def calc_daily_return(r):
        pass

    # def calc_profit(self, pair):
    #     start = 10_000
    #     start_date = '2015-01-01'
    #     end_date = '2020-08-19'
    #     start_ts = self.convert_timestamp_to_date_single(start_date)
    #     end_ts = self.convert_timestamp_to_date_single(end_date)

    #     if pair == 'port':
    #         sql_stmt = f"SELECT * FROM public.History WHERE Timestamp >= {start_ts} AND Timestamp <= {end_ts}"
    #         sql_stmt1 = f"SELECT * FROM public.Orders"
    #     else:
    #         id = self.get_asset_id(pair)
    #         sql_stmt = f"SELECT * FROM public.Orders WHERE assetID='{id}' ORDER BY closeDate"
    #     self.connect_to_db()
    #     self.cur.execute(sql_stmt)
    #     history = self.cur.fetchall()
    #     self.cur.execute(sql_stmt1)
    #     orders = self.cur.fetchall()
    #     df = pd.DataFrame(history)
    #     for i in range(len(history)):
    #         ts = history.iloc[i]['Timestamp']
            
    #     df['daily_return'] = df.apply(calc_daily_return, axis=1)

    #     dates = []
    #     pl = []
    #     pl.append(start)
    #     dates.append(date)
    #     for d in data:
    #         id = d[1]
    #         o = d[2]
    #         c = d[3]
    #         q = d[4]
    #         self.cur.execute(f"SELECT Close FROM public.History WHERE Timestamp='{o}' AND assetID='{id}'")
    #         o_price = self.cur.fetchone()[0]
    #         self.cur.execute(f"SELECT Close FROM public.History WHERE Timestamp='{c}' AND assetID='{id}'")
    #         c_price = self.cur.fetchone()[0]
    #         dates.append(self.convert_timestamp_to_date([d[3]]))
    #         pl.append(((c_price / o_price - 1) * q) + q)
    #     pl = [sum(pl[:i]) for i in range(1,len(pl)+1)]
    #     return pd.DataFrame({'Time': dates, 'Balance': pl})
   

    def create_table(self):
        command = "CREATE TABLE IF NOT EXISTS public.Assets (assetID INT PRIMARY KEY, name VARCHAR(255))"
        command1 = "CREATE TABLE IF NOT EXISTS public.History (assetID INT, Timestamp VARCHAR(255), Open REAL, High Real, Low Real, Close REAL, FOREIGN KEY (assetID) REFERENCES public.Assets (assetID), PRIMARY KEY (assetID, Timestamp))"
        command2 = "CREATE TABLE IF NOT EXISTS public.Orders (orderID SERIAL PRIMARY KEY, assetID INT, openDate VARCHAR(255), closeDate VARCHAR(255), Quantity REAL, FOREIGN KEY (assetID) REFERENCES public.Assets (assetID))"
        self.connect_to_db()
        self.cur.execute(command)
        self.cur.execute(command1)
        self.cur.execute(command2)
        self.cur.close()
        self.conn.commit()
        self.conn.close()

    def get_asset_pairs(self):
        resp = cw.markets.list(EXCHANGE)
        pairs = [x.pair.upper() for x in resp.markets]
        return pairs

    def get_asset_id(self, pair):
        resp = cw.markets.list(EXCHANGE)
        for market in resp.markets:
            if (market.pair).upper() == pair:
                return market.id




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
    dg.create_order('BTCEUR','2017-01-01' , '2018-01-01',500)

if __name__ == '__main__':
    main()
