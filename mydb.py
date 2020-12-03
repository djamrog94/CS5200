import pymysql.cursors
import helpers
import cryptowatch as cw
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
            print('Cannot find database. Make sure MySQL is running, and that "sys" db exists!')

    def create_connection(self):
        return pymysql.connect(host='localhost',
                        user='root',
                        password='password',
                        db=self.name,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)

    def create_engine(self):
        db_data = f'mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}?charset=utf8mb4'
        engine = create_engine(db_data)
        return engine
            
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

    def login(self, username, password):
        sql_stmt = f"SELECT * FROM users where username='{username}'"
        resp = self.send_query(sql_stmt, helpers.ResponseType.ONE)
        if resp == None:
            return False
        if resp['password'] == password:
            return True

    def create_account(self, username, password, fName, lName, date, start):
        ans = ''
        try:
            ts = helpers.convert_string_to_timestamp(date)
        except:
            ans = 'Date is of wrong format!'

        try:
            float(start)
            if float(start) <= 0:
                ans = 'Starting balance must be greater than 0'
        except:
            ans = 'Starting balance must be a number greater than 0'
        if ans == '':
            try:
                sql_stmt = f"INSERT INTO users VALUES ('{username}', '{password}', '{fName}', '{lName}')"
                self.send_query(sql_stmt, helpers.ResponseType.NONE)
                sql_stmt = f"INSERT INTO portfolio (openDate, startingBalance, username) VALUES ({ts}, {start}, '{username}')"
                self.send_query(sql_stmt, helpers.ResponseType.NONE)
            except:
                ans = 'Username is already taken!'

        if ans == '':
            return [True, 'Succesfully created account!']
        return [False, ans]

    def create_asset(self, id, pair):
        insert_st = f"INSERT INTO assets VALUES ({id}, '{pair.upper()}')"
        self.send_query(insert_st, helpers.ResponseType.NONE)

    def remove_asset(self, user, pair):
        try:
            id = self.get_asset_id(pair)
            args = [user, id]
            self.send_procedure('remove_asset', args, helpers.ResponseType.NONE)
            return f'Successfully removed {pair} from database!'
        except:
            return f'Failed to remove {pair} from database!'

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

    def error_order(self, open, close, amount):
        try:
            open = helpers.convert_string_to_timestamp(open)
        except:
            return 'Format of open date is incorrect!'
        try:
            close = helpers.convert_string_to_timestamp(close)
        except:
            return 'Format of close date is incorrect!'
        if open > close:
            return 'Cannot have open date after close date!'
        try:
            float(amount)
        except:
            return 'Quantity must be a number!'
        if float(amount) <= 0:
            return 'Quantity must be a number greater than 0!'

        return None

    def create_order(self, pair, open, close, amount, user):
        ans = self.error_order(open, close, amount)
        if ans is not None:
            return ans
        open = helpers.convert_string_to_timestamp(open)
        close = helpers.convert_string_to_timestamp(close)
        sql = f"SELECT startingBalance, openDate FROM portfolio WHERE username='{user}'"
        person = self.send_query(sql, helpers.ResponseType.ONE)
        openDate = person['openDate']
        if open < float(openDate):
            return 'Cannot have open date for trade be before account was opened!'
        
        id = self.get_asset_id(pair)

        sql = f"SELECT Timestamp FROM history WHERE assetID='{id}' ORDER BY Timestamp Limit 1"
        firstDate = self.send_query(sql, helpers.ResponseType.ONE)
        firstDate = int(firstDate['Timestamp'])
        if open < firstDate:
            return 'Cannot have open date for trade be before asset existed!'
        curr_balance = self.calc_profit(open, user)
        if curr_balance.iloc[-1]['Balance'] < float(amount):
            return 'Quantity of Trade cannot be greater than current balance!'

        sql_stmt = f"INSERT INTO Orders (assetID, openDate, closeDate, Quantity, username) VALUES ({id},{open}, {close}, {float(amount)}, '{user}')"
        self.send_query(sql_stmt, helpers.ResponseType.NONE)
        return f'Order placed to buy ${amount} of {pair} completed!'

    def remove_order(self, orderIDs):
        for order in orderIDs:
            sql_stmt = f"DELETE FROM orders WHERE orderID='{order}'"
            self.send_query(sql_stmt, helpers.ResponseType.NONE)

    def update_order(self, id, open, close, quantity):
        ans = self.error_order(open, close, quantity)
        if ans is not None:
            return [False, ans]
        # try to update
        try:
            open = helpers.convert_string_to_timestamp(open)
            close = helpers.convert_string_to_timestamp(close)
            quantity = float(quantity)
            self.send_procedure('update_order', [id, open, close, quantity], helpers.ResponseType.NONE)
            return [True, 'Successfully updated order']
        except:
            return [False, 'Failed to update order']

    def get_order_details(self, user):
        resp = self.send_procedure('order_details', [user], helpers.ResponseType.ALL)
        df = pd.DataFrame(resp)
        if len(df) == 0:
            df = pd.DataFrame(None, columns=['ID', 'Asset', 'Open', 'Close', 'Quantity', 'P/L'])

        return df

    def add_hist_user(self, user, pair):
        id = self.get_asset_id(pair)
        sql_stmt = f"INSERT INTO user_asset_detail VALUES ('{user}', '{id}')"
        self.send_query(sql_stmt, helpers.ResponseType.NONE)

    def get_orders(self, pair):
        id = self.get_asset_id(pair)
        sql_stmt = f"SELECT openDate, closeDate FROM Orders WHERE assetID='{id}'"
        data = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        if len(data) == 0:
            return None, None
        open = [[],[]]
        close = [[],[]]
        for trade in data:
            # sql_stmt = f"SELECT Close FROM history WHERE Timestamp='{trade['openDate']}' AND assetID='{id}'"
            # o_price = self.send_query(sql_stmt, helpers.ResponseType.ONE)
            o_price = self.send_procedure('order_history', [trade['openDate'], id])
            open[0].append(trade['openDate'])
            open[1].append(o_price['Close'])
            # sql_smt = f"SELECT Close FROM history WHERE Timestamp='{trade['closeDate']}' AND assetID='{id}'"
            # c_price = self.send_query(sql_smt, helpers.ResponseType.ONE)
            c_price = self.send_procedure('order_history', [trade['closeDate'], id])
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

    def calc_profit(self, time, user):
        if time == 'port':
            now_ts = datetime.now().timestamp()
        else:
            now_ts = time
        if user != '':
            sql = f"SELECT startingBalance, openDate FROM portfolio WHERE username='{user}'"
            person = self.send_query(sql, helpers.ResponseType.ONE)
            start_balance = person['startingBalance']
            date = person['openDate']
        else:
            return pd.DataFrame([0])
        data = []
        sql_stmt = f"SELECT orderID FROM orders WHERE username = '{user}'"
        orders = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        if len(orders) == 0:
            # sql_stmt = f"SELECT DISTINCT Timestamp from history WHERE Timestamp >= {date} and Timestamp <= {now_ts}"
            # dates = self.send_query(sql_stmt, helpers.ResponseType.ALL)
            dates = self.send_procedure('get_dates', [date, now_ts])
            df = pd.DataFrame(dates)
            all_days = []
            if len(df) == 0:
                date_dt = helpers.convert_timestamp_to_date_single(int(date))
                all_days.append(date_dt)
                while date_dt < datetime.now():
                    date_dt += timedelta(days=1)
                    all_days.append(date_dt)
                return pd.DataFrame({'Time': all_days, 'Balance': start_balance})

        for order in orders:
            args = [order['orderID']]
            resp = self.send_procedure('order_daily_returns', args, helpers.ResponseType.ALL)
            df = pd.DataFrame(resp)
            df = df.dropna()
            quantity = df.iloc[0]['Quantity']
            rets = np.cumprod(1 + df['percChange'].values) - 1
            rets = rets * quantity
            rets_df = pd.DataFrame(rets, index=df['Timestamp'], columns=['Balance'])
            rets_df = rets_df.dropna()
            data.append(rets_df)
        # sql_stmt = f"SELECT DISTINCT Timestamp from history WHERE Timestamp >= {date} and Timestamp <= {now_ts}"
        # dates = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        dates = self.send_procedure('get_dates', [date, now_ts])
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
        start_balance = float(start_balance)
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

    def get_asset_name(self, id):
        sql_stmt = f"SELECT name FROM assets where assetID='{id}'"
        resp = self.send_query(sql_stmt, helpers.ResponseType.ONE)
        return resp['name']

    def get_order_ids(self, user):
        if user == '':
            return ''
        sql_stmt = f"SELECT orderID FROM orders where username='{user}' ORDER BY orderID"
        resp = self.send_query(sql_stmt, helpers.ResponseType.ALL)
        return [{'label': x['orderID'], 'value': x['orderID']} for x in resp]        

