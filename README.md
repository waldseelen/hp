# 🚀 Buğra AKIN - Django Portfolio Website

A modern, professional portfolio website built with Django, featuring dark theme, responsive design, and comprehensive content management system.

## ✨ Technology Stack

This portfolio website is built with:

### 🎯 Core Framework
- **⚡ Django 5.2** - High-level Python web framework
- **🐍 Python 3.11+** - Modern Python for robust backend development
- **🎨 Tailwind CSS** - Utility-first CSS framework for responsive design

### 🧩 UI Components & Styling
- **🌙 Dark Theme** - Elegant dark design with smooth transitions
- **📱 Responsive Design** - Mobile-first approach with Alpine.js interactions
- **✨ Starfield Animation** - Dynamic background effects
- **🎨 Custom CSS** - Optimized styling without build process

### 📋 Content Management
- **📝 Dynamic Content** - Flexible PersonalInfo model system
- **📚 Blog System** - Full-featured blog with search and categorization
- **🔧 Tools Showcase** - Curated development tools and resources
- **📞 Contact Form** - Secure contact system with rate limiting

### 🗄️ Database & Backend
- **🗄️ SQLite** - Development database (PostgreSQL ready for production)
- **🔐 Custom User Model** - Enhanced authentication system
- **📊 Django Admin** - Powerful admin interface for content management
- **🛡️ Security Features** - CSRF protection, input validation, rate limiting

### 🎨 Advanced Features
- **🔍 Search Functionality** - Blog and tools search capabilities
- **📱 Mobile Navigation** - Responsive mobile menu with Alpine.js
- **💾 Caching System** - Performance optimization with Django cache
- **📧 Email Integration** - Contact form with email notifications

## 🚀 Project Setup and Quick Start

Follow these steps to get the project running locally.

### 1. Prerequisites

- Python 3.11 or later
- pip (Python package installer)
- Virtual environment (recommended)

### 2. Installation

Clone the repository and set up the project environment.

```bash
git clone <repository-url>
cd <project-directory>

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root of the project for production settings (optional for development).

```bash
cp .env.example .env
```

Environment variables (all optional for development):
- `SECRET_KEY`: Django secret key for production
- `DEBUG`: Set to False for production (defaults to True)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `ADMIN_URL`: Custom admin URL path (defaults to 'admin/')
- `EMAIL_*`: Email configuration for contact form notifications

### 4. Database Setup

Navigate to the Django project directory and set up the database.

```bash
cd portfolio_site

# Run migrations to create database tables
python manage.py migrate

# Create a superuser for admin access (optional)
python manage.py createsuperuser
    
# Collect static files (for production)
python manage.py collectstatic
```

### 5. Running the Development Server

Start the Django development server.

```bash
# Make sure you're in the portfolio_site directory
python manage.py runserver
```

The application will be available at [http://localhost:8000](http://localhost:8000).

### Available Commands

- `python manage.py runserver`: Starts the development server
- `python manage.py migrate`: Applies database migrations
- `python manage.py makemigrations`: Creates new migrations
- `python manage.py collectstatic`: Collects static files for production
- `python manage.py createsuperuser`: Creates an admin user
- `python manage.py shell`: Opens Django interactive shell

## 📊 Admin Interface

Access the Django admin interface at [http://localhost:8000/admin/](http://localhost:8000/admin/) to manage:

- **Personal Information**: Bio, skills, and personal details via flexible key-value system
- **Social Links**: Platform links with validation and visibility controls
- **Blog Posts**: Create and manage blog articles with search and categorization
- **Tools**: Curate a showcase of development tools and resources
- **Contact Messages**: View and manage contact form submissions

## 🏗️ Application Structure

This Django project consists of four main apps:

### 📝 Main App (`main/`)
- **PersonalInfo Model**: Flexible key-value system for storing personal information
- **SocialLink Model**: Social media and contact links with platform validation
- **Custom User Model**: Enhanced authentication system
- **Context Processors**: Global data for templates

### 📚 Blog App (`blog/`)
- **Post Model**: Blog articles with slug-based URLs and search functionality
- **Admin Interface**: Rich content management for blog posts
- **Views**: List and detail views with search and filtering

### 🔧 Tools App (`tools/`)
- **Tool Model**: Development tools and resources showcase
- **Visibility Controls**: Show/hide tools from public display
- **Category Filtering**: Organize tools by category and favorites

### 📞 Contact App (`contact/`)
- **ContactMessage Model**: Store contact form submissions
- **Rate Limiting**: IP-based protection against spam (5 requests/minute)
- **Email Integration**: Optional email notifications for new messages

## 🔒 Security Features

- **Rate Limiting**: Contact form protected with cache-based rate limiting
- **Honeypot Protection**: Hidden field to prevent automated spam
- **CSRF Protection**: Built-in Django CSRF protection
- **Input Validation**: Server-side validation for all forms
- **Custom Admin URL**: Configurable admin path via ADMIN_URL setting
- **Secure Headers**: XSS and content type sniffing protection

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some feature'`).
5. Push to the branch (`git push origin feature/your-feature`).
6. Open a pull request.

## 🚀 Production Deployment

### Environment Configuration

For production deployment, configure these environment variables:

```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ADMIN_URL=secure-admin-path/
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Production Checklist

1. **Database Migration**: `python manage.py migrate`
2. **Static Files**: `python manage.py collectstatic`
3. **Create Superuser**: `python manage.py createsuperuser`
4. **Web Server**: Use Gunicorn with reverse proxy (Nginx)
   ```bash
   gunicorn portfolio_site.wsgi:application
   ```

## 📁 Project Structure

```
portfolio_site/
├── portfolio_site/          # Django project settings
│   ├── settings.py         # Main settings with environment support
│   ├── urls.py             # URL configuration with custom admin URL
│   └── wsgi.py             # WSGI configuration for deployment
├── main/                    # Main app (personal info, social links)
│   ├── models.py           # PersonalInfo and SocialLink models
│   ├── views.py            # Home page view with caching
│   ├── admin.py            # Admin interface configuration
│   └── context_processors.py # Global template context
├── blog/                    # Blog application
│   ├── models.py           # Post model with search functionality
│   ├── views.py            # List and detail views with filtering
│   └── admin.py            # Blog admin interface
├── tools/                   # Tools showcase application
│   ├── models.py           # Tool model with visibility controls
│   ├── views.py            # Tools listing with search and categories
│   └── admin.py            # Tools admin interface
├── contact/                 # Contact form application
│   ├── models.py           # ContactMessage model
│   ├── views.py            # Form handling with rate limiting
│   └── admin.py            # Contact messages admin
├── templates/               # Django templates
│   ├── base.html           # Base template with navigation and footer
│   ├── main/home.html      # Homepage with personal information
│   ├── blog/               # Blog list and detail templates
│   ├── tools/              # Tools showcase templates
│   └── contact/            # Contact form templates
└── static/                  # Static files
    ├── css/custom.css      # Custom CSS with Tailwind integration
    └── js/main.js          # JavaScript for interactions
```

## 👨‍💼 About Buğra AKIN

**Elektrik-Elektronik Mühendisliği Öğrencisi**
📍 Ankara, Türkiye | 📧 bugraakin01@gmail.com

**Uzmanlık Alanları:**
- Embedded Systems & Linux
- Artificial Intelligence & Cloud Computing
- Cybersecurity & Network Security
- Problem Solving & Data Analysis

**Eğitim:**
- Gaziantep Üniversitesi - Elektrik-Elektronik Mühendisliği
- Aktif Öğrenci (75 Kredi, 98 AKTS)

---

Built with ❤️ using Django and modern web technologies 🚀
