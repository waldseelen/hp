"""
Schema.org structured data helpers for SEO optimization
"""

import json

from django.urls import reverse
from django.utils import timezone


class StructuredData:
    """Helper class for generating Schema.org structured data"""

    @staticmethod
    def website_schema(request):
        """Generate website schema markup"""
        return {
            "@context": "https://schema.org",
            "@type": "Website",
            "name": "Portfolio - Full Stack Developer",
            "alternateName": "Developer Portfolio",
            "url": request.build_absolute_uri("/"),
            "description": "Full Stack Developer & Cybersecurity Enthusiast Portfolio showcasing projects, blog posts, and technical expertise.",
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": request.build_absolute_uri("/")
                    + "?q={search_term_string}",
                },
                "query-input": "required name=search_term_string",
            },
            "author": {
                "@type": "Person",
                "name": "Portfolio Developer",
                "jobTitle": "Full Stack Developer",
                "description": "Experienced developer specializing in Python, Django, and cybersecurity.",
            },
        }

    @staticmethod
    def person_schema(request):
        """Generate person schema for about page"""
        return {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": "Portfolio Developer",
            "jobTitle": "Full Stack Developer",
            "description": "Full Stack Developer & Cybersecurity Enthusiast passionate about creating innovative solutions.",
            "url": request.build_absolute_uri("/"),
            "sameAs": [
                "https://github.com",
                "https://linkedin.com",
                "https://twitter.com",
            ],
            "knowsAbout": [
                "Python Programming",
                "Django Framework",
                "Web Development",
                "Cybersecurity",
                "Database Design",
                "REST APIs",
                "JavaScript",
                "HTML/CSS",
            ],
            "alumniOf": {"@type": "Organization", "name": "University/School Name"},
        }

    @staticmethod
    def blog_post_schema(request, post):
        """Generate blog post schema"""
        return {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title,
            "description": post.excerpt or post.content[:160],
            "author": {"@type": "Person", "name": "Portfolio Developer"},
            "datePublished": (
                post.published_at.isoformat()
                if post.published_at
                else timezone.now().isoformat()
            ),
            "dateModified": (
                post.updated_at.isoformat()
                if post.updated_at
                else timezone.now().isoformat()
            ),
            "url": request.build_absolute_uri(reverse("blog:detail", args=[post.slug])),
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": request.build_absolute_uri(
                    reverse("blog:detail", args=[post.slug])
                ),
            },
            "publisher": {
                "@type": "Organization",
                "name": "Portfolio",
                "logo": {
                    "@type": "ImageObject",
                    "url": request.build_absolute_uri("/static/images/logo.png"),
                    "width": 600,
                    "height": 60,
                },
            },
            "image": (
                {
                    "@type": "ImageObject",
                    "url": (
                        post.featured_image.url
                        if post.featured_image
                        else request.build_absolute_uri("/static/images/og-image.png")
                    ),
                    "width": 1200,
                    "height": 630,
                }
                if hasattr(post, "featured_image")
                else {
                    "@type": "ImageObject",
                    "url": request.build_absolute_uri("/static/images/og-image.png"),
                    "width": 1200,
                    "height": 630,
                }
            ),
        }

    @staticmethod
    def project_schema(request, project):
        """Generate project/software application schema"""
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": project.name,
            "description": project.description,
            "url": request.build_absolute_uri(
                reverse("main:project_detail", args=[project.slug])
            ),
            "applicationCategory": "DeveloperApplication",
            "operatingSystem": "Web Browser",
            "author": {"@type": "Person", "name": "Portfolio Developer"},
            "dateCreated": (
                project.created_at.isoformat()
                if hasattr(project, "created_at")
                else timezone.now().isoformat()
            ),
            "dateModified": (
                project.updated_at.isoformat()
                if project.updated_at
                else timezone.now().isoformat()
            ),
            "programmingLanguage": (
                project.technologies.split(",")
                if hasattr(project, "technologies") and project.technologies
                else ["Python", "Django"]
            ),
            "codeRepository": (
                project.github_url
                if hasattr(project, "github_url") and project.github_url
                else None
            ),
            "screenshot": {
                "@type": "ImageObject",
                "url": (
                    project.image.url
                    if hasattr(project, "image") and project.image
                    else request.build_absolute_uri(
                        "/static/images/project-placeholder.png"
                    )
                ),
                "width": 1200,
                "height": 630,
            },
        }

    @staticmethod
    def breadcrumb_schema(request, items):
        """Generate breadcrumb navigation schema"""
        list_items = []
        for i, item in enumerate(items, 1):
            list_items.append(
                {
                    "@type": "ListItem",
                    "position": i,
                    "name": item["name"],
                    "item": (
                        request.build_absolute_uri(item["url"])
                        if item.get("url")
                        else None
                    ),
                }
            )

        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": list_items,
        }

    @staticmethod
    def organization_schema(request):
        """Generate organization schema"""
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "Portfolio",
            "url": request.build_absolute_uri("/"),
            "logo": request.build_absolute_uri("/static/images/logo.png"),
            "description": "Portfolio website of a Full Stack Developer & Cybersecurity Enthusiast.",
            "founder": {"@type": "Person", "name": "Portfolio Developer"},
            "foundingDate": "2024",
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Customer Service",
                "url": request.build_absolute_uri(reverse("contact:form")),
            },
        }

    @staticmethod
    def faq_schema(faqs):
        """Generate FAQ schema for pages with questions/answers"""
        main_entity = []
        for faq in faqs:
            main_entity.append(
                {
                    "@type": "Question",
                    "name": faq["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]},
                }
            )

        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": main_entity,
        }


def render_structured_data(data):
    """Render structured data as JSON-LD script tag"""
    if not data:
        return ""

    json_data = json.dumps(data, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">{json_data}</script>'
