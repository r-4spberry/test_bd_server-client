-- Create a user for replication
CREATE USER 'replica'@'%' IDENTIFIED WITH mysql_native_password BY 'replicapassword';
GRANT REPLICATION SLAVE ON *.* TO 'replica'@'%';
FLUSH PRIVILEGES;

-- Ensure binary logging is enabled
RESET MASTER;
