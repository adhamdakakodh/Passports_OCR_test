

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'PassportData')
BEGIN
    CREATE TABLE dbo.PassportData (
        id INT IDENTITY(1,1) PRIMARY KEY,
        first_name NVARCHAR(200) NULL,
        last_name NVARCHAR(200) NULL,
        date_of_birth NVARCHAR(50) NULL,
        nationality NVARCHAR(100) NULL,
        passport_number NVARCHAR(50) NULL,
        place_of_birth NVARCHAR(200) NULL,
        passport_issue_date NVARCHAR(50) NULL,
        issuing_authority NVARCHAR(200) NULL,
        expiry_date NVARCHAR(50) NULL,
        sex NVARCHAR(10) NULL,
        mrz_line1 NVARCHAR(50) NULL,
        mrz_line2 NVARCHAR(50) NULL,
        mrz_valid BIT NULL,
        mrz_consistent_with_visual BIT NULL,
        created_at DATETIME2 DEFAULT GETUTCDATE()
    );
END
