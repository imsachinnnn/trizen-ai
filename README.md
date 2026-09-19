# TrizenAI Full-Stack Photo Sharing Platform

A production-oriented full-stack photo-sharing web application built for event photography teams. The platform enables multi-user photo uploads, administrative curation & selection, PIN-protected public customer galleries, server-side role-based authorization, and private object storage with signed URL access.

Designed in accordance with **TrizenAI Anti-AI-Slop Design Guidelines** — photography-first, clean dark neutral/charcoal UI, restrained typography, and robust security architecture.

---

## 1. Features & Core Workflows

- **Role-Based Security (RBAC)**: Distinct permissions for **Admin / Lead** and **Team Members**.
  - **Admin**: Create events, assign team members, review all uploaded photos, select/batch toggle gallery photos, publish galleries, configure 6-digit access PINs.
  - **Team Member**: View assigned events, upload multi-file event photos, view personal uploads. Cannot publish galleries or access unassigned events.
  - **Customer**: Access shareable gallery links (`/gallery/<slug>/`) protected by a 6-digit PIN — no account required.
- **Pillow Image Processing**: Automatic image validation (JPEG, PNG, WebP), metadata extraction (width, height, file size, MIME type), and WebP thumbnail generation (`300x300` max dimensions).
- **Private Object Storage Architecture**: Cloudflare R2 / AWS S3 private object storage integration using signed temporary URLs. Direct unauthenticated object URLs return `403 Forbidden` / `404 Not Found`.
- **Responsive Dark Photography UI**: Charcoal base (`#09090b`), dark zinc containers (`#18181b`), slate borders (`#27272a`), touch-friendly mobile PIN keypad, drag-and-drop upload zone, and photo lightbox modal.

---

## 2. Technology Stack

- **Backend Framework**: Python 3.13 + Django 5.x + Django REST Framework (DRF)
- **Database**: PostgreSQL (Consistent across local development & production)
- **Image Processing**: Pillow (Python Imaging Library)
- **Object Storage**: Cloudflare R2 / AWS S3 private bucket via `django-storages` + `boto3` (Fallback to local authenticated private media serving for zero-config offline dev)
- **Frontend**: Django Templates + Tailwind CSS + Vanilla JS / Alpine.js + Lucide Icons
- **Production Server**: Gunicorn + Nginx + OCI Ubuntu VM + Certbot HTTPS

---

## 3. System Architecture & Data Schema

### Architecture Diagram

```text
                         ┌─────────────────────────┐
                         │        Browser          │
                         │                         │
                         │ Admin / Team / Customer │
                         └────────────┬────────────┘
                                      │
                                    HTTPS
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │         Nginx           │
                         │ Reverse Proxy / TLS     │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │     Django 5 + DRF      │
                         │                         │
                         │ Authentication           │
                         │ RBAC Middleware         │
                         │ Events & Photos         │
                         │ PIN Verification        │
                         │ Signed URL Generator    │
                         └──────────┬───────┬──────┘
                                    │       │
                         ┌──────────┘       └──────────┐
                         ▼                             ▼
                ┌──────────────────┐          ┌──────────────────┐
                │    PostgreSQL    │          │  Cloudflare R2   │
                │  (Primary DB)    │          │  (Private Bucket)│
                │                  │          │                  │
                │ Users            │          │ Original Photos  │
                │ Events & Members │          │ Thumbnails       │
                │ Photo Metadata   │          │ Private Objects  │
                │ Galleries        │          └──────────────────┘
                └──────────────────┘
```

### Database Schema (ERD Overview)

- **`User`**: `id` (UUID), `email` (Unique), `name`, `role` (`ADMIN` | `TEAM_MEMBER`), `created_at`
- **`Event`**: `id` (UUID), `title`, `description`, `event_date`, `location`, `created_by_id`, `created_at`
- **`EventMember`**: `id` (UUID), `event_id`, `user_id` (`unique(event, user)`)
- **`Photo`**: `id` (UUID), `event_id`, `uploaded_by_id`, `image`, `thumbnail`, `filename`, `file_size`, `mime_type`, `width`, `height`, `is_selected`
- **`Gallery`**: `id` (UUID), `event_id` (Unique), `slug` (Unique), `pin_hash` (PBKDF2/SHA256), `is_published`, `published_at`

---

## 4. Local Setup & Quickstart Guide

### Prerequisites
- Python 3.13+
- PostgreSQL (or local SQLite fallback)

### Step-by-Step Local Setup

1. **Clone Repository & Navigate to Directory**:
   ```bash
   git clone <repository_url>
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

4. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and set your PostgreSQL credentials:
   ```bash
   cp .env.example .env
   ```

5. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Seed Demo Data**:
   Populates demo Admin, Team Member, "Arjun & Priya Wedding" event, sample photos, and published gallery (`/gallery/arjun-priya-wedding/` with PIN `482917`).
   ```bash
   python manage.py seed_demo_data
   ```

7. **Run Local Server**:
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

---

## 5. Demo Credentials & Gallery Details

| Role | Email | Password | Access Rights |
|---|---|---|---|
| **Admin / Lead** | `admin@trizen.com` | `AdminPass123!` | Create events, assign team, curate photo selections, publish gallery, configure PIN |
| **Team Member** | `photographer@trizen.com` | `TeamPass123!` | View assigned events, upload multi-file photos |

### Demo Gallery URL & Access PIN
- **Gallery URL**: `http://127.0.0.1:8000/gallery/arjun-priya-wedding/`
- **Access PIN**: `482917`

---

## 6. Running Automated Tests

Run the full integration test suite covering Auth, RBAC isolation, Pillow processing, PIN verification, and private object access protection:

```bash
python manage.py test core
```

### Verified Test Suite Summary (9 Tests)
1. `test_admin_and_team_member_login`: Validates auth and session creation.
2. `test_team_member_event_isolation`: Verifies Team Member cannot access unassigned events (403 Forbidden).
3. `test_team_member_cannot_publish_gallery`: Verifies 403 Forbidden on publish endpoint for non-admins.
4. `test_photo_upload_processing_and_thumbnail`: Tests image validation, Pillow metadata extraction, and thumbnail creation.
5. `test_gallery_pin_protection_locked_state`: Accessing `/gallery/<slug>/` without PIN returns PIN prompt.
6. `test_gallery_pin_verification_wrong_pin`: Submitting wrong PIN returns 401 Unauthorized.
7. `test_gallery_pin_verification_correct_pin`: Submitting correct PIN unlocks session and grants access to published photos.
8. `test_unpublished_gallery_returns_404`: Attempting to access unpublished gallery returns 404 Not Found.
9. `test_private_photo_access_cannot_be_bypassed`: Verifies unauthenticated/direct photo access requests are blocked (`403 Forbidden`).

---

## 7. Production Deployment (OCI Ubuntu + Nginx + Gunicorn)

1. **Provision Server**: OCI Ubuntu 24.04 LTS instance with open HTTP (80) & HTTPS (443) ports.
2. **Install System Dependencies**:
   ```bash
   sudo apt update && sudo apt install -y python3-venv python3-pip postgresql nginx certbot python3-certbot-nginx
   ```
3. **Configure PostgreSQL**:
   ```bash
   sudo -u postgres psql -c "CREATE DATABASE trizen_db;"
   sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'your_secure_password';"
   sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE trizen_db TO postgres;"
   ```
4. **Deploy Application & Gunicorn**:
   ```bash
   gunicorn --workers 3 --bind 127.0.0.1:8000 photo_sharing.wsgi:application
   ```
5. **Nginx Reverse Proxy & SSL**:
   Configure Nginx reverse proxy to `127.0.0.1:8000` and execute `sudo certbot --nginx` for free SSL termination.
