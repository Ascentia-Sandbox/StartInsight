-- Database setup script for StartInsight
-- Run this as the PostgreSQL superuser (postgres)
-- Usage: sudo -u postgres psql -f setup_database.sql

-- Create the startinsight database
CREATE DATABASE startinsight;

-- Create the startinsight user with password
CREATE USER startinsight WITH PASSWORD 'startinsight_dev_password';

-- Grant all privileges on the database to the user
GRANT ALL PRIVILEGES ON DATABASE startinsight TO startinsight;

-- Connect to the startinsight database
\c startinsight

-- Grant schema privileges (needed for SQLAlchemy)
GRANT ALL ON SCHEMA public TO startinsight;

-- Show confirmation
SELECT 'Database setup complete!' AS status;
