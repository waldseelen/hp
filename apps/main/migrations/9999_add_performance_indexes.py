"""
Migration to add database indexes for main app query optimization
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("main", "0012_alter_admin_groups_alter_admin_user_permissions_and_more"),
    ]

    operations = [
        # Admin model indexes
        migrations.AddIndex(
            model_name="admin",
            index=models.Index(fields=["email"], name="idx_main_admin_email"),
        ),
        migrations.AddIndex(
            model_name="admin",
            index=models.Index(fields=["is_active"], name="idx_main_admin_active"),
        ),

        # PersonalInfo indexes
        migrations.AddIndex(
            model_name="personalinfo",
            index=models.Index(fields=["key"], name="idx_personal_key"),
        ),
        migrations.AddIndex(
            model_name="personalinfo",
            index=models.Index(fields=["is_visible", "order"], name="idx_personal_visible_order"),
        ),

        # SocialLink indexes
        migrations.AddIndex(
            model_name="sociallink",
            index=models.Index(fields=["platform", "is_visible"], name="idx_social_platform_visible"),
        ),
        migrations.AddIndex(
            model_name="sociallink",
            index=models.Index(fields=["is_primary"], name="idx_social_primary"),
        ),
        migrations.AddIndex(
            model_name="sociallink",
            index=models.Index(fields=["order"], name="idx_social_order"),
        ),

        # AITool indexes
        migrations.AddIndex(
            model_name="aitool",
            index=models.Index(fields=["category", "is_visible"], name="idx_aitool_category_visible"),
        ),
        migrations.AddIndex(
            model_name="aitool",
            index=models.Index(fields=["is_featured"], name="idx_aitool_featured"),
        ),
        migrations.AddIndex(
            model_name="aitool",
            index=models.Index(fields=["order"], name="idx_aitool_order"),
        ),

        # CybersecurityResource indexes
        migrations.AddIndex(
            model_name="cybersecurityresource",
            index=models.Index(fields=["type", "is_visible"], name="idx_cyber_type_visible"),
        ),
        migrations.AddIndex(
            model_name="cybersecurityresource",
            index=models.Index(fields=["is_featured"], name="idx_cyber_featured"),
        ),
        migrations.AddIndex(
            model_name="cybersecurityresource",
            index=models.Index(fields=["-is_urgent", "-severity_level"], name="idx_cyber_urgency"),
        ),

        # BlogCategory indexes
        migrations.AddIndex(
            model_name="blogcategory",
            index=models.Index(fields=["is_visible", "order"], name="idx_blogcat_visible_order"),
        ),
    ]
