# Daily Nutrition Tracker

A starter Django web project for a daily nutrition intake tracking system.

## Features
- User registration, login, logout
- Food database management
- Daily meal records
- Nutrition dashboard with daily totals
- Basic frontend with HTML/CSS/JS

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Default database
SQLite (`db.sqlite3`)

## Main modules
- `tracker.models.Food`
- `tracker.models.MealRecord`
- `tracker.views.dashboard`

## Notes
This is an initial scaffold intended for coursework / prototype use. It can be extended with charts, nutritional goals, APIs, and reports.
