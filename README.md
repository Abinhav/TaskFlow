# TaskFlow – To-Do Management System

A full-stack, multi-user To-Do Management System built using **Python, Flask, PostgreSQL, and SQLAlchemy**.

TaskFlow helps users organize daily tasks, manage priorities, track deadlines, and monitor completed activities through a clean and responsive interface.

## Features

### User Authentication
- User registration and login
- Secure password hashing
- Protected dashboard
- User-specific task management
- Logout functionality

### Task Management
- Create, view, edit, and delete tasks
- Set task start dates and due dates
- Add task descriptions
- Set task priorities
- Upload task images
- Mark tasks as completed
- Track task completion timestamps

### Dashboard
- View task statistics
- Search tasks
- Filter tasks
- Sort tasks
- View completed task history

### Profile Management
- View user profile details
- Edit username and email
- Change password securely
- Upload and update profile pictures

### Additional Features
- Contact form with email integration
- CSRF protection
- Custom 404 and 500 error pages
- Application logging
- Environment-based configuration
- File upload validation

## Tech Stack

| Category | Technologies |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | Flask-Login, Werkzeug |
| Database Migrations | Flask-Migrate |
| Security | Flask-WTF, CSRF Protection |
| Email | SMTP |
| Version Control | Git, GitHub |

## Project Structure

```text
todo_management/
│
├── app/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   └── script.js
│   │   └── images/
│   │
│   ├── templates/
│   │   ├── 404.html
│   │   ├── 500.html
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── edit_profile.html
│   │   ├── change_password.html
│   │   ├── create_task.html
│   │   ├── edit_task.html
│   │   └── contact.html
│   │
│   ├── __init__.py
│   ├── extensions.py
│   └── models.py
│
├── migrations/
├── logs/
├── .env
├── .gitignore
├── requirements.txt
└── run.py
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Abinhav/TaskFlow.git
cd TaskFlow
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database named:

```sql
CREATE DATABASE taskflow_db;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root directory.

Add your own configuration:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/taskflow_db

SECRET_KEY=your-secret-key

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_RECEIVER=receiver-email@gmail.com

FLASK_DEBUG=False
```

Replace the example values with your own credentials.

**Important:** Never upload your `.env` file or expose passwords, secret keys, or email credentials on GitHub.

### 6. Apply Database Migrations

```powershell
python -m flask --app run:app db upgrade
```

### 7. Run the Application

```bash
python run.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

Register an account and start managing your tasks!

## Security

- Passwords are stored using secure password hashing.
- CSRF protection is enabled for forms.
- Authentication is required for protected routes.
- Users can access only their own tasks.
- File uploads are restricted by extension and size.
- Sensitive configuration is stored in environment variables.
- Session cookie security settings are configured.

## Future Enhancements

- Task reminders and email notifications
- Calendar integration
- REST API integration
- Docker containerization
- CI/CD pipeline using Jenkins
- Cloud deployment
- Automated testing

## Author

**Abinhav Suthan**

- GitHub: https://github.com/Abinhav
- Project Repository: https://github.com/Abinhav/TaskFlow

## License

This project is available for learning and educational purposes. Add an appropriate open-source license if you intend to distribute it under specific reuse terms.