# LuxeCommerce &mdash; Enterprise-Grade Django E-Commerce Platform

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-green.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791.svg)](https://www.postgresql.org/)
[![REST Framework](https://img.shields.io/badge/Django_REST-Framework-red.svg)](https://www.django-rest-framework.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modern, production-ready, full-stack eCommerce application built with **Django 5**, **Django REST Framework**, and **PostgreSQL**. Designed with high craft adhering to the **Neo-Luxe Commerce** design system, featuring real-time cart persistence, multi-step checkout, visual order tracking, sandbox payment simulation, comprehensive catalog administration, and complete RESTful API coverage.

---

## 🌟 Key Features

### 🛍️ Customer Experience & Storefront
- **Neo-Luxe Modern UI**: Dark obsidian glassmorphic header, Google Fonts (*Outfit* & *Plus Jakarta Sans*), micro-interactions, responsive product grid.
- **Product Catalog & Discovery**: Instant category filtering, real-time keyword search, sorting (price low-high, high-low, rating, newest), inventory badges (*In Stock*, *Only X left*, *Sold Out*).
- **Product Details & Customer Reviews**: High-resolution image showcase, interactive 5-star rating selector, verified review feed, related product recommendations.
- **Persistent Shopping Bag**: Seamless synchronization between client-side storage and server-side Django session, live quantity adjustments, and dynamic free shipping progress bar.
- **Multi-Step Checkout**: Encrypted shipping details capture, payment method selection (Simulated Instant Test Card & PayPal), and order breakdown.
- **Visual Order Tracking**: 4-stage tracking stepper (**Order Placed** &rarr; **Payment Confirmed** &rarr; **Dispatch & Transit** &rarr; **Delivered**), invoice receipt, and 1-click test payment sandbox.

### 🛡️ Administrative Console
- **Product Catalog Management**: Web interface for store administrators to create products, upload images, update pricing/specifications, and remove discontinued items.
- **Customer Order Management**: Filter orders by status (*Paid*, *Unpaid*, *Needs Delivery*, *Delivered*), inspect buyer shipping details, and update dispatch/delivery milestones.
- **User Directory**: View registered accounts, toggle administrator privileges, and manage user permissions.

### ⚡ Technical Highlights
- **PostgreSQL Native**: Configured for PostgreSQL (`ecommerce_db`) with support for ports `5432` and `5050` (pgAdmin / Docker mapped).
- **RESTful API + Template Hybrid**: Dual-purpose views serving both modern HTML frontend pages and JSON API endpoints.
- **JWT & Session Auth**: SimpleJWT integration alongside standard Django session authentication.
- **Automated Test Suite**: 14 automated tests covering products, search, cart, checkout, reviews, auth, and order lifecycles.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Django 5.1.7, Python 3.12 |
| **API Framework** | Django REST Framework (DRF), SimpleJWT |
| **Database** | PostgreSQL (`psycopg2-binary`) |
| **Frontend & Styling** | HTML5, Vanilla CSS Design System, Bootstrap 5.3, FontAwesome 6 |
| **Typography** | Google Fonts (*Outfit*, *Plus Jakarta Sans*) |
| **Configuration** | `python-dotenv` environment variables |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **PostgreSQL 14+** (running locally or in Docker)
- **Git**

### 2. Clone the Repository
```bash
git clone https://github.com/mikhailemad999/ecommerce.git
cd ecommerce
```

### 3. Create & Activate Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is not yet present, install: `pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary python-dotenv pillow`)*

### 5. Configure Environment Variables (`.env`)
Create a `.env` file in the project root:
```ini
# Django Settings
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# PostgreSQL Database Configuration
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432
# If your PostgreSQL instance or pgAdmin container is mapped to port 5050:
# DB_PORT=5050
```

### 6. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Seed Sample Products & Admin Account
Populate the database with sample products and the default superuser:
```bash
python manage.py populate_db
```

### 8. Run the Development Server
```bash
python manage.py runserver 8000
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🔑 Default Credentials

| Role | Email / Username | Password | Access |
|---|---|---|---|
| **Administrator** | `admin@example.com` | `admin123` | Full Store & Catalog Management |
| **Demo Customer** | Any newly registered account | User defined | Browsing, Purchasing, Invoices |

---

## 🧪 Running Automated Tests

Execute the comprehensive test suite verifying catalog, search, cart, checkout, reviews, and authentication:
```bash
python manage.py test
```

Expected output:
```text
Creating test database for alias 'default'...
Found 14 test(s).
System check identified no issues (0 silenced).
..............
----------------------------------------------------------------------
Ran 14 tests in 19.375s

OK
Destroying test database for alias 'default'...
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/api/products/` | List all products (supports `?keyword=`, `?page=`) | Public |
| `GET` | `/api/products/<id>/` | Get detailed product specifications | Public |
| `POST` | `/api/products/<id>/reviews/` | Submit a review (rating 1-5 & comment) | Authenticated |
| `POST` | `/api/products/cart/save/` | Sync client cart items into server session | Public |
| `POST` | `/api/products/create/` | Create a new product | Admin |
| `PUT` | `/api/products/update/<id>/` | Update an existing product | Admin |
| `DELETE` | `/api/products/delete/<id>/` | Delete a product | Admin |
| `POST` | `/api/orders/add/` | Create and place a new order | Authenticated |
| `GET` | `/api/orders/myorders/` | List current user's orders | Authenticated |
| `GET` | `/api/orders/<id>/` | Fetch order details by ID | Authenticated (Owner / Admin) |
| `PUT` | `/api/orders/<id>/pay/` | Update order payment status to paid | Authenticated |
| `PUT` | `/api/orders/<id>/deliver/` | Update delivery status to delivered | Admin |
| `POST` | `/api/users/login/` | Obtain JWT token pair (access + refresh) | Public |
| `POST` | `/api/users/register/` | Register new customer account | Public |
| `GET` | `/api/users/profile/` | Fetch current user account profile | Authenticated |

---

## 📁 Project Directory Structure

```text
ecommerce/
├── base/                       # Core utilities and template tags
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── custom_filters.py   # Safe multiply, subtract, currency filters
│   └── management/commands/
│       └── populate_db.py      # Seed data generator
├── ecommerce/                  # Root project configuration
│   ├── settings.py             # Dotenv, dynamic DB, JWT, static settings
│   ├── urls.py                 # Core routing (API + Frontend)
│   ├── wsgi.py
│   └── asgi.py
├── media/                      # User-uploaded media and product assets
├── orders/                     # Order lifecycle, checkout & shipping
│   ├── models.py               # Order, OrderItem, ShippingAddress
│   ├── views.py                # Order processing, sandbox payment, delivery
│   ├── serializers.py          # DRF serializers
│   └── tests.py                # Order and checkout test suite
├── products/                   # Product catalog, stock & reviews
│   ├── models.py               # Product, Review
│   ├── views.py                # Catalog, search, filters, admin CRUD
│   ├── serializers.py          # Product serializers with safe image resolution
│   └── tests.py                # Product and review test suite
├── static/
│   ├── css/
│   │   └── styles.css          # Neo-Luxe Modern design system
│   ├── images/                 # High-resolution product image assets
│   └── js/
│       └── main.js             # Cart synchronization and toast alerts
├── templates/                  # Modern responsive HTML5 templates
│   ├── base.html               # Main layout, sticky header, search & footer
│   ├── products/               # Catalog, detail, cart, admin product management
│   ├── orders/                 # Checkout, order details, order management
│   └── users/                  # Sign in, register, profile, user management
├── users/                      # Authentication, profile & permissions
├── .env                        # Local PostgreSQL and secret key configuration
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules for Python/Django
├── manage.py
└── README.md                   # Comprehensive project documentation
```

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
