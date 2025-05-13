# SkiRentals Web App - Portfolio Project

This SkiRentals Web App was created as a team project for CS 3240: "Software Engineering" at the University of Virginia. Our assignment was to build a "Cataloging and Lending App" (CLA) that lets users catalog, share, and lend items. Our team focused on ski and winter sports equipment.

This repository shows my contributions to the project, where I worked as the **Software Architect** and a **main developer**. I led and built major parts of the backend, database design, frontend, and cloud integrations.

## My Role and Contributions (ariveram128)

As the **Software Architect** and lead developer, I helped shape the project from start to finish. My work included:

**1. Architecture Design & Requirements:**
* Served as the official Software Architect, analyzing requirements and designing solutions
* Led the implementation of the "Patrons creating public Collections" feature in Sprint 5
* Designed model changes and guided the team through implementation

**2. Backend Development & Database:**
* Set up the core Django app structure and initial database design
* Built the "Collections" feature from scratch, including public/private collections and access controls
* Integrated AWS S3 for all image uploads (profile pictures, equipment images)
* Developed user role management (Patron to Librarian promotion)
* Implemented seasonal pricing, rental calculations, and fixed related bugs

**3. Frontend Development:**
* Built key pages like the homepage, dashboards, equipment catalog, and detail pages
* Customized all login/signup screens for a consistent look
* Created dynamic content displays and interactive features
* Fixed numerous UI bugs and responsive design issues

**4. Admin Interface Improvements:**
* Enhanced the Django admin interface with custom styling
* Added image thumbnails for equipment listings
* Created a custom admin login page
* Set up admin views for core models

**5. Testing & DevOps:**
* Wrote unit tests for features like ski size validation
* Helped set up the testing infrastructure
* Configured the app for Heroku deployment and S3 integration

**6. Project Management:**
* Participated in team Git workflow
* Managed and reviewed pull requests
* Ensured code quality and project goals were met

## Project Overview

This app was developed as a "Cataloging and Lending App" to help users catalog items and lend them to others.

**Key Terms:**
* **Items:** Individual things available for borrowing (skis, snowboards, etc.)
* **Collection:** A group of items based on a theme
* **Library:** All items within the app

### Core Features
* **Login:** Google Account login for users
* **User Types:**
  * **Visitors:** Can browse but not interact
  * **Patrons:** Can create accounts, borrow items, rate/comment, and create public collections
  * **Librarians:** Can manage items and collections, approve/deny borrow requests
  * **Administrators:** Have access to the Django Admin panel
* **Equipment Management:** Add, edit, and delete items with details and images
* **Collections:** Group items by theme (public or private)
* **Search:** Find items and collections using keywords
* **Rentals:** Request to borrow items, approve/deny requests, track borrowed items
* **Reviews:** Rate and comment on items
* **Cloud Storage:** AWS S3 for all file uploads
* **Custom Admin:** Themed admin panel for site management
* **Responsive Design:** Works on different screen sizes
* **Notifications:** Alerts for rental requests and collection access

### Tech Stack
* **Backend:** Python 3, Django 5
* **Frontend:** HTML, CSS, JavaScript
* **Database:** PostgreSQL (production), SQLite (development)
* **Login:** Django-allauth with Google OAuth2
* **File Storage:** Amazon S3
* **CI/CD:** GitHub Actions
* **Hosting:** Heroku

## Admin Interface

The project has a customized Django admin interface for site administrators.

### Features
* Matches SkiRentals branding (colors and design)
* Shows image thumbnails in equipment listings
* Provides user-friendly forms for adding/editing items
* Includes a custom admin login page
* Manages all core models (Equipment, Rentals, Reviews, etc.)

### Access
1. Create a Django admin user:
   ```bash
   python manage.py createsuperuser
   ```
2. Go to: `http://127.0.0.1:8000/admin/`

## Testing

The project includes tests for core functions in `equipment/tests.py` and the `tests/` directory.

### Running Tests
```bash
# Run all equipment tests
python manage.py test equipment

# Run all tests in the tests directory
python manage.py test tests

# Run with more details
python manage.py test equipment --verbosity=2
```

## Setup & Installation

To run this project locally:

1. Clone the repository:
   ```bash
   git clone git@github.com:ariveram128/ski-rentals-web-app.git
   cd ski-rentals-web-app
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   
   # On Mac/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with these settings:
   ```
   DJANGO_SECRET_KEY='your_secret_key'
   DEBUG=True
   
   # S3 Storage
   USE_S3=False  # Set to True to use AWS S3
   AWS_ACCESS_KEY_ID='your_aws_key'
   AWS_SECRET_ACCESS_KEY='your_aws_secret'
   AWS_STORAGE_BUCKET_NAME='your_bucket_name'
   AWS_S3_REGION_NAME='your_region'
   
   # Email settings
   EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST='smtp.gmail.com'
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER='your_email@gmail.com'
   EMAIL_HOST_PASSWORD='your_app_password'
   DEFAULT_FROM_EMAIL='your_email@gmail.com'
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Create an admin user:
   ```bash
   python manage.py createsuperuser
   ```

7. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

8. Run the server:
   ```bash
   python manage.py runserver
   ```

9. Visit `http://127.0.0.1:8000/` in your browser
