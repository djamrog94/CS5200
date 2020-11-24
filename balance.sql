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

CREATE TABLE Asset_Info ( 
assetName VARCHAR(255) PRIMARY KEY, 
assetID INT, 
altName VARCHAR(255) NOT NULL, 
assetClass VARCHAR(255) NOT NULL, 
FOREIGN KEY (assetID) REFERENCES Assets(assetID)
ON DELETE SET NULL ON UPDATE CASCADE); 

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

USE papertrader;
DROP PROCEDURE IF EXISTS order_details;
DELIMITER $$
CREATE PROCEDURE order_details
( 

)
BEGIN
SELECT orderID as "Order ID", name as "Asset Name", FROM_UNIXTIME(openDate, "%m/%d/%Y") as "Open Date", FROM_UNIXTIME(closeDate, "%m/%d/%Y") as "Close Date", quantity as Quantity, FORMAT(b.close - a.close, 'C') as "Profit / Loss"
 FROM Orders JOIN Assets on Orders.assetID=Assets.assetID
LEFT JOIN history as a ON orders.assetID=a.assetID AND orders.openDate=a.Timestamp
LEFT JOIN history as b ON orders.assetID=b.assetID AND orders.closeDate=b.Timestamp
ORDER BY orderID;
END$$
DELIMITER ;





