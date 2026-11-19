# AI-Based Mock Interview Preparation System
## Complete Django Backend & Flutter Integration

An enterprise-grade, end-to-end recruitment and AI-powered mock interview preparation system. Features a modular **Python / Django REST Framework** backend and a cross-platform **Flutter** client (Mobile & Web).

---

### Key Modules & Capabilities

- **Role-Based Access Control (RBAC)**: Distinct permissions, authentication, and workflows for **Admin**, **Company**, and **Candidate (User)** roles.
- **AI Mock Interview Engine**:
  - Dynamic interview question generation powered by **Google Gemini API** (`gemini-1.5-flash`) with fallback domain-specific question synthesizer.
  - Multi-category support: **Technical**, **HR / Culture Fit**, **General & Behavioral**, and **Job-Specific Competencies**.
  - Multi-tier difficulty levels: **Junior**, **Mid**, and **Senior**.
- **AI Answer Evaluation**:
  - Multidimensional scoring criteria: **Relevance**, **Technical Accuracy**, **Completeness**, and **Clarity & Communication**.
  - Generates composite scores (0-100%), actionable candidate feedback, observed strengths, and targeted improvement suggestions.
- **Privacy-Conscious Camera Telemetry**:
  - Built with **OpenCV**. Analyzes candidate posture alignment, head stability, and camera/screen focus proxy.
  - Strictly non-psychological: Does not claim to measure emotions or personality, and is never used as an automated rejection filter. Candidate consent is enforced.
- **Job Vacancy & Application Management**:
  - Full CRUD for verified companies, search, filters, pagination, and duplicate application prevention.
- **Assessment & Interview Scheduling**:
  - Schedule assessments and rounds with automated scheduling conflict detection across candidate and company calendars.
- **PDF Report Generation**:
  - Professional, branded evaluation report cards generated using **ReportLab** (`/api/v1/reports/mock-interviews/<id>/pdf/`).
- **Feedback & Complaints Center**:
  - Full grievance lifecycle with administrative review, status tracking, and reply threads.
- **Notifications Hub**:
  - Real-time updates for application statuses, assessment schedules, and administrative replies.
- **100% Backward Compatibility Layer**:
  - Dedicated compatibility layer (`/myapp/*`) seamlessly servicing all 14 legacy endpoints expected by the existing Flutter mobile application.
- **Automated Testing Suite**:
  - **92 comprehensive tests** covering authentication, company verification, vacancy pipelines, scheduling conflicts, AI generation, answer grading, telemetry, security, and legacy endpoints.

---

### Project Structure

```text
AI-Based-Mock-Interview-Preparation-System/
├── backend/
│   ├── apps/
│   │   ├── accounts/          # Custom User model, RBAC, SimpleJWT auth, Admin API
│   │   ├── companies/         # Company profiles, verification, reviews, dashboard
│   │   ├── candidates/        # Candidate profiles, photo/resume uploads, dashboard
│   │   ├── vacancies/         # Vacancy CRUD, active filtering, candidate applications
│   │   ├── applications/      # Application tracking, status updates, withdrawals
│   │   ├── tests_app/         # Test schedules, candidate assignments, attendance
│   │   ├── interviews/        # Interview schedules, conflict detection, rescheduling
│   │   ├── ai_interviews/     # Gemini dynamic questions, AI grading, camera telemetry
│   │   ├── feedback/          # User feedback submission and administrative review
│   │   ├── complaints/        # Grievance filing, status management, admin replies
│   │   ├── notifications/     # User notification center and read receipts
│   │   ├── reports/           # ReportLab PDF report card generator
│   │   └── compatibility/     # Flutter legacy API layer (/myapp/*)
│   ├── mock_interview_backend/
│   │   ├── settings.py        # Django production & security configurations
│   │   ├── urls.py            # Swagger/OpenAPI documentation and root routing
│   │   ├── wsgi.py / asgi.py  # Production WSGI & ASGI entrypoints
│   ├── build.sh               # Render build script (collectstatic & migrate)
│   ├── Procfile               # Gunicorn deployment configuration
│   ├── render.yaml            # Render Blueprint specification
│   ├── requirements.txt       # Production dependencies
│   └── manage.py
├── mock_interview/            # Flutter Mobile & Web Client
│   ├── lib/
│   │   ├── config/            # Centralized API Configuration (api_config.dart)
│   │   ├── ai_mock_interview.dart # AI Mock Interview Interactive Screen
│   │   ├── home.dart          # Candidate home dashboard with AI entrypoint
│   │   ├── login.dart         # Authentication with JWT & legacy lid persistence
│   │   └── ...                # Profile, vacancy, test, feedback, & complaint screens
│   ├── vercel.json            # Vercel deployment configuration
│   ├── firebase.json          # Firebase Hosting configuration
│   └── pubspec.yaml
├── DEPLOYMENT.md              # Complete Production Deployment Guide
└── README.md                  # Project overview and documentation
```

---

### Quickstart Guide

#### 1. Backend Setup (Local Development)

```bash
cd backend

# Create and activate a Python virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# (Optional) Create administrative superuser
python manage.py createsuperuser

# Run local development server on port 8000
python manage.py runserver 0.0.0.0:8000
```

#### 2. Run the Automated Test Suite

```bash
cd backend
python manage.py test
```
*Expected: 92 tests passing (OK).*

#### 3. Access Interactive API Documentation
- **Swagger Interactive UI**: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **ReDoc Interactive UI**: [http://127.0.0.1:8000/api/redoc/](http://127.0.0.1:8000/api/redoc/)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/)

#### 4. Run Flutter Mobile App

```bash
cd mock_interview
flutter pub get
flutter run
```

---

### Deployment

For complete instructions on deploying the Django backend to **Render** and the Flutter Web client to **Vercel** or **Firebase Hosting**, refer to [DEPLOYMENT.md](file:///c:/Users/LOQ/Downloads/AI-Based-Mock-Interview-Preparation-System-main/AI-Based-Mock-Interview-Preparation-System-main/DEPLOYMENT.md).
