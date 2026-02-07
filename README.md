# Sales Distribution System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Django](https://img.shields.io/badge/Django-4.2-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

A comprehensive, **Myanmar-language ready Sales Distribution System** built with Django 4.2. Designed for FMCG (Fast-Moving Consumer Goods) distributors to manage the entire lifecycle from lead generation to final delivery and accounting.

> **Open Source & Vibe Coding Initiative**
>
> This project is open source and was developed using the **"Vibe Coding"** methodology, powered by next-generation AI coding assistants:
> - **Cursor**
> - **Trae**
> - **Open Code**
> - **Antigravity**
>
> We embrace the future of AI-driven software development to build faster, smarter, and more efficient solutions.

**GitHub Repository:** [https://github.com/attthurein/django-sales-distribution](https://github.com/attthurein/django-sales-distribution)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [System Deep Dive](#system-deep-dive)
- [Installation & Setup](#installation--setup)
- [User Roles & Permissions](#user-roles--permissions)
- [Management Commands](#management-commands)
- [Localization & Translation](#localization--translation)
- [Production Deployment](#production-deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This system is a monolithic Django application optimized for reliability and traceability. It supports:
- **Bilingual UI**: Seamless switching between English and Myanmar (Unicode) interfaces.
- **Role-Based Access**: Pre-configured roles for Salespeople, Managers, and Accountants.
- **Data Integrity**: Soft-delete mechanisms and full audit trails for critical data.
- **Performance**: Optimized database queries (N+1 prevention), caching, and asynchronous task readiness.

---

## Key Features

### 📊 Dashboard & Reporting
- **Real-time Analytics**: 7-day trends for Revenue, Payments, and Expenses.
- **Smart Alerts**: Low stock warnings, Expiry alerts (highlighting batches expiring in <30 days).
- **PDF Generation**: Invoices and Payment Vouchers with customizable company branding.

### 🛒 Sales & Orders
- **Flexible Order Types**:
  - **Normal**: Immediate stock deduction.
  - **Pre-order**: Stock deducted upon delivery.
  - **Replacement**: Zero-price orders for handling exchanges/returns.
- **Smart Pricing**:
  - **Tiered Pricing**: Different price lists for Wholesalers, Retailers, etc.
  - **Auto-Promotions**: Automatically applies the best active discount.
  - **Location-based Delivery**: Auto-calculates fees based on Customer Township.

### 📦 Inventory Management
- **Batch Tracking**: First-In-First-Out (FIFO) expiry logic.
- **Stock Movements**: Immutable history of every stock change (IN, OUT, ADJUST, RETURN).
- **Reconciliation**: Built-in tools to verify and fix stock discrepancies.

### 🤝 CRM
- **Lead Pipeline**: Track leads from `New` → `Contacted` → `Converted`.
- **Activity Logs**: Record visits, calls, and sample deliveries.

### ↩️ Returns Management
- **Strict Policies**: Single return request per order to prevent duplication.
- **Waste vs Restock**: Explicit handling for damaged goods (Waste) vs reusable items (Restock).

---

## Architecture & Tech Stack

### Technology Stack
- **Backend**: Python 3.10+, Django 4.2.7
- **Database**: SQLite (Dev) / PostgreSQL (Production ready)
- **Frontend**: Bootstrap 5, Crispy Forms, Django Templates
- **Server**: Gunicorn, Whitenoise (Static files)
- **Utilities**:
  - `django-environ`: Configuration management
  - `reportlab`: PDF generation
  - `openpyxl`: Excel exports

### Module Diagram

```mermaid
graph TD
    User((User)) --> Dashboard
    User --> Orders
    
    subgraph Core
        Product --> Batch
        Batch --> StockMovement
    end
    
    subgraph Sales
        Customer --> SalesOrder
        SalesOrder --> OrderItem
        SalesOrder --> Payment
    end
    
    subgraph Logistics
        ReturnRequest --> ReturnItem
        ReturnRequest --> ReplacementOrder
    end
    
    Orders --> Product
    ReturnRequest --> SalesOrder
    Payment --> Accounting
```

---

## System Deep Dive

### Inventory Logic
The system uses a **Batch-based Inventory System**:
- **Batches**: Every product belongs to a batch with a specific expiry date.
- **Stock Movements**: Stock is never just "updated". Every change is recorded as a `StockMovement` (IN, OUT, ADJUST, RETURN).
- **Source of Truth**: The `Product.stock_quantity` is a cached value. The absolute truth is the sum of all `StockMovement` records. Use the `reconcile_stock` command to sync them if they drift.

### Order Management
- **Voucher Generation**: Payment Vouchers generate unique IDs (`PV-YYYYMMDD-XXXX`) using atomic database transactions to ensure uniqueness even under high load.
- **Soft Deletion**: Orders cannot be hard-deleted. They use `SoftDeleteMixin` to mark as deleted, preserving historical references for stock and audit purposes.

### Security & Audit
- **SoftDeleteMixin**: Most models (Product, Order, Payment, Customer) inherit from this. `Model.objects.all()` returns only active records. Use `Model.all_objects.all()` to see deleted ones.
- **AuditMiddleware**: A custom middleware captures the actor (User) for every request. Signals automatically create `AuditLog` entries for creations, updates, and deletions.

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/attthurein/django-sales-distribution.git
   cd django-sales-distribution
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Copy `.env.example` to `.env` and adjust settings if needed (defaults work for dev).
   ```bash
   cp .env.example .env
   ```

5. **Initialize Database**
   ```bash
   python manage.py migrate
   ```

6. **Create Default Roles, Master Data & Superuser**
   ```bash
   python manage.py setup_groups
   python manage.py setup_master_data
   python manage.py createsuperuser
   ```

7. **Run the Server**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000`

---

## User Roles & Permissions

Run `python manage.py setup_groups` to initialize these roles:

| Role | Permissions |
|------|-------------|
| **Salesperson** | Create Orders, View Products, Manage Customers, CRM activities. |
| **Manager** | Full access to all modules including Reports, Master Data, and User Audits. |
| **Accountant** | View Orders, Manage Payments, Manage Expenses, View Financial Reports. |

---

## Management Commands

The system includes custom CLI commands for maintenance:

- **Reconcile Stock**: Recalculates product stock based on movement history.
  ```bash
  python manage.py reconcile_stock --fix
  ```
- **Setup Groups**: Resets/Updates default user roles and permissions.
  ```bash
  python manage.py setup_groups
  ```
- **Setup Master Data**: Seeds initial master data (Regions, Townships, Company Info, Payment Methods).
  ```bash
  python manage.py setup_master_data
  ```
- **Daily Backup**: Creates a JSON dump of the database (configured in `common/management/commands`).
  ```bash
  python manage.py backup_db
  ```

---

## Localization & Translation

The system is bilingual (English/Myanmar). When you modify translation files (`.po`), you must compile them into binary files (`.mo`) for the changes to take effect.

### Updating Translations

**Option 1: Using Helper Scripts (Recommended)**

- **Windows**:
  Double-click `scripts/update_translations.bat` or run in terminal:
  ```powershell
  .\scripts\update_translations.bat
  ```

- **Linux/Mac**:
  Run the shell script:
  ```bash
  ./scripts/update_translations.sh
  ```

**Option 2: Manual Command**

Ensure your virtual environment is active, then run:
```bash
python manage.py compilemessages
```

*Note: If you add new translatable strings to the code, run `python manage.py makemessages -l my` first to generate the `.po` entries.*

---

## Production Deployment

To deploy this system to a production environment (e.g., Ubuntu VPS, DigitalOcean, AWS), follow these additional steps:

### 1. Environment Configuration
Create a `.env` file for production (see `.env.prod.example`):
```ini
DEBUG=False
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@localhost:5432/sales_db
DJANGO_SETTINGS_MODULE=sales_distribution.settings.production
```

### 2. Database (PostgreSQL)
Production requires a robust database.
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create DB and User
sudo -u postgres psql
postgres=# CREATE DATABASE sales_db;
postgres=# CREATE USER sales_user WITH PASSWORD 'secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE sales_db TO sales_user;
postgres=# \q
```

### 3. Static & Media Files
- **Static Files**: Run `python manage.py collectstatic` to gather all assets into `staticfiles/`.
- **Media Files**: Ensure the `media/` directory is writable by the web server user.

### 4. Gunicorn (App Server)
Install Gunicorn (already in requirements) and create a systemd service:
`/etc/systemd/system/gunicorn.service`:
```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/Sale
ExecStart=/path/to/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --bind unix:/run/gunicorn.sock \
          sales_distribution.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 5. Nginx (Web Server)
Configure Nginx as a reverse proxy:
`/etc/nginx/sites-available/sales`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Serve Static Files (WhiteNoise handles this, but Nginx is faster)
    location /static/ {
        root /path/to/Sale/staticfiles;
    }

    # Serve Media Files (User Uploads)
    location /media/ {
        root /path/to/Sale;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

---

## Project Structure

- `core/`: Inventory (Products, Batches, StockMovements).
- `orders/`: SalesOrders, OrderItems, Payments.
- `customers/`: Customer profiles and segmentation.
- `returns/`: Return requests and processing logic.
- `crm/`: Leads, Contact Logs, Samples.
- `master_data/`: System configuration (Company info, Payment methods).
- `common/`: Shared utilities, Audit logic, SoftDelete mixins.
- `reports/`: Reporting views and PDF generation.
- `sales_distribution/`: Project settings and main URL routing.

---

## Contributing

Contributions are welcome! If you'd like to improve this project, please follow these steps:

1.  **Fork** the repository.
2.  Create a new branch for your feature or fix.
3.  Commit your changes.
4.  Submit a **Pull Request (PR)** back to this repository.

*Note: This project is maintained on a voluntary basis. Issues will be addressed as time permits. If you find a bug but can't fix it, feel free to open an Issue.*

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
