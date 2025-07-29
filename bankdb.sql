-- Create and switch to the BankDB
CREATE DATABASE BankDB;
GO
USE BankDB;
GO

-- Customers Table
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    FullName NVARCHAR(100),
    Email NVARCHAR(100),
    Country NVARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE()
);

-- Sample Customers
INSERT INTO Customers (CustomerID, FullName, Email, Country)
VALUES 
(1, 'Alice Johnson', 'alice@example.com', 'USA'),
(2, 'Bob Smith', 'bob@example.com', 'USA'),
(3, 'John Mwangi', 'john@example.com', 'Kenya');

-- Payees Table
CREATE TABLE Payees (
    PayeeID INT PRIMARY KEY,
    Name NVARCHAR(100)
);

-- Sample Payees
INSERT INTO Payees (PayeeID, Name) VALUES
(1, 'SuperMart'),
(2, '0713888999'),
(3, 'FuelStation'),
(4, 'ATM-Thika'),
(5, '0722111222');

-- Transactions Table
CREATE TABLE Transactions (
    TransactionID INT PRIMARY KEY IDENTITY(1001,1),
    CustomerID INT,
    PayeeID INT,
    Amount DECIMAL(12,2),
    TransactionType NVARCHAR(50),
    Location NVARCHAR(100),
    Latitude FLOAT,
    Longitude FLOAT,
    TransactionDate DATETIME,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (PayeeID) REFERENCES Payees(PayeeID)
);

-- Sample Transactions
INSERT INTO Transactions (CustomerID, PayeeID, Amount, TransactionType, Location, Latitude, Longitude, TransactionDate)
VALUES
(1, 4, 11363.66, 'ATM', 'Thika', -1.047, 37.070, '2025-07-05 19:49:52'),
(2, 1, 146000.41, 'POS', 'Kisumu', -0.091, 34.767, '2025-07-06 12:45:37'),
(2, 1, 76149.22, 'POS', 'Mombasa', -4.043, 39.668, '2025-07-06 22:36:45'),
(3, 3, 121872.25, 'POS', 'Thika', -1.047, 37.070, '2025-07-08 11:08:23'),
(1, 5, 71309.25, 'MobileMoney', 'Nakuru', -0.303, 36.080, '2025-07-01 04:11:20');

-- Transfers Table (MobileMoney)
CREATE TABLE Transfers (
    TransferID INT PRIMARY KEY IDENTITY(1,1),
    SenderID INT,
    RecipientID INT,
    Amount DECIMAL(12,2),
    TransferDate DATETIME,
    FOREIGN KEY (SenderID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (RecipientID) REFERENCES Customers(CustomerID)
);

-- Sample Transfers
INSERT INTO Transfers (SenderID, RecipientID, Amount, TransferDate)
VALUES
(1, 2, 99000.00, '2025-07-06 10:00:00'),
(1, 2, 98000.00, '2025-07-06 10:45:00'),
(1, 2, 105000.00, '2025-07-06 11:15:00');

-- POS Transactions Table
CREATE TABLE POS_Transactions (
    POSID INT PRIMARY KEY IDENTITY(1,1),
    CustomerID INT,
    Amount DECIMAL(12,2),
    MCC INT,
    TransactionDate DATETIME,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);

-- Sample POS Transactions
INSERT INTO POS_Transactions (CustomerID, Amount, MCC, TransactionDate)
VALUES
(1, 1000.00, 7995, '2025-07-06 08:00:00'),
(1, 1500.00, 7995, '2025-07-06 08:30:00'),
(1, 2000.00, 7995, '2025-07-06 09:00:00'),
(1, 1700.00, 7995, '2025-07-06 09:30:00'),
(1, 1200.00, 7995, '2025-07-06 10:00:00');

-- Fraud Alerts Table
CREATE TABLE FraudAlerts (
    AlertID INT PRIMARY KEY IDENTITY(1,1),
    TransactionID INT NULL,
    CustomerID INT,
    Reason NVARCHAR(255),
    DetectedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);
