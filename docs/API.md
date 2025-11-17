# RESTful API Documentation

## Base URL
All RESTful API endpoints are prefixed with `/api/v1`

## Authentication
Most endpoints require authentication via Flask-Login session. Include session cookies in requests.

## API Endpoints

### Projects Resource

#### List Projects
```
GET /api/v1/projects
```

Query Parameters:
- `status` (optional): Filter by status (e.g., `approved`, `pending`, `rejected`)
- `available` (optional): Filter available projects (not expired, not full) - `true` or `false`

Example:
```
GET /api/v1/projects?status=approved&available=true
```

#### Get Single Project
```
GET /api/v1/projects/<project_id>
```

#### Create Project
```
POST /api/v1/projects
```

Body (JSON or Form):
```json
{
  "title": "Project Title",
  "description": "Project description",
  "category": "Environment",
  "date": "2024-12-31",
  "location": "Location",
  "max_participants": 20,
  "duration": 4.0,
  "points": 100,
  "requirements": "Requirements"
}
```

**Requires:** Organization authentication

#### Update Project
```
PATCH /api/v1/projects/<project_id>
```

Body (JSON):
```json
{
  "status": "approved"  // Admin only
  // or other fields for organization
}
```

**Requires:** Admin (for status changes) or Organization (for own projects)

---

### Registrations Resource

#### List Project Registrations
```
GET /api/v1/projects/<project_id>/registrations
```

**Requires:** Authentication (Organization can see all, Participant can see own)

#### Register for Project
```
POST /api/v1/projects/<project_id>/registrations
```

**Requires:** Participant authentication (Admin not allowed)

#### Get Single Registration
```
GET /api/v1/registrations/<registration_id>
```

**Requires:** Authentication (Participant can see own, Organization can see for their projects)

#### Update Registration Status
```
PATCH /api/v1/registrations/<registration_id>
```

Body (JSON):
```json
{
  "status": "approved"  // or "registered", "cancelled", "completed"
}
```

**Requires:** Organization (for their projects) or Admin

#### Cancel Registration
```
DELETE /api/v1/registrations/<registration_id>
```

**Requires:** Participant (own registrations) or Organization (for their projects)

---

### Records Resource (Volunteer Records)

#### List Records
```
GET /api/v1/records
```

Query Parameters:
- `status` (optional): Filter by status (`pending`, `approved`, `rejected`)
- `user_id` (optional): Filter by user ID (Admin only)

**Requires:** Authentication
- Participants: See own records only
- Organizations: See records for their projects
- Admins: See all records

#### Get Single Record
```
GET /api/v1/records/<record_id>
```

**Requires:** Authentication (Participant can see own, Organization can see for their projects, Admin can see all)

#### Update Record Status
```
PATCH /api/v1/records/<record_id>
```

Body (JSON):
```json
{
  "status": "approved"  // or "pending", "rejected"
}
```

**Requires:** Admin only

#### Batch Update Records
```
PATCH /api/v1/records/batch
```

Body (JSON):
```json
{
  "record_ids": [1, 2, 3],
  "status": "approved"
}
```

**Requires:** Admin only

---

### Users Resource

#### List Users
```
GET /api/v1/users
```

**Requires:** Admin only (excludes admin users)

#### Get Current User
```
GET /api/v1/users/me
```

**Requires:** Authentication

#### Get Single User
```
GET /api/v1/users/<user_id>
```

**Requires:** Authentication (Users can see own profile)

#### Update User
```
PATCH /api/v1/users/<user_id>
```

Body (JSON):
```json
{
  "is_active": true  // Admin only
  // or "display_name", "description" for own profile
}
```

**Requires:** Admin (for status changes) or User (for own profile)

---

### Dashboard Resource

#### Get Dashboard Data
```
GET /api/v1/users/me/dashboard
```

Returns different data based on user type:
- **Participant**: Statistics, registrations, badges
- **Organization**: Statistics, projects, recent projects
- **Admin**: Pending projects, pending records, users

**Requires:** Authentication

---

### Comments Resource

#### List Project Comments
```
GET /api/v1/projects/<project_id>/comments
```

#### Create Comment
```
POST /api/v1/projects/<project_id>/comments
```

Body (JSON):
```json
{
  "comment": "Comment text"
}
```

**Requires:** Participant or Organization authentication (must be registered for project, Admin not allowed)

---

## HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Not authenticated
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Response Format

All responses are in JSON format.

Success response example:
```json
{
  "id": 1,
  "status": "approved",
  "message": "Operation successful"
}
```

Error response example:
```json
{
  "error": "Error message"
}
```

## Legacy API Endpoints

All old API endpoints are still available for backward compatibility but are marked as `[DEPRECATED]`. They will continue to work but should be migrated to the new RESTful endpoints.

### Migration Guide

| Old Endpoint | New RESTful Endpoint |
|-------------|---------------------|
| `POST /api/register-project` | `POST /api/v1/projects/<id>/registrations` |
| `POST /api/admin/approve-project/<id>` | `PATCH /api/v1/projects/<id>` with `{"status": "approved"}` |
| `POST /api/admin/reject-project/<id>` | `PATCH /api/v1/projects/<id>` with `{"status": "rejected"}` |
| `POST /api/admin/approve-record/<id>` | `PATCH /api/v1/records/<id>` with `{"status": "approved"}` |
| `POST /api/admin/reject-record/<id>` | `PATCH /api/v1/records/<id>` with `{"status": "rejected"}` |
| `POST /api/admin/batch-approve-records` | `PATCH /api/v1/records/batch` with `{"record_ids": [...], "status": "approved"}` |
| `POST /api/admin/user/<id>/toggle-status` | `PATCH /api/v1/users/<id>` with `{"is_active": true/false}` |
| `GET /api/participant/dashboard-data` | `GET /api/v1/users/me/dashboard` |
| `GET /api/organization/dashboard-data` | `GET /api/v1/users/me/dashboard` |
| `GET /api/admin/dashboard-data` | `GET /api/v1/users/me/dashboard` |
| `GET /api/participant/available-projects` | `GET /api/v1/projects?available=true` |
| `GET /api/projects` | `GET /api/v1/projects?status=approved&available=true` |

