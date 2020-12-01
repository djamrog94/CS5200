CREATE DATABASE IF NOT EXISTS paperTrader;
USE papertrader;

CREATE TABLE Assets
(assetID INT PRIMARY KEY, name VARCHAR(255) NOT NULL);

CREATE TABLE IF NOT EXISTS History (
Timestamp INT, 
assetID INT, 
open REAL NOT NULL, 
high REAL NOT NULL, 
low REAL NOT NULL, 
close REAL NOT NULL, 
FOREIGN KEY (assetID) REFERENCES Assets(assetID) 
ON DELETE CASCADE ON UPDATE CASCADE, 
PRIMARY KEY (assetID, Timestamp));

CREATE TABLE Users (
username VARCHAR(255) PRIMARY KEY,
password VARCHAR(255) NOT NULL,
firstName VARCHAR(255) NOT NULL, 
lastName VARCHAR(255) NOT NULL);

CREATE TABLE Portfolio (
accountID INT AUTO_INCREMENT PRIMARY KEY,
openDate VARCHAR(255) NOT NULL, 
startingBalance VARCHAR(255) NOT NULL,
username VARCHAR(255),

FOREIGN KEY (username) REFERENCES Users(username) 
ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE Orders ( 
orderID INT AUTO_INCREMENT PRIMARY KEY, 
username VARCHAR(255), 
assetID INT, 
openDate INT NOT NULL, 
closeDate INT NOT NULL, 
quantity REAL NOT NULL, 
FOREIGN KEY (assetID) REFERENCES Assets(assetID) 
ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (username) REFERENCES Users(username) 
ON DELETE CASCADE ON UPDATE CASCADE);

CREATE TABLE user_asset_detail (
username VARCHAR(255), 
assetID INT, 

FOREIGN KEY (assetID) REFERENCES Assets(assetID)
ON DELETE CASCADE ON UPDATE CASCADE,

FOREIGN KEY (username) REFERENCES Users(username)
ON DELETE CASCADE ON UPDATE CASCADE,

PRIMARY KEY(username, assetID)
);

DROP PROCEDURE IF EXISTS order_daily_returns;
DELIMITER $$
CREATE PROCEDURE order_daily_returns
( 
IN oid INT
)
BEGIN

SELECT Timestamp, (Close / Open - 1) AS percChange, (SELECT quantity FROM orders WHERE orderID=oid) as Quantity
FROM history WHERE Timestamp >= (SELECT openDate FROM orders WHERE orderID=oid)
AND Timestamp <= (SELECT closeDate FROM orders WHERE orderID=oid)
AND assetID=(SELECT assetID FROM orders WHERE orderID=oid);

END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS order_details;
DELIMITER $$
CREATE PROCEDURE order_details
( 
IN user VARCHAR(255)
)
BEGIN
SELECT orderID as "Order ID", name as "Asset Name", DATE_ADD(FROM_UNIXTIME(openDate, "%Y/%m/%d"), INTERVAL 1 DAY) as "Open Date", DATE_ADD(FROM_UNIXTIME(closeDate, "%Y/%m/%d"), INTERVAL 1 DAY) as "Close Date", FORMAT(quantity, 'C') as Quantity, FORMAT(((b.close / a.close) - 1) * Quantity, 'C') as "Gain / Loss"
 FROM Orders JOIN Assets on Orders.assetID=Assets.assetID
LEFT JOIN history as a ON orders.assetID=a.assetID AND orders.openDate=a.Timestamp
LEFT JOIN history as b ON orders.assetID=b.assetID AND orders.closeDate=b.Timestamp
WHERE orders.username=user
ORDER BY orderID;
END$$
DELIMITER ;

DROP PROCEDURE IF EXISTS remove_asset;
DELIMITER $$
CREATE PROCEDURE remove_asset
( 
IN user VARCHAR(255),
IN id INT
)
BEGIN
DELETE FROM user_asset_detail Where assetID=id and username=user;

IF (SELECT COUNT(*) FROM user_asset_detail where assetID=id) = 0 THEN DELETE FROM assets where assetId=id;
END IF;

END$$
DELIMITER ;

INSERT INTO users VALUES ('test', 'test', 'dave', 'jam');
INSERT INTO portfolio (openDate, startingBalance, username) VALUES (1420070400, 15000, 'test');



