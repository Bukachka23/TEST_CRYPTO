-- Database initialization script for microservices
-- This script creates the required databases for both services

-- Create database for User Verification Service
CREATE DATABASE user_verification_db;

-- Create database for Wallet Service  
CREATE DATABASE wallet_service_db;

-- Grant privileges to postgres user (already the owner)
GRANT ALL PRIVILEGES ON DATABASE user_verification_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE wallet_service_db TO postgres;

-- Display created databases
\l 