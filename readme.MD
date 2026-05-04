# 🚀 Multi-Tenant SaaS Backend (Django + DRF)

A production-ready backend system built using Django REST Framework implementing real-world SaaS architecture with authentication, role-based access control, tenant isolation, and advanced permission handling.

---

## 📌 Overview

This project simulates a real SaaS platform where:

* Each company (tenant) has isolated data
* Admins and Managers control user access
* Users have restricted permissions based on role and ownership
* System enforces secure, scalable, and production-ready practices

---

## ⚙️ Tech Stack

* Python 3.12
* Django
* Django REST Framework
* Simple JWT (Authentication)
* SQLite (Development)

---

## 🔐 Core Features

### ✅ Authentication

* JWT-based login system
* Access + Refresh token implementation
* Secure login endpoint with rate limiting

---

### 🏢 Multi-Tenant Architecture

* Each user belongs to a tenant
* Data isolation per tenant
* No cross-tenant data leakage

---

### 👥 Role-Based Access Control (RBAC)

| Role    | Permissions          |
| ------- | -------------------- |
| Admin   | Full control         |
| Manager | Manage created users |
| User    | Self access only     |

---

### 🔍 Object-Level Permissions

* Access control based on:

  * Role
  * Ownership (`created_by`)
* Ensures secure data handling at object level

---

### ♻️ Soft Delete & Restore

* Users are not permanently deleted
* `is_active = False` for safe deactivation
* Restore API available

---

### 📦 Bulk Operations

* Bulk delete users
* Bulk restore users
* Efficient admin actions

---

### 📊 Dashboard API

Provides real-time insights:

* Total users
* Active / inactive users
* Role distribution

---

### 📄 Pagination, Search & Sorting

* Pagination support
* Search users by username
* Filter by role
* Sort by:

  * username
  * role
  * created_at

---

### 🧾 Audit Logging

Tracks system actions:

* User deletion
* Role changes
* Restore operations

---

### 🚦 Rate Limiting (Security)

* Prevents brute-force login
* Limits API abuse
* Custom throttle for login endpoint

---

## 📷 Screenshots

### 🔐 Login API (JWT Tokens)

👉 Add screenshot: Postman showing access + refresh token

---

### 👥 User List (Role-Based)

👉 Add screenshot:

* Admin → sees all users
* Manager → sees limited users

---

### ❌ Permission Denied (403)

👉 Add screenshot:

* Manager trying unauthorized action

---

### ♻️ Soft Delete & Restore

👉 Add screenshot:

* Delete → user disappears
* Restore → user reappears

---

### 📊 Dashboard API

👉 Add screenshot:

* Total users
* Active users
* Role breakdown

---

### 🔥 Bulk Actions

👉 Add screenshot:

* Multiple user delete request

---

### 🚦 Rate Limiting

👉 Add screenshot:

* 429 Too Many Requests

---

## 🧪 API Endpoints (Sample)

```http
POST   /api/login/
POST   /api/user/register/
GET    /api/users/
PATCH  /api/users/<id>/
DELETE /api/users/<id>/
POST   /api/users/<id>/restore/
POST   /api/users/bulk-delete/
POST   /api/users/bulk-restore/
GET    /api/dashboard/
POST   /api/users/<id>/change-role/
```

---

## 🚀 How to Run Locally

```bash
git clone https://github.com/your-username/saas-backend.git
cd saas-backend

python -m venv venv
venv\Scripts\activate   # Windows

pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

## 📈 Learning Outcomes

* Built a real-world SaaS backend architecture
* Implemented RBAC + object-level permissions
* Designed secure multi-tenant system
* Applied production-level backend patterns

---

## 🧠 Future Improvements

* Redis caching
* Celery for async tasks
* Swagger API documentation
* Deployment (AWS / Render)

---

## 🤝 Connect

If you're interested in backend engineering or SaaS systems, feel free to connect.

---

⭐ If you found this useful, consider giving a star!
