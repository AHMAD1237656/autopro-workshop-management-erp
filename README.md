# AutoPro ERP — Auto Spare Parts, Workshop & Showroom Suite

![Django](https://img.shields.io/badge/Django-6.x-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)

An enterprise-grade, modular Management ERP system engineered for Auto Spare Parts retailers, Mechanical Repair Workshops, and Vehicle Showrooms. Built with clean Django architecture, role-based access control (RBAC), and responsive interface components.

---

## 🚀 Key Modules & Capabilities

- **📦 Spare Parts & Inventory Management (`inventory`)**
  - OEM SKU lookup, vehicle compatibility tracking, shelf/bin locator.
  - Automatic low-stock threshold triggers and reorder warnings.

- **🛠️ Repair & Maintenance Job Cards (`workshop`)**
  - Full vehicle check-in lifecycle (inspection, status transitions, technician assignment).
  - Parts consumption tracking with real-time inventory deduction and labor billing.

- **🛒 Counter POS Terminal (`sales`)**
  - High-speed checkout terminal optimized for retail walk-ins.
  - Barcode search autofocus, dynamic cart calculation, and instant stock sync.

- **📑 Unified Invoicing Engine (`invoices`)**
  - Printable dual-format templates: 80mm compact thermal receipts and formal A4 tax invoices.

- **🚗 Showroom Vehicle Tracking (`showroom`)**
  - Inventory management for new and pre-owned cars/motorcycles.
  - Status management (Available, Booked, Sold), chassis/VIN verification, and pricing analytics.

- **📥 Supplier Purchases & Stock Receiving (`purchases`)**
  - Vendor replenishment orders with automated stock incrementation.

- **💳 General Ledger & Accounts (`ledger`)**
  - Double-entry party ledgers for customer receivables and vendor payables.
  - Real-time running balances and transaction statement generation.

- **💵 Payment Settlements (`payments`)**
  - Voucher recording (Cash, Cheque, Online/Bank) with direct ledger synchronization.

- **🔒 Role-Based Access Control (`roles` & `users_app`)**
  - Permissions matrix for Super Admins, Workshop Technicians, Cashiers, and Managers.

- **📊 Central Analytics & Executive Dashboard (`dashboard`)**
  - Live KPI metric cards for revenue, active jobs, and low stock warnings.

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Django (MVT Architecture)
- **Database:** SQLite (Development) / PostgreSQL-ready
- **Frontend:** HTML5, CSS3, Tailwind CSS / Custom Enterprise Theme, Vanilla JavaScript
- **Analytics:** Chart.js, Pandas, NumPy

---

## 📁 System Architecture & Directory Structure

```text
autopro_erp/
├── autopro_core/          # Core settings, routing, base layouts & context
├── users_app/             # User authentication & profile management
├── roles/                 # Role-based access control matrix (RBAC)
├── inventory/             # Spare parts catalogue & shelf tracking
├── workshop/              # Vehicle profiles & repair job cards
├── showroom/              # Vehicle sales & showroom inventory
├── sales/                 # Fast counter POS billing terminal
├── invoices/              # Dynamic invoice & receipt printing engine
├── purchases/             # Supplier orders & stock replenishment
├── ledger/                # Double-entry general ledger statements
├── payments/              # Payment collection & settlement vouchers
├── dashboard/             # Executive metrics & summary charts
├── static/                # CSS themes, icons, and modular JS scripts
└── templates/             # HTML templates and responsive partials
