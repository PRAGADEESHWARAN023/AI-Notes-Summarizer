# 🧠 AI Notes Summarizer

A Django-based web application that extracts and summarizes notes from uploaded documents using AI-powered processing.

## 🚀 Features

- Upload PDF files and extract their content
- Automatically summarize extracted notes
- REST API integration using Django REST Framework
- Token-based authentication using JWT
- PostgreSQL as the database
- Environment configuration via `.env`

```

## 🛠️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/your-username/AI-Notes-Summarizer.git
cd AI-Notes-Summarizer/Project
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Create a PostgreSQL database**

Make sure PostgreSQL is installed and running. Then create a new database:

```sql
CREATE DATABASE notes_summarizer_db;
CREATE USER summarizer_user WITH PASSWORD 'yourpassword';
ALTER ROLE summarizer_user SET client_encoding TO 'utf8';
ALTER ROLE summarizer_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE summarizer_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE notes_summarizer_db TO summarizer_user;
```

5. **Create a `.env` file**

Create a `.env` file and add:

```env
DEEPAI_API_KEY=your API_Key
SECRET_KEY=your_django_secret_key
DEBUG=True
DB_NAME=notes_summarizer_db
DB_USER=summarizer_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

6. **Configure `settings.py` for PostgreSQL**

Ensure `DATABASES` in `settings.py` looks like:

```python
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

7. **Apply migrations and run server**

```bash
python manage.py migrate
python manage.py runserver
```
