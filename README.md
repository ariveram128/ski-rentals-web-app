[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/hLqvXyMi)

# SkiRentals Web App - Project A-25

## Latest Updates (March 29, 2024)

### Customized Admin Interface
We've implemented a fully customized Django admin interface that matches our site's design:

- **Brand-Consistent Styling**: The admin UI now uses our SkiRentals color scheme and typography
- **Improved UI Elements**: Enhanced forms, buttons, and tables for better usability
- **Image Thumbnails**: Equipment listings show thumbnail previews directly in admin lists
- **Custom Login Page**: Distinct admin login page that clearly separates from user authentication
- **Responsive Design**: Admin interface works well on all screen sizes
- **S3 Integration**: Admin image uploads work correctly with our S3 storage

### S3 Integration Complete
We've successfully implemented AWS S3 for file storage with the following features:

- **Profile Pictures**: Users can now upload and update profile pictures
- **Equipment Images**: Equipment listings support multiple image uploads
- **Secure Storage**: All images are stored in S3 with proper permissions

### Model Improvements
- Consolidated UserProfile models to fix conflicts
- Enhanced Equipment model with proper image relationships
- Added EquipmentImage model for multiple images per equipment item

### UI Enhancements
- Homepage now displays actual equipment from the database
- Fixed navigation for different user types (librarian vs patron)
- Improved equipment catalog display with actual images
- Enhanced modals and forms for better user experience

### Bug Fixes
- Resolved issues with multiple file uploads
- Fixed template inconsistencies
- Improved modal behavior in the rental management screen

## Frontend Progress (Updated March 10, 2024)

Latest updates to the frontend:

- Created a base template with a responsive navbar and footer
- Built a modern homepage with hero section and featured equipment
- Set up the equipment catalog page with cards and filtering
- Added equipment detail page for individual items
- Created forms for adding new equipment (admin only)
- Fixed up the Google OAuth flow with custom templates
- Implemented dashboards for both patrons and librarians
- Made a profile page with rental history and settings
- Added a help page with FAQs

All the templates are now properly styled with our color scheme (check out the CSS vars in static/css/main.css). The Google login flow is also working and has a consistent design - no more ugly default pages!

### Login/Authentication
We're using Django-allauth for Google OAuth. I've customized all the auth-related pages:
- Login
- Signup
- Password reset
- Google auth screens

The navbar now correctly shows either sign-in or the user dropdown based on authentication state.

### Still To Do
- Fix a few responsive design issues / Identify what is not working correctly
- Add placeholder images (the img URLs are set up but we need actual images)
- Set up the JavaScript for filtering on the equipment page
- Create the cart functionality
- Connect the frontend to the backend models

To test it out, just run:
```bash
python manage.py runserver
```

### Sprint 04 Plans (Due March 16)
For the next sprint, we need to implement AWS S3 for file storage along with other features. Here's what we need to focus on:

1. **Amazon S3 Integration (Required for Sprint 04)**: 
   - Set up AWS S3 buckets for file storage
   - Implement user profile picture uploads
   - Add image upload functionality for equipment items
   - Create the necessary models and forms for handling file uploads

2. **Backend Connection**: Wire up all the templates to actually work with our models
   - Connect the equipment catalog to actual database entries
   - Make user profiles store and display real data

3. **Rental Process**: Implement the full rental flow (browse → add to cart → checkout → confirmation)

4. **Search & Filter**: Get the equipment search/filter functionality working with JavaScript

5. **GitHub Actions CI**: Set up continuous integration with at least a few working tests
   - Create basic model tests for equipment and user profiles
   - Add tests for the file upload functionality

6. **Bugfixes**: Address any responsive issues and template bugs from Sprint 03

## Admin Interface

The project includes a custom-styled Django admin interface that matches our main site's design while providing powerful management capabilities.

### Admin Features
- **Consistent Branding**: Uses the same colors, fonts, and styles as the main site
- **Enhanced Equipment Management**: Thumbnail previews, image galleries, and detailed forms
- **Improved UX**: Better form styling, responsive tables, and intuitive navigation
- **Clear Admin/User Separation**: Custom login page that clearly indicates admin-only access
- **Streamlined Workflow**: Optimized for common administrative tasks

### Available Models
- Equipment: Manage inventory of winter sports equipment (with image uploads)
- MaintenanceRecord: Track equipment maintenance history
- Rental: Handle rental transactions
- Review: Manage customer reviews
- UserProfile: User management and preferences
- Collection: Manage equipment groupings (public and private)

### Admin Access
1. Create a superuser:
```bash
python manage.py createsuperuser
```

2. Run the development server:
```bash
python manage.py runserver
```

3. Access the admin interface at: http://127.0.0.1:8000/admin

### Admin Implementation Details
The admin customization uses template overrides and custom CSS to provide a consistent look and feel while maintaining full Django admin functionality. Key components:

- `templates/admin/` - Contains template overrides for admin pages
- `static/admin/css/` - Custom CSS files for admin styling
- `equipment/admin.py` - Custom AdminSite and model admin classes

## Testing

The project includes comprehensive test suites for core functionality. All tests are located in `equipment/tests.py`.

### Current Test Coverage

✅ **Basic Model Testing**
- Equipment creation and validation
- Rental transaction management
- User profile configuration

### Running Tests

```bash
# Run all tests
python manage.py test equipment

# Run specific test class
python manage.py test equipment.tests.EquipmentTests
```

### Test Implementation TODO

The following test cases need implementation:

1. **Equipment Management**
   - [ ] Equipment availability tracking
   - [ ] Maintenance scheduling
   - [ ] Rating calculations

2. **Rental Operations**
   - [ ] Rental extensions
   - [ ] Late return processing
   - [ ] Rental history tracking

3. **User Management**
   - [ ] Equipment recommendations
   - [ ] Experience level validation
   - [ ] Rental history association

4. **Review System**
   - [ ] Review creation and validation
   - [ ] Rating constraints
   - [ ] Equipment rating updates

### Contributing Tests

When implementing new tests:

1. Follow existing test patterns in `equipment/tests.py`
2. Include descriptive docstrings
3. Test both success and error cases
4. Run the full test suite before committing

```bash
# Check test coverage
python manage.py test equipment --verbosity=2
```

## Environment Setup

To run this project locally, you'll need to set up the following environment variables in a `.env` file in the project root:

```
USE_S3=False
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_STORAGE_BUCKET_NAME=your_bucket_name
```

Without these properly configured, image uploads will not function correctly.

### Installation

1. Clone the repository
2. Create a virtual environment and activate it
3. Install the dependencies:
```bash
pip install -r requirements.txt
```
4. Apply migrations:
```bash
python manage.py migrate
```
5. Create a superuser (for admin access):
```bash
python manage.py createsuperuser
```
6. Run the development server:
```bash
python manage.py runserver
```
