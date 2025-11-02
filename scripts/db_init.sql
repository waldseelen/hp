-- =============================================================================
-- Database Initialization Script for Development
-- =============================================================================
-- This script creates necessary database objects for development environment

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE portfolio_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'portfolio_dev');

-- Create test database for running tests
SELECT 'CREATE DATABASE test_portfolio_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'test_portfolio_dev');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE portfolio_dev TO postgres;
GRANT ALL PRIVILEGES ON DATABASE test_portfolio_dev TO postgres;
