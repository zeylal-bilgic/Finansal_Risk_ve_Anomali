CREATE DATABASE IF NOT EXISTS financial_risk;
USE financial_risk;

CREATE TABLE IF NOT EXISTS transfer_transactions (
    transaction_id VARCHAR(16) PRIMARY KEY,
    transaction_time DATETIME NOT NULL,
    account_id VARCHAR(16) NOT NULL,
    beneficiary_id VARCHAR(16) NOT NULL,
    channel VARCHAR(10) NOT NULL,
    direction ENUM('incoming','outgoing') NOT NULL,
    amount_try DECIMAL(14,2) NOT NULL,
    status VARCHAR(16) NOT NULL,
    INDEX idx_time (transaction_time),
    INDEX idx_account_beneficiary_time (account_id, beneficiary_id, transaction_time)
);
