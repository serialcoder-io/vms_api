# 🧾 Voucher Management System – Backend API

A RESTful API built with Django and Django REST Framework to manage and redeem purchase vouchers in physical stores.

---

## 📘 About the Project

This API is part of a real-world Voucher Management System developed during and after my internship. It centralizes purchase voucher management and enables store employees to validate and redeem vouchers through connected mobile and desktop applications.

Authentication uses Django's default system for the admin interface and JWT tokens for client applications (mobile and desktop).

---

## 🛠 Tech Stack

- **Backend framework**: Django, Django REST Framework  
- **Authentication**: Django Admin Auth (for web admin) and JWT (for clients)  
- **Database**: PostgreSQL (default), with optional MySQL or SQLite support  
- **Python version**: 3.10+  
- **Email backend**: Configurable via environment variables  

---

## ⚙️ Step-by-step Setup

### 1. Clone the repository

```bash
git clone https://github.com/serialcoder-io/vms_api.git
cd vms_api
```
### 2. Create and activate a virtual environment

```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a .env file at the root of the project
This file will hold your environment-specific configuration, including secrets and database connection info.

````bash
# DATABASE
DB_NAME=the_db_name
DB_USER=db_user
PASSWORD=your_passowrd
DB_HOST=your_bd_host
PORT=5432

# DJANGO SETTINGS
DJANGO_SECRET_KEY=your_secret_key_here
DEBUG=True
ACCESS_TOKEN_LIFETIME=7 (your can choose the diration(it\'s in days  days))
REFRESH_TOKEN_LIFETIME=15 same thing here
PASSWORD_RESET_TIMEOUT=3600 (minuites)
ALLOWED_HOSTS=localhost,127.0.0.1,your_host
HOST=127.0.0.1
SECURE_HSTS_SECONDS=31536000
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# EMAIL
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your_email_host
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=Your_password
DEFAULT_FROM_EMAIL=your_email
````
### 6. Generate Django SECRET_KEY
You can generate a Django secret key using online tools or Python shell:

````code
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
````
Copy the output and paste it into your .env as SECRET_KEY.


### 7. Alternative database configurations

#### SQLite (development or quick start):

replace this

````bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': config('PASSWORD'),
        'HOST': DB_HOST,
        'PORT': config('PORT'),
        'OPTIONS': {
            'client_encoding': 'UTF-8',
        },
    }
}
````

by this

````bash
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
````

### 8. Apply migrations and create superuser


````bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

````

### 9. Run the development server

````bash
python manage.py runserver
````

## 🔐 Authentication Overview

Admin interface: Uses Django’s built-in authentication system.

Client applications (mobile/desktop): Use JWT tokens for secure API access.

## Api documentation

- /vms/api/schema/swagger-ui/

## 📧 Email Configuration

````text
To enable sending real emails (password resets, notifications, etc.), configure your email backend in .env as shown above and ensure:

DEBUG=False in .env to enable email sending

Valid SMTP credentials and host information

If DEBUG=True, Django will use the console or file backend to simulate email sending.
````

## 👤 Author
Developed by "Anli omar" during and after an internship, in collaboration with ms universal logistics ltd.