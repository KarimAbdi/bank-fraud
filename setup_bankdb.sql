USE BankDB;
GO

-- Drop foreign key constraints first (if re-running setup)
IF OBJECT_ID('FraudAlerts', 'U') IS NOT NULL DROP TABLE FraudAlerts;
IF OBJECT_ID('Transactions', 'U') IS NOT NULL DROP TABLE Transactions;
IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;
GO

-- Create Customers table
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    FullName NVARCHAR(100),
    Email NVARCHAR(100),
    Country NVARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE()
);
GO

-- Create Transactions table
CREATE TABLE Transactions (
    TransactionID INT PRIMARY KEY IDENTITY(1001,1),
    CustomerID INT,
    Amount DECIMAL(10, 2),
    TransactionDate DATETIME,
    TransactionType NVARCHAR(50),
    Location NVARCHAR(100),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);
GO

-- Create FraudAlerts table
CREATE TABLE FraudAlerts (
    AlertID INT PRIMARY KEY IDENTITY(1,1),
    TransactionID INT,
    CustomerID INT,
    Reason NVARCHAR(255),
    DetectedAt DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (TransactionID) REFERENCES Transactions(TransactionID),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);
GO

-- Insert sample customers
INSERT INTO Customers (CustomerID, FullName, Email, Country) VALUES
(1, 'Alice Smith', 'alice@example.com', 'USA'),
(2, 'Bob Johnson', 'bob@example.com', 'USA');
GO

-- Insert sample transactions
INSERT INTO Transactions (CustomerID, Amount, TransactionDate, TransactionType, Location) VALUES
(1, 100.00, GETDATE() - 1, 'debit', 'New York'),
(1, 9500.00, GETDATE(), 'debit', 'Nigeria'), --suspecious
(2, 50.00, GETDATE() - 2, 'debit', 'California'),
(2, 49.00, GETDATE(), 'debit', 'California'),
(2, 5000.00, GETDATE(), 'debit', 'Russia'); --suspicious
GO
