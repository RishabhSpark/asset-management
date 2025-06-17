# Asset Management System

A Flask-based asset management system with Google Drive integration for managing laptops, users, and invoices. The system supports uploading and extracting invoice data from Google Drive PDFs, deduplication of laptop records, warranty expiry tracking, and both manual and Drive-based laptop entries.

## Features

- **Google Drive Integration:**
  - Browse and select invoice PDFs from a Google Drive folder tree.
  - Upload and extract invoice data directly from Drive.
- **Asset Management:**
  - Add, edit, and assign laptops to users.
  - Manual and Drive-based laptop entry support.
  - Deduplication logic ensures no duplicate laptop records (using serial and Drive file ID).
  - Stable laptop IDs even after repeated uploads.
- **Warranty Tracking:**
  - Tracks warranty start and expiry dates for each laptop.
  - Displays warnings for expired or soon-to-expire warranties in the UI.
- **User Management:**
  - Add, edit, and view users.
  - Assign laptops to users and track assignment history.
- **Database:**
  - Uses SQLite (`invoices_database.db`) for all records.
  - Schema includes warranty dates and Drive file IDs for robust deduplication.

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/yourusername/asset-management.git
cd asset-management
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Google Drive API Setup
- Place your `client_secret.json` in the project root.
- The first time you use Drive features, you will be prompted to authenticate and authorize access.

### 4. Database Initialization
- The database is created automatically at `invoices_database.db` in the project root.

```sql
ALTER TABLE laptop_items ADD COLUMN warranty_start_date TEXT;
ALTER TABLE laptop_items ADD COLUMN drive_file_id TEXT;
```

### 5. Run the Application
```sh
python app/main.py
```
- The app will be available at `http://localhost:8000` by default.

## Usage Guide

- **Upload Invoice:** Use the "Upload Invoice" button on any main page to browse Google Drive and select a PDF invoice.
- **Warranty Warnings:** Laptops with expired or soon-to-expire warranties are highlighted with a red badge.
- **Manual Entry:** Add laptops and users manually if needed.
- **Deduplication:** The system prevents duplicate laptop records by checking both serial number and Drive file ID.

## File Structure

- `app/` - Flask app and templates
- `db/` - Database models, CRUD logic, and migrations
- `extractor/` - Invoice and PDF extraction logic
- `output/` - Exported data (CSV, JSON, Excel)
- `invoices/` - Example invoice PDFs

## Troubleshooting

- **Google Drive Auth Issues:** Delete any `token.json` or cached credentials and re-authenticate.
- **Database Errors:** Ensure the schema matches the latest code. Run migration SQL if needed.
- **Session Conflicts:** All session variables are now properly scoped to avoid Flask conflicts.
