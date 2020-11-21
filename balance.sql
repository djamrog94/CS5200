USE papertrader;
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





