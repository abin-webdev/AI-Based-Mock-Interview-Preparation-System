# AI-Based Mock Interview Preparation System
## Production Deployment & Operational Manual

This guide documents the end-to-end production deployment process for the **AI-Based Mock Interview Preparation System**, featuring a Python/Django REST Framework backend deployed on **Render** (with managed PostgreSQL), and the Flutter mobile/web client deployed on **Vercel** or **Firebase Hosting**.

---

### Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Backend Deployment on Render](#2-backend-deployment-on-render)
3. [Environment Variables Reference](#3-environment-variables-reference)
4. [Database & Static Assets (PostgreSQL + WhiteNoise)](#4-database--static-assets)
5. [Flutter Web Deployment (Vercel & Firebase)](#5-flutter-web-deployment)
6. [API & Swagger Documentation](#6-api--swagger-documentation)
7. [Health Checks & System Monitoring](#7-health-checks--system-monitoring)
8. [Automated Testing & Quality Gates](#8-automated-testing--quality-gates)

---

### 1. Architecture Overview

```mermaid
flowchart TD
    subgraph Clients["Frontend Clients"]
        MobileApp["Flutter Mobile App (Android/iOS)"]
        WebApp["Flutter Web SPA (Vercel / Firebase)"]
    end

    subgraph Render["Render Cloud Platform"]
        WSGI["Gunicorn WSGI (3 Workers)"]
        DjangoApp["Django REST Framework API"]
        WhiteNoise["WhiteNoise CDN Static Files"]
        Postgres[("Managed PostgreSQL Database")]
    end

    subgraph AI["AI Providers"]
        Gemini["Google Gemini API (gemini-1.5-flash)"]
        OpenCV["OpenCV Camera Telemetry Processor"]
    end

    MobileApp -->|HTTP/REST & Multipart| WSGI
    WebApp -->|CORS HTTPS| WSGI
    WSGI --> DjangoApp
    DjangoApp --> WhiteNoise
    DjangoApp --> Postgres
    DjangoApp --> Gemini
    DjangoApp --> OpenCV
```

---

### 2. Backend Deployment on Render

The backend includes a pre-configured Render Blueprint (`render.yaml`) and Gunicorn `Procfile`.

#### Option A: One-Click Render Blueprint (Recommended)
1. Push this repository to GitHub: `https://github.com/aleenasaji004-droid/AI-Based-Mock-Interview-Preparation-System`.
2. Log into the [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically detect `render.yaml` and provision:
   - A managed **PostgreSQL Database** (`mock-interview-db`).
   - A **Python Web Service** (`ai-mock-interview-backend`) running `gunicorn mock_interview_backend.wsgi:application`.
6. Add your Google Gemini API key under **Environment Variables** (`GEMINI_API_KEY`).
7. Click **Apply**. Render will automatically run `./build.sh` (collectstatic and migrate) and start the service.

#### Option B: Manual Web Service Setup on Render
1. Click **New +** -> **Web Service**.
2. Connect your repository and select the **Root Directory** as `backend`.
3. Configure the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh` (or `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`)
   - **Start Command**: `gunicorn mock_interview_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
   - **Health Check Path**: `/api/health/`
4. Add a managed PostgreSQL instance and set `DATABASE_URL` in the Web Service environment settings.

---

### 3. Environment Variables Reference

| Variable Name | Required | Default Value | Description |
|---|:---:|---|---|
| `SECRET_KEY` | **Yes** | Generated | Django cryptographic signing key. Keep secret in production. |
| `DEBUG` | **Yes** | `False` | Must be `False` in production to enforce security headers. |
| `DATABASE_URL` | **Yes** | `sqlite:///db.sqlite3` | PostgreSQL connection string (`postgres://user:pass@host:5432/dbname`). |
| `ALLOWED_HOSTS` | **Yes** | `.onrender.com,localhost,127.0.0.1` | Comma-separated allowed hostnames. |
| `CORS_ALLOW_ALL_ORIGINS` | No | `True` | Set to `False` in high-security production. |
| `CORS_ALLOWED_ORIGINS` | No | `https://your-flutter-web.vercel.app` | Whitelisted frontend origins when allow-all is false. |
| `GEMINI_API_KEY` | Recommended | None | Google Gemini API key for dynamic interview question generation. |
| `ENABLE_CAMERA_ANALYSIS`| No | `True` | Enables OpenCV posture and facial alignment telemetry. |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | No | `60` | JWT access token lifespan in minutes. |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | No | `7` | JWT refresh token lifespan in days. |
| `DJANGO_SUPERUSER_EMAIL` | Optional (One-time) | None | Email for initial production superuser creation. |
| `DJANGO_SUPERUSER_USERNAME` | Optional (One-time) | None | Username for initial production superuser. |
| `DJANGO_SUPERUSER_PASSWORD` | Optional (One-time) | None | Password for initial production superuser. |

---

### 4. Creating the Production Superuser (No Shell Required)

On Render's Free Plan, the web terminal shell is unavailable. You can safely create or update the initial Django superuser without a shell using our automated `create_initial_admin` command:

1. In the **Render Dashboard**, open your web service (`ai-mock-interview-backend`).
2. Navigate to the **Environment** tab.
3. Add the following environment variables:
   - `DJANGO_SUPERUSER_EMAIL`: e.g. `admin@mockinterview.org`
   - `DJANGO_SUPERUSER_USERNAME`: e.g. `admin`
   - `DJANGO_SUPERUSER_PASSWORD`: `YourSecurePassword123!`
4. Click **Save Changes** and click **Manual Deploy** > **Deploy latest commit**.
5. During the build phase, `build.sh` automatically runs `python manage.py create_initial_admin`:
   - It securely hashes the password via Django's PBKDF2 algorithm.
   - It assigns `role='ADMIN'`, `is_staff=True`, and `is_superuser=True`.
   - Passwords are never logged or exposed.
   - The command is completely **idempotent** (safe to run on every deploy; will not duplicate users).
6. *(Optional)* After first login at `https://<your-app>.onrender.com/admin/`, you can delete `DJANGO_SUPERUSER_PASSWORD` from Render's Environment tab if desired.

---

### 4. Database & Static Assets

#### Database Migrations
Migrations are applied automatically during the Render build phase via `build.sh`:
```bash
python manage.py migrate
```

To run migrations manually via the Render Shell:
```bash
python manage.py migrate
```

To create an administrative superuser on Render:
```bash
python manage.py createsuperuser
```

#### Static Files & WhiteNoise
WhiteNoise is pre-configured with compression and caching:
```bash
python manage.py collectstatic --no-input
```
All static files (Django admin styling, Swagger UI bundles) are served directly by Gunicorn with `max-age=31536000` cache headers without needing Nginx.

---

### 5. Flutter Web Deployment

The Flutter web frontend can be deployed to **Vercel** or **Firebase Hosting**.

#### Step 1: Build Flutter Web Bundle
Run the build command from the `mock_interview` folder:
```bash
cd mock_interview
flutter build web --release
```
The compiled SPA bundle will be placed in `mock_interview/build/web/`.

#### Step 2A: Deploy to Vercel
1. Install Vercel CLI: `npm install -g vercel`
2. Deploy directly from the `mock_interview` folder:
   ```bash
   cd mock_interview
   vercel --prod
   ```
   *Vercel uses the bundled `vercel.json` to configure SPA rewrites to `/index.html` and 1-year asset caching.*

#### Step 2B: Deploy to Firebase Hosting
1. Install Firebase CLI: `npm install -g firebase-tools`
2. Initialize and deploy:
   ```bash
   cd mock_interview
   firebase login
   firebase deploy --only hosting
   ```
   *Firebase uses the bundled `firebase.json` for SPA rewrites and CDN optimization.*

---

### 6. API & Swagger Documentation

Once deployed, interactive API documentation is available out of the box:
- **Swagger Interactive UI**: `https://<your-render-url>/api/docs/`
- **ReDoc Interactive UI**: `https://<your-render-url>/api/redoc/`
- **OpenAPI Schema (JSON)**: `https://<your-render-url>/api/schema/`

---

### 7. Health Checks & System Monitoring

Render monitors application uptime using the dedicated health check endpoint:
- **Health Check URL**: `GET https://<your-render-url>/api/health/`
- **Expected Response (HTTP 200)**:
  ```json
  {
    "status": "healthy",
    "system": "AI-Based Mock Interview Preparation System",
    "version": "1.0.0"
  }
  ```

---

### 8. Automated Testing & Quality Gates

The backend includes a comprehensive automated test suite consisting of **92 unit, integration, and security tests** across all 13 Django apps.

To run the entire test suite locally:
```bash
cd backend
python manage.py test
```

Expected result:
```text
Ran 92 tests in 93.203s
OK
System check identified no issues (0 silenced).
```
