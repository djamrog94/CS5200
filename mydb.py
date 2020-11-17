import pymysql.cursors
import helpers
import cryptowatch as cw

class Database():
    def __init__(self) -> None:
        self.name = 'paperTrader'
        self.columns = ['assetID', 'Timestamp', 'Open', 'High', 'Low', 'Close']
        self.exchange = 'KRAKEN'
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
                        user='user',
                        password='passwd',
                        db=self.name,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)
            
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
                create_asset_table_stmt = "CREATE TABLE IF NOT EXISTS ASSETS \
                     (assetID INT PRIMARY KEY,name VARCHAR(255) NOT NULL)"
                create_history_table_stmt = "CREATE TABLE IF NOT EXISTS History ( \
                            Timestamp VARCHAR(255), \
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
                            openDate VARCHAR(255) NOT NULL, \
                            closeDate VARCHAR(255) NOT NULL, \
                            FOREIGN KEY (assetID) REFERENCES Assets(assetID) \
                            ON DELETE SET NULL ON UPDATE CASCADE);"
                crate_user_table_stmt = "CREATE TABLE Users ( \
                            userID INT AUTO_INCREMENT PRIMARY KEY, \
                            firstName VARCHAR(255) NOT NULL, \
                            lastName VARCHAR(255) NOT NULL);"
                create_accounts_table_stmt = "CREATE TABLE Accounts ( \
                            accountID INT AUTO_INCREMENT PRIMARY KEY, \
                            userID INT, \
                            openDate VARCHAR(255) NOT NULL, \
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
                cursor.execute(query)
            connection.commit()
        finally:
            connection.close()

    def read_query(self, query, response):
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
                    return
                return result
        finally:
            connection.close()

    def create_asset(self, id, pair):
        insert_st = f"INSERT INTO public.Assets VALUES ({id}, '{pair.upper()}')"
        self.send_query(insert_st, helpers.ResponseType.NONE)

    def get_history(self, pair):
        pass

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


