-- Table for Global Passport OCR pipeline (process-passport endpoint).
-- Run in your Azure SQL / SQL Server database.

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'passport_ocr_results')
BEGIN
    CREATE TABLE dbo.passport_ocr_results (
        id INT IDENTITY(1,1) PRIMARY KEY,
        request_id NVARCHAR(100) NULL,
        passport_number NVARCHAR(50) NULL,
        surname NVARCHAR(200) NULL,
        given_names NVARCHAR(200) NULL,
        nationality NVARCHAR(10) NULL,
        country_name NVARCHAR(200) NULL,
        date_of_birth NVARCHAR(50) NULL,
        expiry_date NVARCHAR(50) NULL,
        sex NVARCHAR(10) NULL,
        national_id NVARCHAR(14) NULL,
        mrz_line_1 NVARCHAR(50) NULL,
        mrz_line_2 NVARCHAR(50) NULL,
        mrz_valid BIT NULL,
        name_match BIT NULL,
        passport_number_match BIT NULL,
        dob_match BIT NULL,
        expiry_match BIT NULL,
        confidence_score INT NULL,
        validation_errors NVARCHAR(MAX) NULL,
        raw_visual_fields_json NVARCHAR(MAX) NULL,
        raw_mrz_fields_json NVARCHAR(MAX) NULL,
        image_url NVARCHAR(500) NULL,
        processing_time INT NULL,
        document_model_version NVARCHAR(50) NULL,
        created_at DATETIME2 DEFAULT GETUTCDATE()
    );
END

-- If the table already exists, add the national_id column.
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID('dbo.passport_ocr_results') AND name = 'national_id'
)
BEGIN
    ALTER TABLE dbo.passport_ocr_results ADD national_id NVARCHAR(14) NULL;
END
