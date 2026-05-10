<div align="center">

# 🏢 Multi-Tenant SaaS Backend

**Production-grade REST API built with Django REST Framework**

[![Django](https://img.shields.io/badge/Django-6.0.4-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.17.1-red?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-45%20Passing-brightgreen?style=for-the-badge&logo=pytest)](.)
[![Live](https://img.shields.io/badge/Live-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://multi-tenant-saas-backend-x74a.onrender.com/api/docs/)

<br/>

[📖 Swagger Docs](https://multi-tenant-saas-backend-x74a.onrender.com/api/docs/) &nbsp;·&nbsp;
[📄 ReDoc](https://multi-tenant-saas-backend-x74a.onrender.com/api/redoc/) &nbsp;·&nbsp;
[🐛 Report Bug](https://github.com/sagarkumarr1/multi-tenant-saas-backend/issues)

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Architecture Diagram](#-architecture-diagram)
- [API Flow](#-api-flow)
- [API Endpoints](#-api-endpoints)
- [Database Schema](#-database-schema)
- [RBAC — Role-Based Access Control](#-rbac--role-based-access-control)
- [Tenant Isolation](#-tenant-isolation)
- [Security Features](#-security-features)
- [Environment Setup](#-environment-setup)
- [Deployment Guide](#-deployment-guide-render)
- [Running Tests](#-running-tests)
- [Project Structure](#-project-structure)
- [Tech Stack](#-tech-stack)

---

## 🎯 Overview

A **production-ready multi-tenant SaaS backend** where multiple organizations (tenants) share the same infrastructure but have **completely isolated data**. Built with security-first principles — every endpoint is authenticated, tenant-scoped, and role-protected.

### ✅ What's Implemented

| Feature | Details |
|---|---|
| 🏢 **Multi-Tenancy** | Complete data isolation — tenant A cannot see tenant B's data |
| 🔐 **JWT Auth** | Access + Refresh tokens with server-side blacklist logout |
| 🎭 **RBAC** | 3-tier roles — Admin, Manager, User with object-level permissions |
| 🗑️ **Soft Delete** | Users deactivated, never hard-deleted. Fully restorable |
| 📋 **Audit Logging** | Every sensitive action logged with actor, target & timestamp |
| 📊 **Dashboard API** | Live tenant stats broken down by role |
| 🔍 **Search & Filter** | Username search, role filter, sort, pagination |
| 📖 **Swagger Docs** | Auto-generated OpenAPI 3.0 via drf-spectacular |
| ✅ **45 Tests** | Login, permissions, tenant isolation, CRUD, bulk ops, logout |
| 🤖 **CI/CD** | GitHub Actions runs full test suite on every push |

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│          Postman  /  Android App  /  Web Browser                │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RENDER CLOUD (Live)                        │
│            https://multi-tenant-saas-backend-x74a.onrender.com  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DJANGO APPLICATION                        │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              MIDDLEWARE LAYER                           │   │
│  │   SecurityMiddleware → SessionMiddleware → CSRF         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           JWT AUTHENTICATION + RATE LIMITING            │   │
│  │   JWTAuthentication · LoginRateThrottle (3/min)         │   │
│  │   UserRateThrottle (10/min) · AnonRateThrottle (5/min)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           RBAC PERMISSION LAYER                         │   │
│  │   IsAdminOrManager  ·  IsOwnerOrAdmin                   │   │
│  │   Object-level checks · Tenant boundary enforcement     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           SERIALIZER VALIDATION LAYER                   │   │
│  │   LoginSerializer · RegisterSerializer (duplicate check)│   │
│  │   BulkUserActionSerializer · LogoutSerializer           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               VIEWS (Business Logic)                    │   │
│  │   LoginView · LogoutView · RegisterView · ProfileView   │   │
│  │   UserListView · UserDetailView · RestoreUserView       │   │
│  │   ChangeUserRoleView · BulkDeleteView · BulkRestoreView │   │
│  │   DashboardView                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                               │                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   POSTGRESQL DATABASE                           │
│                                                                 │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│   │   tenants    │   │    users     │   │  audit_logs  │      │
│   │   (Tenant)   │◄──│   (User)     │──►│  (AuditLog)  │      │
│   └──────────────┘   └──────────────┘   └──────────────┘      │
│                                                                 │
│   ┌──────────────────────────────────────┐                     │
│   │   token_blacklist (JWT Blacklist)    │                     │
│   └──────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 API Flow

### Login & Token Flow

```
Client                          API Server                    Database
  │                                  │                             │
  │──── POST /api/user/login/ ───────►│                             │
  │     { username, password }        │                             │
  │                                  │── authenticate(user) ───────►│
  │                                  │◄── User object ─────────────│
  │                                  │                             │
  │                                  │── Generate JWT tokens       │
  │◄─── 200 OK ──────────────────────│                             │
  │     { access, refresh }          │                             │
  │                                  │                             │
  │──── GET /api/user/profile/ ──────►│                             │
  │     Authorization: Bearer <access>│                             │
  │                                  │── Validate JWT ─────────────│
  │                                  │── Check tenant scope ───────►│
  │◄─── 200 OK ──────────────────────│                             │
  │     { username, role, tenant }   │                             │
  │                                  │                             │
  │──── POST /api/user/logout/ ──────►│                             │
  │     { refresh: "eyJ..." }        │── Blacklist refresh token ──►│
  │◄─── 200 OK ──────────────────────│                             │
  │     { message: "Logged out" }    │                             │
```

### RBAC Permission Check Flow

```
Incoming Request
       │
       ▼
┌─────────────────────────────┐
│  Is user authenticated?     │
│  (JWT token valid?)         │
└──────┬──────────────────────┘
       │ NO ──────────────────────────► 401 Unauthorized
       │ YES
       ▼
┌─────────────────────────────┐
│  Check View-level permission│
│  (IsAdminOrManager ?)       │
└──────┬──────────────────────┘
       │ NO ──────────────────────────► 403 Forbidden
       │ YES
       ▼
┌─────────────────────────────┐
│  Fetch object from DB       │
│  WITH tenant filter         │
│  (tenant=request.user.tenant)│
└──────┬──────────────────────┘
       │ NOT FOUND ───────────────────► 404 Not Found
       │ FOUND
       ▼
┌─────────────────────────────┐
│  Check Object-level perm    │
│  (IsOwnerOrAdmin ?)         │
└──────┬──────────────────────┘
       │ NO ──────────────────────────► 403 Forbidden
       │ YES
       ▼
  ✅ Access Granted → Execute Business Logic → Response
```

---

## 📡 API Endpoints

**Base URL:** `https://multi-tenant-saas-backend-x74a.onrender.com/api/`

| Method | Endpoint | Auth Required | Role | Description |
|:---:|---|:---:|:---:|---|
| `POST` | `/user/login/` | ❌ | Public | Get JWT access + refresh tokens |
| `POST` | `/user/logout/` | ✅ | Any | Blacklist refresh token (server-side logout) |
| `POST` | `/user/register/` | ✅ | Admin / Manager | Create a new user in your tenant |
| `GET` | `/user/profile/` | ✅ | Any | View your own profile and role |
| `GET` | `/user/` | ✅ | Admin / Manager | List users with search, filter, sort, paginate |
| `GET` | `/user/{id}/` | ✅ | Owner / Admin / Manager | Get single user detail |
| `PATCH` | `/user/{id}/` | ✅ | Owner / Admin / Manager | Update username |
| `DELETE` | `/user/{id}/` | ✅ | Admin / Manager | Soft delete user (restorable) |
| `POST` | `/user/{id}/restore/` | ✅ | Admin / Manager | Restore a soft-deleted user |
| `POST` | `/user/{id}/change-role/` | ✅ | Admin only | Change role (ADMIN / MANAGER / USER) |
| `POST` | `/user/bulk-delete/` | ✅ | Admin / Manager | Delete multiple users at once |
| `POST` | `/user/bulk-restore/` | ✅ | Admin / Manager | Restore multiple users at once |
| `GET` | `/dashboard/` | ✅ | Admin / Manager | Live tenant stats by role |
| `GET` | `/api/schema/` | ❌ | Public | OpenAPI 3.0 schema (JSON) |
| `GET` | `/api/docs/` | ❌ | Public | Swagger UI |
| `GET` | `/api/redoc/` | ❌ | Public | ReDoc UI |

### Query Parameters for `GET /api/user/`

```
?search=sagar          → Username search (case-insensitive)
?role=MANAGER          → Filter by role (ADMIN / MANAGER / USER)
?ordering=username     → Sort ascending by username
?ordering=-created_at  → Sort descending by created_at (default)
?page=2                → Page number (5 users per page)
```

### Request / Response Examples

<details>
<summary><b>POST /api/user/login/</b></summary>

**Request:**
```json
{
  "username": "sagar",
  "password": "yourpassword"
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 401:**
```json
{ "error": "Invalid credentials" }
```
</details>

<details>
<summary><b>POST /api/user/logout/</b></summary>

**Headers:** `Authorization: Bearer <access_token>`

**Request:**
```json
{ "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

**Response 200:**
```json
{ "message": "Logged out successfully. Token has been blacklisted." }
```
</details>

<details>
<summary><b>GET /api/user/</b></summary>

**Headers:** `Authorization: Bearer <access_token>`

**Response 200:**
```json
{
  "count": 12,
  "next": "http://localhost:8000/api/user/?page=2",
  "previous": null,
  "results": [
    {
      "id": 3,
      "username": "john_doe",
      "role": "USER",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```
</details>

<details>
<summary><b>POST /api/user/bulk-delete/</b></summary>

**Request:**
```json
{ "user_ids": [3, 7, 12] }
```

**Response 200:**
```json
{
  "deleted": ["john_doe", "jane_smith"],
  "skipped": [
    { "username": "yourself", "reason": "Cannot delete yourself" }
  ]
}
```
</details>

---

## 🗄️ Database Schema

```
┌────────────────────────────────────────────┐
│                  TENANT                    │
├────────────────────────────────────────────┤
│  id               INTEGER   PK AUTO        │
│  organization_name VARCHAR(50) NOT NULL    │
│  created_at       DATETIME  auto_now_add   │
└──────────────────────┬─────────────────────┘
                       │ FK (tenant_id)
                       │ CASCADE on delete
                       ▼
┌────────────────────────────────────────────┐
│                   USER                     │
├────────────────────────────────────────────┤
│  id               INTEGER   PK AUTO        │
│  username         VARCHAR   UNIQUE         │
│  password         VARCHAR   hashed         │
│  phone_number     VARCHAR(15) nullable     │
│  tenant_id        FK → Tenant nullable     │
│  role             VARCHAR(20)              │
│                   choices: ADMIN/MANAGER   │
│                            /USER           │
│                   default: USER            │
│  created_by_id    FK → self nullable       │ ◄─ Self-referential
│  is_active        BOOLEAN  default: True   │    (who created this user)
│  created_at       DATETIME auto_now_add    │
│  (+ Django AbstractUser fields)            │
└────────────────┬─────────────┬─────────────┘
                 │             │
    FK (performed_by)    FK (target_user)
                 │             │
                 ▼             ▼
┌────────────────────────────────────────────┐
│                 AUDIT LOG                  │
├────────────────────────────────────────────┤
│  id               INTEGER   PK AUTO        │
│  action           VARCHAR(100)             │
│                   e.g. DELETE_USER         │
│                        RESTORE_USER        │
│                        BULK_DELETE_USER    │
│                        CHANGE_ROLE_TO_X    │
│  performed_by_id  FK → User nullable       │
│  target_user_id   FK → User nullable       │
│  timestamp        DATETIME auto_now_add    │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│         TOKEN BLACKLIST (SimpleJWT)        │
├────────────────────────────────────────────┤
│  outstanding_token  — all issued tokens    │
│  blacklisted_token  — invalidated tokens   │
└────────────────────────────────────────────┘
```

### Key Database Design Decisions

| Decision | Reason |
|---|---|
| `is_active = False` for delete | Users are never hard-deleted — data integrity + restore capability |
| `created_by` self-FK on User | Managers can only manage users they created |
| `tenant` FK on User | Every query scoped with `tenant=request.user.tenant` |
| `db_index=True` on `created_by` | Fast lookup of manager's users |
| `max_length=20` on role | Future-proof — "MANAGER" is 7, gives room to grow |
| `max_length=100` on AuditLog.action | "CHANGE_ROLE_TO_MANAGER" = 22 chars, safe margin |

---

## 🎭 RBAC — Role-Based Access Control

The system implements **3-tier RBAC** with both view-level and object-level permissions.

### Role Hierarchy

```
                        ┌─────────────────┐
                        │      ADMIN      │
                        │  (God Mode 👑)  │
                        └────────┬────────┘
                                 │ can create
                    ┌────────────┴────────────┐
                    │                         │
             ┌──────▼──────┐          ┌───────▼──────┐
             │   MANAGER   │          │    MANAGER   │
             │  (Team Lead)│          │  (Team Lead) │
             └──────┬──────┘          └──────────────┘
                    │ can create
          ┌─────────┴──────────┐
     ┌────▼────┐          ┌────▼────┐
     │  USER   │          │  USER   │
     └─────────┘          └─────────┘
```

### Permission Matrix

| Action | Admin | Manager | User |
|---|:---:|:---:|:---:|
| Login / Logout | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| Update own username | ✅ | ✅ | ✅ |
| View user list | ✅ All users | ✅ Own users only | ❌ |
| Create new user | ✅ | ✅ | ❌ |
| View user detail | ✅ Any | ✅ Own users | ✅ Self only |
| Soft delete user | ✅ Any | ✅ Own users | ❌ |
| Restore user | ✅ Any | ✅ Own users | ❌ |
| Change user role | ✅ | ❌ | ❌ |
| Bulk delete | ✅ Any | ✅ Own users | ❌ |
| Bulk restore | ✅ Any | ✅ Own users | ❌ |
| View dashboard | ✅ | ✅ | ❌ |
| Delete self | ❌ | ❌ | ❌ |

### Permission Classes

```python
# View-level — who can access this endpoint at all
class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in [User.ADMIN, User.MANAGER]

# Object-level — who can act on a specific user object
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == User.ADMIN:
            return True                                    # Admin → full access
        if obj == request.user:
            return True                                    # Self → own profile
        if request.user.role == User.MANAGER:
            return obj.created_by == request.user         # Manager → own users
        return False
```

---

## 🏢 Tenant Isolation

**The core security guarantee:** No user from Tenant A can ever read, modify, or delete data belonging to Tenant B — regardless of their role.

### How It Works

Every database query that touches user data is automatically scoped to the requesting user's tenant:

```python
# ❌ WRONG — No tenant isolation (vulnerable)
users = User.objects.filter(id__in=user_ids)

# ✅ CORRECT — Tenant-scoped (safe)
users = User.objects.filter(id__in=user_ids, tenant=request.user.tenant)
```

### Isolation Enforcement Points

| Endpoint | Isolation Method |
|---|---|
| `GET /user/` | `filter(tenant=request.user.tenant)` on queryset |
| `GET /user/{id}/` | `get_object_or_404(User, id=id, tenant=...)` |
| `DELETE /user/{id}/` | Object permission + `IsOwnerOrAdmin` |
| `POST /user/{id}/restore/` | `get_object_or_404(..., tenant=request.user.tenant)` |
| `POST /user/{id}/change-role/` | `get_object_or_404(..., tenant=request.user.tenant)` |
| `POST /user/bulk-delete/` | `filter(id__in=ids, tenant=request.user.tenant)` |
| `POST /user/bulk-restore/` | `filter(id__in=ids, tenant=request.user.tenant)` |

### Cross-Tenant Attack — What Happens

```
Tenant A Admin (id=1, tenant="CompanyA") attempts to delete
User id=99 who belongs to "CompanyB"

Request: DELETE /api/user/99/

Server executes:
  get_object_or_404(User, id=99, tenant=CompanyA)
                                 └── CompanyA ≠ CompanyB

Result: 404 Not Found
User 99 is safe. Attack blocked. ✅
```

### Visual Isolation Model

```
┌─────────────────────────────┐    ┌─────────────────────────────┐
│         COMPANY A           │    │         COMPANY B           │
│  ┌──────────────────────┐  │    │  ┌──────────────────────┐  │
│  │  Admin (role=ADMIN)  │  │    │  │  Admin (role=ADMIN)  │  │
│  │  Manager A1          │  │    │  │  Manager B1          │  │
│  │  User A1, A2, A3     │  │    │  │  User B1, B2         │  │
│  └──────────────────────┘  │    │  └──────────────────────┘  │
│                             │    │                             │
│  tenant_id = 1              │    │  tenant_id = 2              │
└─────────────────────────────┘    └─────────────────────────────┘
           ↑                                    ↑
           │         ❌ WALL ❌                 │
           └────────────────────────────────────┘
           Admin of Company A CANNOT access Company B data
```

---

## 🔒 Security Features

| Feature | Implementation |
|---|---|
| **Secret Key Protection** | Loaded from `.env` via `python-decouple`, never in source code |
| **JWT Token Blacklist** | Logout invalidates refresh token server-side — tokens can't be reused |
| **Login Brute Force** | `LoginRateThrottle` — max 3 login attempts per minute per IP |
| **Global Rate Limiting** | 10 req/min authenticated, 5 req/min anonymous |
| **RBAC + Object Permissions** | Two-layer permission checks on every request |
| **Tenant Isolation** | DB-level enforcement — not just UI filtering |
| **Soft Delete** | Users never hard-deleted — data integrity maintained |
| **Input Validation** | Serializer validation prevents duplicate usernames (400, not 500) |
| **Self-Delete Prevention** | Admins cannot delete themselves — prevents lockout |
| **Audit Logging** | All destructive actions logged with full context |

---

## ⚙️ Environment Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Git

### Step 1 — Clone & Virtual Environment

```bash
git clone https://github.com/sagarkumarr1/multi-tenant-saas-backend.git
cd multi-tenant-saas-backend

# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate        # Linux / Mac
venv\Scripts\activate           # Windows
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values
nano .env
```

Your `.env` file should look like:

```env
# Django
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=saas_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

> 💡 **Generate a strong SECRET_KEY:**
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(50))"
> ```

### Step 4 — Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE saas_db;"

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (Django admin)
python manage.py createsuperuser
```

### Step 5 — Run Development Server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000/admin/`

### Step 6 — Initial Data Setup (Admin Panel)

1. Go to `http://127.0.0.1:8000/admin/`
2. Login with your superuser credentials
3. **Create a Tenant:** Tenants → Add Tenant → e.g. "TechCorp"
4. **Assign tenant to superuser:** Users → your user → set `tenant = TechCorp`, `role = ADMIN`
5. Now you can use Postman or Swagger to test all APIs

---

## 🚀 Deployment Guide (Render)

### Step 1 — Push to GitHub

```bash
git add .
git commit -m "feat: production deployment"
git push origin main
```

### Step 2 — Create Web Service on Render

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---|---|
| **Name** | `multi-tenant-saas-backend` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn config.wsgi` |

### Step 3 — Environment Variables on Render

In the Render dashboard → **Environment** tab, add:

```
SECRET_KEY        → your-production-secret-key
DEBUG             → False
ALLOWED_HOSTS     → your-app.onrender.com
DB_NAME           → your_db_name
DB_USER           → your_db_user
DB_PASSWORD       → your_db_password
DB_HOST           → your-db-host.render.com
DB_PORT           → 5432
```

### Step 4 — Create PostgreSQL Database on Render

1. Render Dashboard → **New → PostgreSQL**
2. Copy the **Internal Database URL**
3. Parse it into the env variables above

### Step 5 — Run Migrations on Render

In Render → your service → **Shell** tab:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### Step 6 — Verify Deployment

```bash
curl https://your-app.onrender.com/api/docs/
# Should return Swagger UI HTML
```

> ⚠️ **Note:** Free tier on Render spins down after 15 min of inactivity. First request may take 30-60 seconds.

---

## 🧪 Running Tests

### Install test dependencies

```bash
pip install pytest pytest-django
```

### Run all 45 tests

```bash
pytest users/tests.py -v
```

### Run specific test class

```bash
pytest users/tests.py::TenantIsolationTests -v
pytest users/tests.py::LogoutTests -v
```

### Test Coverage Summary

| Test Class | Tests | What's Covered |
|---|:---:|---|
| `LoginTests` | 8 | Valid login, wrong credentials, token access, profile fields |
| `TenantIsolationTests` | 7 | Cross-tenant role change, bulk ops, restore — all blocked |
| `PermissionTests` | 12 | Admin/Manager/User role limits on every endpoint |
| `UserCRUDTests` | 13 | Soft delete, restore, patch validation, bulk operations |
| `LogoutTests` | 5 | Token blacklist, reuse prevention, missing fields |
| **Total** | **45** | **Full coverage of all critical paths** |

### CI — GitHub Actions

Tests run automatically on every `git push`:

```yaml
# .github/workflows/ci.yml
on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main, master]
```

View results in the **Actions** tab of your GitHub repository.

---

## 📁 Project Structure

```
multi-tenant-saas-backend/
│
├── config/                    ← Django project config
│   ├── settings.py            ← All settings (DB, JWT, DRF, Swagger)
│   ├── settings_test.py       ← Test settings (SQLite, no throttle)
│   ├── urls.py                ← Root URL conf + Swagger routes
│   ├── wsgi.py
│   └── asgi.py
│
├── core/                      ← AuditLog model
│   ├── models.py              ← AuditLog (action, performed_by, target, timestamp)
│   ├── admin.py
│   └── migrations/
│
├── tenants/                   ← Tenant / Organization model
│   ├── models.py              ← Tenant (organization_name, created_at)
│   ├── admin.py
│   └── migrations/
│
├── users/                     ← Main app
│   ├── models.py              ← Custom User (AbstractUser + tenant + role + created_by)
│   ├── serializers.py         ← Login, Register, Logout, BulkAction serializers
│   ├── permissions.py         ← IsAdminOrManager, IsOwnerOrAdmin
│   ├── throttles.py           ← LoginRateThrottle (3/min)
│   ├── views.py               ← All 11 view classes
│   ├── urls.py                ← All 11 URL patterns (all named)
│   ├── tests.py               ← 45 tests across 5 test classes
│   ├── admin.py
│   └── migrations/
│
├── .github/
│   └── workflows/
│       └── ci.yml             ← GitHub Actions CI
│
├── .env                       ← Local secrets (gitignored)
├── .env.example               ← Template for env variables
├── .gitignore
├── conftest.py                ← pytest configuration
├── pytest.ini                 ← Points to settings_test.py
├── requirements.txt           ← All dependencies pinned
├── Procfile                   ← Render/Heroku: gunicorn config.wsgi
└── manage.py
```

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **Django** | 6.0.4 | Web framework |
| **Django REST Framework** | 3.17.1 | REST API layer |
| **SimpleJWT** | 5.5.1 | JWT authentication + token blacklist |
| **drf-spectacular** | 0.28.0 | OpenAPI 3.0 / Swagger auto-docs |
| **PostgreSQL** | 16 | Production database |
| **psycopg2-binary** | 2.9.10 | PostgreSQL adapter for Python |
| **python-decouple** | 3.8 | Environment variable management |
| **gunicorn** | 25.3.0 | Production WSGI server |
| **pytest-django** | latest | Testing framework |
| **GitHub Actions** | — | CI/CD pipeline |
| **Render** | — | Cloud deployment |

---

## 📞 Contact

**Sagar Kumar**

[![GitHub](https://img.shields.io/badge/GitHub-sagarkumarr1-181717?style=flat-square&logo=github)](https://github.com/sagarkumarr1)

---

<div align="center">

**⭐ If this project helped you, please give it a star!**

[🔝 Back to Top](#-multi-tenant-saas-backend)

</div>
