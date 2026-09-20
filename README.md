# TrizenAI Photo Sharing Platform

A production-oriented, full-stack event photo sharing web application designed for professional photography teams and event studios. The platform provides collaborative multi-user photo uploading, administrative selection & curation, PIN-protected customer galleries, server-side role-based authorization (RBAC), Supabase PostgreSQL database integration, and exclusive Cloudflare R2 Object Storage for secure media hosting.

---

## 1. Core Features & Architecture Workflows

### Role-Based Access Control (RBAC)


- **Login-Only Authentication**: Secure authentication flow restricted to pre-provisioned team members and administrators.
- **Admin / Studio Lead**:
  - Create and manage photography events.
  - Assign registered photographers and team members to specific events.
  - Review all uploaded photos across assigned team members.
  - Batch select/deselect photos for customer gallery publishing.
  - Configure 6-digit access PINs (e.g. `123456`) and publication expiration timestamps.
  - 1-click full URL clipboard copy for live public customer galleries.
- **Team Member / Photographer**:
  - Access assigned events only (strict multi-tenant event isolation).
  - Bulk upload multi-file high-resolution event photos.
  - View personal uploads and team photos within assigned event studios.
  - Strictly prohibited from accessing unassigned events or publishing galleries.
- **Customer / Client**:
  - Access PIN-protected public galleries via custom shareable links (`/gallery/<slug>/`).
  - Interactive PIN verification modal (no user account registration required).
  - High-resolution grid view of selected photos with image lightbox.

### Image Processing & Validation Pipeline
- **Automated Validation**: Image binary verification using Pillow (JPEG, PNG, WebP) with strict 25MB file size enforcement.
- **Metadata Extraction**: Automatic resolution extraction (width and height), file size calculation, and MIME type identification.
- **WebP Thumbnail Generation**: On-the-fly thumbnail rendering (`300x300` max bounding box, WebP format with Lanczos resampling).

### Exclusive Cloudflare R2 Object Storage
- **Direct Object Streaming**: All original uploads and thumbnails stream directly to Cloudflare R2 S3-compatible Object Storage bucket (`django-storages` + `boto3`).
- **Database Reference Mapping**: Database stores exact Cloudflare R2 object locations (`photo.storage_location` and presigned URLs).
- **Private Presigned Object Security**: Media access requests route through authorized presigned temporary URL redirects (`AWS_QUERYSTRING_AUTH = True`, 15-minute expiration window).

---

## 2. Technology Stack

| Layer | Technology / Library | Description |
|---|---|---|
| **Backend Framework** | Python 3.13 + Django 5.1 | Core application logic & MVC structure |
| **API Layer** | Django REST Framework (DRF) | REST endpoints for photo uploads, selection toggle, & PIN verification |
| **Database** | Supabase Managed PostgreSQL | Production relational database via `dj-database-url` / `psycopg2-binary` |
| **Object Storage** | Cloudflare R2 (S3 API) | Private cloud object storage via `django-storages` & `boto3` |
| **Image Processing** | Pillow (PIL) | Server-side validation, metadata extraction, & WebP thumbnail generation |
| **Frontend UI** | Django Templates + Tailwind CSS | Responsive dark photography UI with Lucide Icons |
| **Production Server** | Render Web Services + Gunicorn | Cloud platform deployment (`build.sh`, `Procfile`, `render.yaml`) |

---

## 3. Production Environment Reference (`.env`)

Configure the following environment variables in your production environment (Render / Supabase / Cloudflare R2):

```env
# Django Core Configuration
DEBUG=False
SECRET_KEY=your_production_django_secret_key
ALLOWED_HOSTS=your-app-name.onrender.com,localhost,127.0.0.1

# Database Configuration (Option A: Supabase Connection String)
DATABASE_URL=postgresql://postgres.xxx:your_password@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Database Configuration (Option B: Individual Env Variables)
USE_POSTGRES=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_supabase_db_password
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=6543

# Cloudflare R2 Object Storage Configuration
R2_ACCESS_KEY_ID=your_cloudflare_r2_access_key_id
R2_SECRET_ACCESS_KEY=your_cloudflare_r2_secret_access_key
R2_BUCKET_NAME=your_r2_bucket_name
R2_ACCOUNT_ID=your_cloudflare_account_id
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_REGION_NAME=auto
R2_PUBLIC_DOMAIN=https://your-custom-domain.com
```

---

## 4. Local Setup & Installation

### Prerequisites
- Python 3.13+ installed
- Git installed

### Installation Steps

1. **Clone Repository**:
   ```bash
   git clone https://github.com/imsachinnnn/trizen-ai.git
   cd trizen
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

5. **Apply Database Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create Admin Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Start Development Server**:
   ```bash
   python manage.py test
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

---

## 5. Automated Test Suite

Run the full Django test suite to verify authentication, event isolation, Pillow processing, PIN verification, and object security:

```bash
python manage.py test
```

### Verified Integration Tests (10/10 Passing)
1. `test_admin_and_team_member_login`: Validates role authentication and session management.
2. `test_team_member_event_isolation`: Verifies unassigned team members receive `403 Forbidden` on private events.
3. `test_team_member_cannot_publish_gallery`: Verifies non-admins cannot publish galleries (`403 Forbidden`).
4. `test_photo_upload_processing_and_thumbnail`: Tests image validation, Pillow metadata extraction, and WebP thumbnail rendering.
5. `test_gallery_pin_protection_locked_state`: Verifies unpublished/locked galleries present PIN prompt.
6. `test_gallery_pin_verification_wrong_pin`: Submitting incorrect PIN returns `401 Unauthorized`.
7. `test_gallery_pin_verification_correct_pin`: Submitting correct PIN (`123456`) unlocks gallery session.
8. `test_unpublished_gallery_returns_404`: Accessing unpublished gallery as customer returns `404 Not Found`.
9. `test_private_photo_access_cannot_be_bypassed`: Verifies direct unauthorized photo access is blocked (`403 Forbidden`).
10. `test_admin_can_delete_photo_and_team_member_forbidden`: Verifies photo deletion is strictly restricted to Admins.

---

## 6. Render & Production Deployment

The project includes pre-configured deployment blueprints for **Render Web Services**:

- **[`Procfile`](file:///c:/Users/sachi/OneDrive/Desktop/trizen/Procfile)**: `web: gunicorn photo_sharing.wsgi:application`
- **[`build.sh`](file:///c:/Users/sachi/OneDrive/Desktop/trizen/build.sh)**: Automatic `pip install`, `collectstatic`, and `migrate` execution script.
- **[`render.yaml`](file:///c:/Users/sachi/OneDrive/Desktop/trizen/render.yaml)**: Blueprint configuration.

### Render Configuration Steps
1. Create a new **Web Service** on [Render](https://render.com) connected to your GitHub repository.
2. Set **Environment** to `Python 3`.
3. Set **Build Command** to `./build.sh`.
4. Set **Start Command** to `gunicorn photo_sharing.wsgi:application`.
5. Add your Environment Variables (`DATABASE_URL`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, etc.) under **Settings > Environment**.
