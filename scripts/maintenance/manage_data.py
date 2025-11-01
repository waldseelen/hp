#!/usr/bin/env python
"""
Django data management script for populating initial data
"""
import os

import django
from django.contrib.auth.hashers import make_password

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings")
django.setup()

from blog.models import Post
from contact.models import ContactMessage
from main.models import Admin, PersonalInfo, SocialLink
from tools.models import Tool


def create_sample_data():
    print("Creating sample data...")

    # Create admin user
    admin_user, created = Admin.objects.get_or_create(
        email="admin@portfolio.com",
        defaults={
            "username": "admin",
            "name": "Portfolio Admin",
            "password": make_password(os.environ.get("ADMIN_PASSWORD", "change-me")),
            "is_staff": True,
            "is_superuser": True,
        },
    )
    if created:
        print(f"Created admin user: {admin_user.email}")
    else:
        print(f"Admin user already exists: {admin_user.email}")

    # Create personal info
    personal_info_data = [
        {
            "key": "bio",
            "value": "Full Stack Developer passionate about creating innovative solutions and exploring cybersecurity. I love building scalable applications and sharing knowledge through blog posts and tutorials.",
            "type": "text",
            "order": 1,
        },
        {
            "key": "experience",
            "value": "5+ years of experience in web development",
            "type": "text",
            "order": 2,
        },
        {
            "key": "skills",
            "value": "Python, Django, JavaScript, React, Node.js, PostgreSQL, Redis, Docker",
            "type": "text",
            "order": 3,
        },
    ]

    for data in personal_info_data:
        info, created = PersonalInfo.objects.get_or_create(
            key=data["key"], defaults=data
        )
        if created:
            print(f"Created personal info: {info.key}")

    # Create social links
    social_links_data = [
        {
            "platform": "github",
            "url": "https://github.com/username",
            "description": "My code repositories",
            "is_primary": True,
            "order": 1,
        },
        {
            "platform": "linkedin",
            "url": "https://linkedin.com/in/username",
            "description": "Professional network",
            "order": 2,
        },
        {
            "platform": "twitter",
            "url": "https://twitter.com/username",
            "description": "Tech thoughts and updates",
            "order": 3,
        },
    ]

    for data in social_links_data:
        link, created = SocialLink.objects.get_or_create(
            platform=data["platform"], defaults=data
        )
        if created:
            print(f"Created social link: {link.platform}")

    # Create sample blog posts
    blog_posts_data = [
        {
            "title": "Welcome to My Portfolio",
            "excerpt": "An introduction to my journey as a developer and what you can expect from this blog.",
            "content": """# Welcome to My Portfolio

Hello and welcome! This is my first blog post on my new Django-powered portfolio site.

## What You'll Find Here

In this blog, I'll be sharing:

- **Technical tutorials** - Step-by-step guides on various technologies
- **Project breakdowns** - Deep dives into projects I'm working on
- **Industry insights** - My thoughts on trends and best practices
- **Learning resources** - Tools and resources I find valuable

## My Background

I'm a full stack developer with over 5 years of experience building web applications. I'm passionate about:

- Clean, maintainable code
- User experience design
- Performance optimization
- Cybersecurity best practices

## Stay Connected

Feel free to reach out through the contact form or connect with me on social media. I love discussing technology and collaborating on interesting projects.

Thanks for visiting!""",
            "status": "published",
            "tags": ["introduction", "portfolio", "welcome"],
            "author": admin_user,
        },
        {
            "title": "Building Scalable Django Applications",
            "excerpt": "Best practices for structuring Django projects that can grow with your needs.",
            "content": """# Building Scalable Django Applications

Django is an excellent framework for building web applications, but as your project grows, maintaining clean architecture becomes crucial.

## Project Structure

Here's how I organize my Django projects:

```
project_root/
├── apps/
│   ├── users/
│   ├── blog/
│   └── api/
├── config/
├── static/
├── media/
└── requirements/
```

## Key Principles

1. **Separation of Concerns** - Keep business logic separate from views
2. **DRY (Don't Repeat Yourself)** - Use mixins and base classes
3. **Fat Models, Thin Views** - Put logic in models when possible
4. **Use Custom Managers** - For complex queries

## Performance Tips

- Use `select_related()` and `prefetch_related()`
- Implement caching strategically
- Optimize database queries
- Use async views for I/O-bound operations

Building scalable applications takes planning, but Django provides the tools to do it right.""",
            "status": "published",
            "tags": ["django", "python", "scalability", "best-practices"],
            "author": admin_user,
        },
    ]

    for data in blog_posts_data:
        post, created = Post.objects.get_or_create(title=data["title"], defaults=data)
        if created:
            print(f"Created blog post: {post.title}")

    # Create sample tools
    tools_data = [
        {
            "title": "VS Code",
            "description": "Powerful, lightweight code editor with excellent extensions ecosystem",
            "url": "https://code.visualstudio.com/",
            "category": "Development",
            "tags": ["editor", "ide", "microsoft"],
            "is_favorite": True,
        },
        {
            "title": "Django",
            "description": "High-level Python web framework that encourages rapid development",
            "url": "https://djangoproject.com/",
            "category": "Framework",
            "tags": ["python", "web", "backend"],
            "is_favorite": True,
        },
        {
            "title": "PostgreSQL",
            "description": "Advanced open source relational database",
            "url": "https://postgresql.org/",
            "category": "Database",
            "tags": ["database", "sql", "relational"],
            "is_favorite": True,
        },
        {
            "title": "Redis",
            "description": "In-memory data structure store for caching and session management",
            "url": "https://redis.io/",
            "category": "Database",
            "tags": ["cache", "memory", "nosql"],
            "is_favorite": False,
        },
        {
            "title": "Docker",
            "description": "Platform for developing, shipping, and running applications in containers",
            "url": "https://docker.com/",
            "category": "DevOps",
            "tags": ["containerization", "deployment"],
            "is_favorite": True,
        },
        {
            "title": "Postman",
            "description": "API development environment for testing and debugging APIs",
            "url": "https://postman.com/",
            "category": "Testing",
            "tags": ["api", "testing", "debugging"],
            "is_favorite": False,
        },
    ]

    for data in tools_data:
        tool, created = Tool.objects.get_or_create(title=data["title"], defaults=data)
        if created:
            print(f"Created tool: {tool.title}")

    print("Sample data creation completed!")


if __name__ == "__main__":
    create_sample_data()
