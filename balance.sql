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


-- SELECT Timestamp from history WHERE Timestamp >= 1385424000 and Timestamp <= 1386892800 


