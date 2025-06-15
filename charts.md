```mermaid
erDiagram

    laptop_invoices ||--o{ laptop_items : contains
    laptop_items ||--o{ laptop_assignments : assigned_to
    users ||--o{ laptop_assignments : owns
    laptop_items ||--o{ maintenance_logs : has

    laptop_invoices {
        int id PK
        string invoice_number
        string order_date
        string invoice_date
        string order_number
        string supplier_name
    }

    laptop_items {
        int id PK
        int invoice_id FK
        string laptop_model
        string processor
        string ram
        string storage
        string model_color
        string screen_size
        string laptop_os
        string laptop_os_version
        string laptop_serial_number
        int warranty_duration
        float laptop_price
        string created_at
        string warranty_expiry
        boolean is_retired
        boolean is_active
        string drive_file_id
    }

    users {
        int id PK
        string name
        string email
        boolean is_active
    }

    laptop_assignments {
        int id PK
        int laptop_item_id FK
        int user_id FK
        string assigned_at
        string unassigned_at
    }

    maintenance_logs {
        int id PK
        int laptop_item_id FK
        string date
        string description
        string performed_by
    }

    drive_files {
        string id PK
        string name
        datetime last_edited
    }
```

```mermaid
graph TD

subgraph Client
    A[HTML + Bootstrap UI]
end

subgraph Backend
    B[App Server - Flask]
    B1[Pandas & PDF Extractor]
    B2[LLM Gemini API]
end

subgraph External Services
    C[Google Drive API]
    D[Gemini LLM API]
end

subgraph Database
    E[(SQLite DB)]
    E1[Laptop Invoices]
    E2[Laptop Items]
    E3[Users]
    E4[Laptop Assignments]
    E5[Maintenance Logs]
    E6[Drive Files]
end

%% Connections
A --> B
B --> B1
B --> B2
B1 --> E
B2 --> B1
B --> E
B --> C
B2 --> D

%% DB relationships
E --> E1
E --> E2
E --> E3
E --> E4
E --> E5
E --> E6
```