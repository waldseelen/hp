"""
Migration to add database indexes for blog app query optimization
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0010_remove_post_blog_status_created_and_more"),
    ]

    operations = [
        # Post indexes - enhanced for better query performance
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["slug"], name="idx_blog_post_slug"),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["status", "-published_at", "-created_at"], name="idx_blog_post_status_dates"),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["author", "status"], name="idx_blog_post_author_status"),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["-view_count"], name="idx_blog_post_views"),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["-created_at"], name="idx_blog_post_created"),
        ),
        migrations.AddIndex(
            model_name="post",
            index=models.Index(fields=["-updated_at"], name="idx_blog_post_updated"),
        ),
    ]
