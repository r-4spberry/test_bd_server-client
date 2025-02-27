-- Wait for the master to be ready
DO SLEEP(10);

-- Configure the replica to connect to the master
CHANGE MASTER TO
    MASTER_HOST='mysql-master',
    MASTER_USER='replica',
    MASTER_PASSWORD='replicapassword',
    MASTER_AUTO_POSITION=1;

START SLAVE;
