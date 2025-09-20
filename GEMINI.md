## Project Overview

This is a professional portfolio website built with Django and styled with Tailwind CSS. It features a clean, responsive design optimized for performance and SEO. The project includes a blog, a curated collection of tools and resources, a contact system with live chat, and a comprehensive admin dashboard.

**Main Technologies:**

*   **Backend:** Django, Python, Django REST Framework, Celery, Redis
*   **Frontend:** Tailwind CSS, Alpine.js
*   **Database:** SQLite (development), PostgreSQL (production)
*   **Deployment:** Railway, Docker

## Building and Running

**Prerequisites:**

*   Python 3.11+
*   Node.js
*   Git

**Installation and-Running:**

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd portfolio-site
    ```

2.  **Set up Python environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

4.  **Set up environment variables:**
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

5.  **Run database migrations:**
    ```bash
    python manage.py migrate
    ```

6.  **Create a superuser:**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Build frontend assets:**
    ```bash
    npm run build:css
    ```

8.  **Start the development server:**
    ```bash
    python manage.py runserver
    ```

**Testing:**

*   Run backend tests:
    ```bash
    pytest
    ```
*   Run frontend tests:
    ```bash
    npm test
    ```

## Development Conventions

*   **Coding Style:** The project follows the PEP 8 style guide for Python code.
*   **Testing:** The project uses pytest for backend testing and Jest for frontend testing.
*   **Branching:** The project uses a feature-branch workflow.
*   **Commits:** Commit messages should be clear and concise.
