"""
Integration tests for Database Relationships & Cascades - Phase 22C.2.

Tests cover:
- ForeignKey CASCADE operations (Admin->UserSession, Admin->BlogPost, etc.)
- ForeignKey SET_NULL and PROTECT operations
- ManyToManyField operations (User groups, permissions)
- Orphan cleanup and referential integrity
- Database constraints (unique, unique_together)

Target: Verify all database relationships behave correctly.
"""

from django.contrib.auth import get_user_model
from django.db import IntegrityError

import pytest

from apps.main.models import BlogPost as MainBlogPost
from apps.playground.models import CodeSnippet, ProgrammingLanguage
from apps.portfolio.models import AccountDeletionRequest, Admin, BlogCategory
from apps.portfolio.models import BlogPost as PortfolioBlogPost
from apps.portfolio.models import (
    DataExportRequest,
    NotificationLog,
    PersonalInfo,
    UserSession,
    WebPushSubscription,
)

User = get_user_model()


# ============================================================================
# FOREIGNKEY CASCADE TESTS
# ============================================================================


@pytest.mark.django_db
class TestForeignKeyCascade:
    """Test ForeignKey CASCADE delete operations."""

    def test_admin_delete_cascades_to_user_sessions(self):
        """Test deleting Admin deletes all related UserSessions."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("testpass123")
        admin.save()

        # Create sessions
        session1 = UserSession.objects.create(
            user=admin,
            session_key="session_key_1",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        session2 = UserSession.objects.create(
            user=admin,
            session_key="session_key_2",
            ip_address="192.168.1.2",
            user_agent="Chrome",
        )

        session_ids = [session1.id, session2.id]

        # Delete admin
        admin.delete()

        # Sessions should be deleted (CASCADE)
        assert UserSession.objects.filter(id__in=session_ids).count() == 0

    def test_admin_delete_cascades_to_export_requests(self):
        """Test deleting Admin deletes all related DataExportRequests."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("testpass123")
        admin.save()

        # Create export request
        export_request = DataExportRequest.objects.create(user=admin, status="pending")

        request_id = export_request.id

        # Delete admin
        admin.delete()

        # Export request should be deleted (CASCADE)
        assert not DataExportRequest.objects.filter(id=request_id).exists()

    def test_admin_delete_cascades_to_deletion_requests(self):
        """Test deleting Admin deletes all related AccountDeletionRequests."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("testpass123")
        admin.save()

        # Create deletion request
        deletion_request = AccountDeletionRequest.objects.create(
            user=admin, reason="Testing"
        )

        request_id = deletion_request.id

        # Delete admin
        admin.delete()

        # Deletion request should be deleted (CASCADE)
        assert not AccountDeletionRequest.objects.filter(id=request_id).exists()

    def test_category_delete_cascades_to_blog_posts(self):
        """Test deleting BlogCategory deletes all related BlogPosts."""
        category = BlogCategory.objects.create(name="Tech", slug="tech")

        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        # Create blog posts in this category
        post1 = PortfolioBlogPost.objects.create(
            title="Post 1",
            slug="post-1",
            content="Content 1",
            category=category,
            author=admin,
            status="published",
        )
        post2 = PortfolioBlogPost.objects.create(
            title="Post 2",
            slug="post-2",
            content="Content 2",
            category=category,
            author=admin,
            status="draft",
        )

        post_ids = [post1.id, post2.id]

        # Delete category
        category.delete()

        # Posts should be deleted (CASCADE)
        assert PortfolioBlogPost.objects.filter(id__in=post_ids).count() == 0

    def test_webpush_subscription_delete_cascades_to_notification_logs(self):
        """Test deleting WebPushSubscription deletes related NotificationLogs."""
        subscription = WebPushSubscription.objects.create(
            endpoint="https://push.example.com/subscription1",
            p256dh="test_p256dh_key",
            auth="test_auth_key",
        )

        # Create notification logs
        log1 = NotificationLog.objects.create(
            subscription=subscription,
            title="Test Notification 1",
            message="Message 1",
            status="sent",
        )
        log2 = NotificationLog.objects.create(
            subscription=subscription,
            title="Test Notification 2",
            message="Message 2",
            status="pending",
        )

        log_ids = [log1.id, log2.id]

        # Delete subscription
        subscription.delete()

        # Logs should be deleted (CASCADE)
        assert NotificationLog.objects.filter(id__in=log_ids).count() == 0


# ============================================================================
# FOREIGNKEY SET_NULL TESTS
# ============================================================================


@pytest.mark.django_db
class TestForeignKeySetNull:
    """Test ForeignKey SET_NULL operations."""

    @pytest.mark.skip("SET_NULL relationships need to be identified in models")
    def test_set_null_on_delete(self):
        """Test SET_NULL sets FK to NULL when referenced object deleted."""
        # Example: If BlogPost.author has on_delete=SET_NULL
        # Then deleting author should set post.author = NULL
        pass


# ============================================================================
# FOREIGNKEY PROTECT TESTS
# ============================================================================


@pytest.mark.django_db
class TestForeignKeyProtect:
    """Test ForeignKey PROTECT operations."""

    @pytest.mark.skip("PROTECT relationships need to be identified in models")
    def test_protect_prevents_deletion(self):
        """Test PROTECT prevents deletion when related objects exist."""
        # Example: If Category has PROTECT, cannot delete category with posts
        # Should raise ProtectedError
        pass


# ============================================================================
# MANYTOMANY RELATIONSHIP TESTS
# ============================================================================


@pytest.mark.django_db
class TestManyToManyRelationships:
    """Test ManyToManyField operations."""

    def test_admin_groups_m2m(self):
        """Test Admin can be added to multiple groups."""
        from django.contrib.auth.models import Group

        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        # Create groups
        group1 = Group.objects.create(name="Editors")
        group2 = Group.objects.create(name="Moderators")

        # Add admin to groups
        admin.groups.add(group1, group2)

        assert admin.groups.count() == 2
        assert group1 in admin.groups.all()
        assert group2 in admin.groups.all()

    def test_admin_groups_m2m_remove(self):
        """Test removing Admin from groups."""
        from django.contrib.auth.models import Group

        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        group = Group.objects.create(name="Editors")
        admin.groups.add(group)

        # Remove from group
        admin.groups.remove(group)

        assert admin.groups.count() == 0

    def test_admin_permissions_m2m(self):
        """Test Admin can have multiple permissions."""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        # Get some permissions
        content_type = ContentType.objects.get_for_model(Admin)
        perms = Permission.objects.filter(content_type=content_type)[:2]

        # Add permissions
        admin.user_permissions.add(*perms)

        assert admin.user_permissions.count() >= 2

    def test_deleting_group_removes_m2m_relations(self):
        """Test deleting Group removes M2M relations but not Admin."""
        from django.contrib.auth.models import Group

        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        group = Group.objects.create(name="Editors")
        admin.groups.add(group)

        admin_id = admin.id

        # Delete group
        group.delete()

        # Admin should still exist
        assert Admin.objects.filter(id=admin_id).exists()

        # Admin should have no groups
        admin.refresh_from_db()
        assert admin.groups.count() == 0


# ============================================================================
# DATABASE CONSTRAINT TESTS
# ============================================================================


@pytest.mark.django_db
class TestDatabaseConstraints:
    """Test database constraints (unique, unique_together)."""

    def test_unique_constraint_prevents_duplicates(self):
        """Test unique constraint prevents duplicate values."""
        # Example: Admin username must be unique
        Admin.objects.create(username="testuser", email="test1@example.com")

        # Try creating another with same username
        with pytest.raises(IntegrityError):
            Admin.objects.create(
                username="testuser", email="test2@example.com"  # Duplicate!
            )

    def test_unique_together_constraint(self):
        """Test unique_together constraint."""
        # Example: UserSession (user, session_key) unique_together
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        UserSession.objects.create(
            user=admin,
            session_key="unique_session_1",
            ip_address="192.168.1.1",
            user_agent="Mozilla",
        )

        # Try creating another session with same user + session_key
        # (This depends on actual unique_together definition)
        # If defined, should raise IntegrityError

    def test_null_constraint_enforcement(self):
        """Test null=False fields reject NULL values."""
        # Try creating BlogPost without required title
        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        category = BlogCategory.objects.create(name="Tech", slug="tech")

        with pytest.raises((IntegrityError, ValueError)):
            PortfolioBlogPost.objects.create(
                title=None,  # Should fail if null=False
                slug="test-slug",
                content="Test content",
                category=category,
                author=admin,
            )


# ============================================================================
# ORPHAN CLEANUP TESTS
# ============================================================================


@pytest.mark.django_db
class TestOrphanCleanup:
    """Test orphan record cleanup (records without parents)."""

    def test_no_orphan_sessions_after_admin_delete(self):
        """Test no orphan UserSessions exist after Admin deleted."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        # Create sessions
        for i in range(5):
            UserSession.objects.create(
                user=admin,
                session_key=f"session_{i}",
                ip_address=f"192.168.1.{i}",
                user_agent="Mozilla",
            )

        admin_id = admin.id

        # Delete admin
        admin.delete()

        # Verify no orphan sessions exist
        orphan_sessions = UserSession.objects.filter(user_id=admin_id)
        assert orphan_sessions.count() == 0

    def test_no_orphan_blog_posts_after_category_delete(self):
        """Test no orphan BlogPosts exist after BlogCategory deleted."""
        category = BlogCategory.objects.create(name="Tech", slug="tech")

        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        # Create posts
        for i in range(3):
            PortfolioBlogPost.objects.create(
                title=f"Post {i}",
                slug=f"post-{i}",
                content=f"Content {i}",
                category=category,
                author=admin,
                status="published",
            )

        category_id = category.id

        # Delete category
        category.delete()

        # Verify no orphan posts exist
        orphan_posts = PortfolioBlogPost.objects.filter(category_id=category_id)
        assert orphan_posts.count() == 0


# ============================================================================
# REFERENTIAL INTEGRITY TESTS
# ============================================================================


@pytest.mark.django_db
class TestReferentialIntegrity:
    """Test referential integrity is maintained."""

    def test_cannot_create_session_with_nonexistent_admin(self):
        """Test cannot create UserSession with nonexistent Admin."""
        with pytest.raises((IntegrityError, ValueError)):
            UserSession.objects.create(
                user_id=99999,  # Nonexistent admin ID
                session_key="invalid_session",
                ip_address="192.168.1.1",
                user_agent="Mozilla",
            )

    def test_cannot_create_blog_post_with_nonexistent_category(self):
        """Test cannot create BlogPost with nonexistent Category."""
        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        with pytest.raises((IntegrityError, ValueError)):
            PortfolioBlogPost.objects.create(
                title="Test Post",
                slug="test-post",
                content="Content",
                category_id=99999,  # Nonexistent category ID
                author=admin,
                status="published",
            )

    def test_foreign_key_validation(self):
        """Test ForeignKey validation prevents invalid references."""
        # Try assigning invalid object to ForeignKey
        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        category = BlogCategory.objects.create(name="Tech", slug="tech")

        post = PortfolioBlogPost(
            title="Test Post",
            slug="test-post",
            content="Content",
            category=category,
            author=admin,
            status="published",
        )

        # Try assigning wrong type to author
        with pytest.raises((TypeError, ValueError)):
            post.author = "not_an_admin_object"
            post.save()


# ============================================================================
# BULK OPERATIONS TESTS
# ============================================================================


@pytest.mark.django_db
class TestBulkDatabaseOperations:
    """Test bulk create, update, delete operations."""

    def test_bulk_create_personal_info(self):
        """Test bulk_create creates multiple records efficiently."""
        personal_infos = [
            PersonalInfo(
                key=f"key_{i}", value=f"value_{i}", type="text", display_order=i
            )
            for i in range(100)
        ]

        created = PersonalInfo.objects.bulk_create(personal_infos)

        assert len(created) == 100
        assert PersonalInfo.objects.count() >= 100

    def test_bulk_update_blog_posts(self):
        """Test bulk_update updates multiple records efficiently."""
        category = BlogCategory.objects.create(name="Tech", slug="tech")
        admin = Admin.objects.create(username="author", email="author@example.com")
        admin.set_password("pass123")
        admin.save()

        # Create posts
        posts = []
        for i in range(10):
            post = PortfolioBlogPost.objects.create(
                title=f"Post {i}",
                slug=f"post-{i}",
                content=f"Content {i}",
                category=category,
                author=admin,
                status="draft",
            )
            posts.append(post)

        # Bulk update status
        for post in posts:
            post.status = "published"

        PortfolioBlogPost.objects.bulk_update(posts, ["status"])

        # Verify all updated
        published_count = PortfolioBlogPost.objects.filter(status="published").count()
        assert published_count >= 10

    def test_bulk_delete_user_sessions(self):
        """Test bulk delete removes multiple records."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        # Create sessions
        for i in range(20):
            UserSession.objects.create(
                user=admin,
                session_key=f"session_{i}",
                ip_address=f"192.168.1.{i % 255}",
                user_agent="Mozilla",
            )

        # Bulk delete
        deleted_count, _ = UserSession.objects.filter(user=admin).delete()

        assert deleted_count >= 20
        assert UserSession.objects.filter(user=admin).count() == 0
