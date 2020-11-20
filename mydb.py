import pymysql.cursors
import helpers
import cryptowatch as cw
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine

class Database():
    def __init__(self) -> None:
        self.name = 'paperTrader'
        self.columns = ['assetID', 'Timestamp', 'Open', 'High', 'Low', 'Close']
        self.exchange = 'KRAKEN'
        self.host = 'localhost'
        self.user = 'root'
        self.password = 'password'
        self.port = '3306'
        try:
            connection = self.create_connection()
            connection.close()
            print('Connected to db!')
        except:
            if self.first_time():
                print('Successfully set up new schema')
            else:
                print('Cannot find database. Make sure MySQL is running, and that "sys" db exists!')

    def create_connection(self):
        return pymysql.connect(host='localhost',
                        user='root',
                        password='password',
                        db=self.name,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)

    def create_engine(self):
        db_data = f'mysql+mysqldb://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?charset=utf8mb4'
        engine = create_engine(db_data)
        return engine
            
    def first_time(self):
        print('First time. Creating schema')
        try:
            connection = pymysql.connect(host='localhost',
                            user='root',
                            password='password',
                            db='sys',
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)
            with connection.cursor() as cursor:
                create_db_statement = "CREATE DATABASE IF NOT EXISTS paperTrader"
                use_stmt = 'USE paperTrader'
                create_asset_table_stmt = "CREATE TABLE Assets \
                     (assetID INT PRIMARY KEY, name VARCHAR(255) NOT NULL)"
                create_history_table_stmt = "CREATE TABLE IF NOT EXISTS History ( \
                            Timestamp INT, \
                            assetID INT, \
                            open REAL NOT NULL, \
                            high REAL NOT NULL, \
                            low REAL NOT NULL, \
                            close REAL NOT NULL, \
                            FOREIGN KEY (assetID) REFERENCES Assets(assetID) \
                            ON DELETE NO ACTION ON UPDATE CASCADE, \
                            PRIMARY KEY (assetID, Timestamp))"
                create_order_table_stmt = "CREATE TABLE Orders ( \
                            orderID INT AUTO_INCREMENT PRIMARY KEY, \
                            assetID INT, \
                            openDate INT NOT NULL, \
                            closeDate INT NOT NULL, \
                            quantity REAL NOT NULL, \
                            FOREIGN KEY (assetID) REFERENCES Assets(assetID) \
                            ON DELETE SET NULL ON UPDATE CASCADE);"
                crate_user_table_stmt = "CREATE TABLE Users ( \
                            userID INT AUTO_INCREMENT PRIMARY KEY, \
                            firstName VARCHAR(255) NOT NULL, \
                            lastName VARCHAR(255) NOT NULL);"
                create_accounts_table_stmt = "CREATE TABLE Accounts ( \
                            accountID INT AUTO_INCREMENT PRIMARY KEY, \
                            userID INT, \
                            openDate INT NOT NULL, \
                            startingBalance REAL NOT NULL, \
                            FOREIGN KEY (userID) REFERENCES Users(userID) \
                            ON DELETE SET NULL ON UPDATE CASCADE);"
                create_asset_detail_table_stmt = "CREATE TABLE Asset_Info ( \
                            assetName VARCHAR(255) PRIMARY KEY, \
                            assetID INT, \
                            altName VARCHAR(255) NOT NULL, \
                            assetClass VARCHAR(255) NOT NULL, \
                            FOREIGN KEY (assetID) REFERENCES Assets(assetID)\
                            ON DELETE SET NULL ON UPDATE CASCADE); "

                stmts = [create_db_statement,
                use_stmt,
                 create_asset_table_stmt,
                  create_history_table_stmt,
                  create_order_table_stmt,
                  crate_user_table_stmt,
                  create_accounts_table_stmt,
                  create_asset_detail_table_stmt]

                for stmt in stmts:
                    cursor.execute(stmt)
                connection.commit()
                connection.close()
            return True

        except:
            return False

    def send_query(self, query, response):
        connection = self.create_connection()
        try:
            with connection.cursor() as cursor:   
                # Read a single record
                cursor.execute(query)
                if response == helpers.ResponseType.ALL:
                    result = cursor.fetchall()
                elif response == helpers.ResponseType.ONE:
                    result = cursor.fetchone()
                else:
                    result = None
                return result
        finally:
            connection.commit()
            connection.close()

    def send_procedure(self, procedure, args, response):
        connection = self.create_connection()
        try:
            with connection.cursor() as cursor:  
                cursor.callproc(procedure, args)
                if response == helpers.ResponseType.ALL:
                    result = cursor.fetchall()
                elif response == helpers.ResponseType.ONE:
                    result = cursor.fetchone()
                else:
                    result = None
                return result
        finally:
            connection.commit()
            connection.close()

    def create_asset(self, id, pair):
        insert_st = f"INSERT INTO assets VALUES ({id}, '{pair.upper()}')"
        self.send_query(insert_st, helpers.ResponseType.NONE)

    def collect_data(self, pair):
        data = cw.markets.get(f'{self.exchange}:{pair.upper()}', ohlc=True, periods=['1d'])
        df = pd.DataFrame(data.of_1d)
        id = self.get_asset_id(pair)
        df['assetID'] = id
        df = df[['assetID', 0, 1, 2, 3, 4]]
        df.drop_duplicates(subset=['assetID', 0], keep = False, inplace=True)
        df.columns = self.columns
        engine = self.create_engine()
        df.to_sql('history', engine, if_exists='append', index=False)

    def get_history(self, pair):
        sql_stmt = f"SELECT assetID FROM assets WHERE name='{pair}'"
        id = self.send_query(sql_stmt, helpers.ResponseType.ONE)
        sql_stmt = f"SELECT Timestamp, Close FROM history WHERE assetID='{id['assetID']}'"
        data = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        df = pd.DataFrame(data)
        df['Time'] = df.apply(helpers.convert_timestamp_to_date, axis = 1)
        df = df[['Time', 'Close']]
        return df

    def create_order(self, pair, open, close, amount):
        open = helpers.convert_string_to_timestamp(open)
        close = helpers.convert_string_to_timestamp(close)
        id = self.get_asset_id(pair)
        sql_stmt = f"INSERT INTO Orders (assetID, openDate, closeDate, Quantity) VALUES ({id},{open}, {close}, {float(amount)})"
        self.send_query(sql_stmt, helpers.ResponseType.NONE)

    def get_order_details(self):
        sql_smt = f"SELECT * FROM Orders"
        data = self.send_query(sql_smt, helpers.ResponseType.ALL)
        df = pd.DataFrame(data)
        return df

    def get_orders(self, pair):
        id = self.get_asset_id(pair)
        sql_stmt = f"SELECT openDate, closeDate FROM Orders WHERE assetID='{id}'"
        data = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        if len(data) == 0:
            return None, None
        open = [[],[]]
        close = [[],[]]
        for trade in data:
            sql_stmt = f"SELECT Close FROM history WHERE Timestamp='{trade['openDate']}' AND assetID='{id}'"
            o_price = self.send_query(sql_stmt, helpers.ResponseType.ONE)
            open[0].append(trade['openDate'])
            open[1].append(o_price['Close'])
            sql_smt = f"SELECT Close FROM history WHERE Timestamp='{trade['closeDate']}' AND assetID='{id}'"
            c_price = self.send_query(sql_smt, helpers.ResponseType.ONE)
            close[0].append(trade['closeDate'])
            close[1].append(c_price['Close'])
        open_df = pd.DataFrame({'Timestamp': open[0], 'Price': open[1]})
        close_df = pd.DataFrame({'Timestamp': close[0], 'Price': close[1]})
        open_df['Time'] = open_df.apply(helpers.convert_timestamp_to_date, axis = 1)
        open_df = open_df[['Time', 'Price']]
        open_df.columns = ['Time', 'Close']
        close_df['Time'] = close_df.apply(helpers.convert_timestamp_to_date, axis = 1)
        close_df = close_df[['Time', 'Price']]
        close_df.columns = ['Time', 'Close']

        return open_df, close_df

    # def calc_profit(self, pair):
    #     start = 10_000
    #     date = '2015-01-01'
    #     if pair == 'port':
    #         sql_stmt1 = f"SELECT * FROM Orders ORDER BY closeDate"
    #     else:
    #         id = self.get_asset_id(pair)
    #         sql_stmt = f"SELECT * FROM Orders WHERE assetID='{id}' ORDER BY closeDate"
    #     # self.cur.execute(f"SELECT Timestamp, assetID, Close FROM public.History WHERE Timestamp='{o}' AND assetID='{id}'")
    #     data = self.send_query(sql_stmt1, helpers.ResponseType.ALL)
    #     dates = []
    #     pl = []
    #     pl.append(start)
    #     dates.append(date)
    #     for d in data:
    #         id = d['assetID']
    #         o = d['openDate']
    #         c = d['closeDate']
    #         q = d['quantity']
    #         sql_stmt = f"SELECT Close FROM History WHERE Timestamp='{o}' AND assetID='{id}'"
    #         o_price = self.send_query(sql_stmt, helpers.ResponseType.ONE)
    #         sql_stmt =f"SELECT Close FROM History WHERE Timestamp='{c}' AND assetID='{id}'"
    #         c_price = self.send_query(sql_stmt, helpers.ResponseType.ONE)
    #         dates.append(helpers.convert_timestamp_to_date_single(c))
    #         pl.append(((c_price['Close'] / o_price['Close'] - 1) * q) + q)
    #     pl = [sum(pl[:i]) for i in range(1,len(pl)+1)]
    #     return pd.DataFrame({'Time': dates, 'Balance': pl})


    def calc_profit(self, pair):
        start_balance = 10_000
        date = '2015-01-01'
        date_ts = helpers.convert_string_to_timestamp(date)
        now_ts = datetime.now().timestamp()
        data = []
        sql_stmt = "SELECT orderID FROM orders"
        orders = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        if len(orders) == 0:
            sql_stmt = f"SELECT DISTINCT Timestamp from history WHERE Timestamp >= {date_ts} and Timestamp <= {now_ts}"
            dates = self.send_query(sql_stmt, helpers.ResponseType.ALL)
            df = pd.DataFrame(dates)
            all_days = []
            if len(df) == 0:
                date_dt = helpers.convert_string_to_date(date)
                all_days.append(date_dt)
                while date_dt < datetime.now():
                    date_dt += timedelta(days=1)
                    all_days.append(date_dt)
                return pd.DataFrame({'Time': all_days, 'Balance': start_balance})

            # df = df.set_index(df['Timestamp'])
            # df['Balance'] = start_balance
            # df['Timestamp'] = df.index
            # df = df[['Timestamp', 'Balance']]
            # df['Time'] = df.apply(helpers.convert_timestamp_to_date, axis=1)
            # df = df[['Time', 'Balance']]
            # return df

        for order in orders:
            args = [order['orderID']]
            resp = self.send_procedure('order_daily_returns', args, helpers.ResponseType.ALL)
            df = pd.DataFrame(resp)
            quantity = df.iloc[0]['Quantity']
            rets = np.cumprod(1 + df['percChange'].values) - 1
            rets = rets * quantity
            rets_df = pd.DataFrame(rets, index=df['Timestamp'], columns=['Balance'])
            rets_df = rets_df.dropna()
            data.append(rets_df)
        sql_stmt = f"SELECT DISTINCT Timestamp from history WHERE Timestamp >= {date_ts} and Timestamp <= {now_ts}"
        dates = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        df = pd.DataFrame(dates)
        df = df.set_index(df['Timestamp'])
        df['Balance'] = 0
        df = df[['Balance']]
        for dd in data:
            df = df.add(dd, fill_value=0)
        df['Timestamp'] = df.index
        df = df[['Timestamp', 'Balance']]
        df['Time'] = df.apply(helpers.convert_timestamp_to_date, axis=1)
        df = df[['Time', 'Balance']]
        for i in range(len(df)):
            if i == 0:
                 df.iat[i,1] += start_balance
                 continue
            if df.iloc[i]['Balance'] == 0:
                start_balance = df.iloc[i-1]['Balance']

            df.iat[i,1] += start_balance
        return df

            

    def get_asset_pairs(self):
        resp = cw.markets.list(self.exchange)
        pairs = [x.pair.upper() for x in resp.markets]
        return pairs

    def get_asset_id(self, pair):
        resp = cw.markets.list(self.exchange)
        for market in resp.markets:
            if (market.pair).upper() == pair:
                return market.id

if __name__ == "__main__":
    db = Database()
    db.calc_profit('port')


