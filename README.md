# Sustainable Volunteer Service Platform

A web application connecting volunteers with organizations to practice sustainable development goals.

## Features

- **Three User Types**: Participants, Organizations, and Administrators
- **Project Management**: Create, browse, and register for volunteer projects
- **Sustainability Rating**: 0-5 star rating system with color-coded badges
- **Volunteer Hours Tracking**: Track and certify volunteer hours
- **Points & Badges System**: Earn points and achievement badges
- **Responsive Design**: Works on desktop and tablet devices

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Design**: Green eco-friendly theme with 8px border radius

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask application:
```bash
# Option A: using Flask CLI
set FLASK_APP=app.py & set FLASK_ENV=development & flask run

# Option B: run directly
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`
- User Type: Administrator

**⚠️ Important: Change the default admin password after first login!**

## Project Structure

```
/
├── app.py                      # App factory, registers blueprints, seeds admin
├── config.py                   # Configuration (secret key, DB URI, etc.)
├── models.py                   # SQLAlchemy models and db instance
├── routes.py                   # All Flask routes (Blueprint 'main')
├── forms.py                    # Minimal form parsers for login/register
├── requirements.txt            # Python dependencies
├── templates/                  # HTML templates
│   ├── index.html             # Home page
│   ├── login.html             # Login/Register page
│   ├── participant_dashboard.html
│   ├── organization_dashboard.html
│   ├── admin_panel.html
│   ├── project_detail.html
│   └── volunteer_record.html
├── static/                     # Static files
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   └── js/
│       ├── home.js
│       ├── auth.js
│       └── participant.js
└── volunteer.db               # SQLite database (auto-created)
```

## Pages

1. **Home Page** - Platform introduction, statistics, featured projects
2. **Login/Register** - User authentication with role selection
3. **Participant Dashboard** - Personal stats, badges, projects
4. **Organization Dashboard** - Create and manage projects
5. **Admin Panel** - Approve projects and volunteer hours
6. **Project Detail** - Complete project information and registration
7. **Volunteer Record** - Hour tracking with filtering and export

## Database Models

- **User**: Stores user accounts (participants, organizations, admins)
- **Project**: Volunteer project information
- **Registration**: Project registrations by participants
- **VolunteerRecord**: Certified volunteer hours and points

## API Endpoints

- `GET /api/projects` - List all approved projects
- `POST /api/register-project` - Register for a project

## Customization

### Change Color Theme

Edit `/static/css/style.css` and modify the CSS variables:
```css
:root {
  --primary-green: #16a34a;
  --secondary-blue: #3b82f6;
  /* ... other variables */
}
```

### Change Secret Key

Edit `app.py` and change the secret key:
```python
app.config['SECRET_KEY'] = 'your-new-secret-key'
```

## License

MIT License - feel free to use this project for educational or commercial purposes.

## Support

For issues or questions, please open an issue on the project repository.
