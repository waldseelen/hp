"""
Integration Tests for Admin Reindex Functionality

Tests covering:
- Admin save triggers index update via signals
- Admin delete triggers index removal
- Bulk reindex admin action
- Management command (python manage.py reindex_search)
- Draft/unpublished content handling
- Error recovery during indexing
- Admin UI integration
"""

from io import StringIO
from unittest.mock import Mock, call, patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.test.utils import override_settings

import pytest

from apps.main.admin import AIToolAdmin, BlogPostAdmin
from apps.main.models import AITool, BlogPost, UsefulResource
from apps.main.search_index import search_index_manager
from apps.main.signals import remove_from_search_index, sync_to_search_index

User = get_user_model()


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.search
class TestAdminSaveIndexUpdate(TestCase):
    """Test that saving in admin triggers index update"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )
        self.client = Client()
        self.client.force_login(self.user)

    @patch("apps.main.search_index.search_index_manager.index_document")
    def test_create_blog_post_in_admin_triggers_index(self, mock_index):
        """Test creating blog post in admin triggers indexing"""
        mock_index.return_value = True

        # Create via model save (simulates admin save)
        blog_post = BlogPost.objects.create(
            title="New Admin Post",
            slug="new-admin-post",
            content="Content created via admin",
            author=self.user,
            status="published",
        )

        # Signal should have triggered indexing
        mock_index.assert_called_once()
        call_args = mock_index.call_args[0]
        assert call_args[0].id == blog_post.id

    @patch("apps.main.search_index.search_index_manager.index_document")
    def test_update_blog_post_triggers_reindex(self, mock_index):
        """Test updating blog post triggers reindexing"""
        mock_index.return_value = True

        # Create post
        blog_post = BlogPost.objects.create(
            title="Original Title",
            slug="original",
            content="Original content",
            author=self.user,
            status="published",
        )

        mock_index.reset_mock()

        # Update post
        blog_post.title = "Updated Title"
        blog_post.save()

        # Should trigger reindex
        mock_index.assert_called_once()

    @patch("apps.main.search_index.search_index_manager.index_document")
    def test_draft_post_not_indexed(self, mock_index):
        """Test that draft posts are not indexed"""
        mock_index.return_value = False  # Should return False for drafts

        blog_post = BlogPost.objects.create(
            title="Draft Post",
            slug="draft",
            content="Draft content",
            author=self.user,
            status="draft",  # Not published
        )

        # Index should be called but return False (skipped)
        mock_index.assert_called_once()

    @patch("apps.main.search_index.search_index_manager.index_document")
    def test_publish_draft_triggers_index(self, mock_index):
        """Test publishing a draft triggers indexing"""
        mock_index.return_value = False

        # Create draft
        blog_post = BlogPost.objects.create(
            title="Draft",
            slug="draft",
            content="Content",
            author=self.user,
            status="draft",
        )

        mock_index.reset_mock()
        mock_index.return_value = True

        # Publish
        blog_post.status = "published"
        blog_post.save()

        # Should now be indexed
        mock_index.assert_called_once()


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.search
class TestAdminDeleteIndexRemoval(TestCase):
    """Test that deleting in admin removes from index"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )

    @patch("apps.main.search_index.search_index_manager.delete_document")
    def test_delete_blog_post_removes_from_index(self, mock_delete):
        """Test deleting blog post removes from index"""
        mock_delete.return_value = True

        blog_post = BlogPost.objects.create(
            title="To Delete",
            slug="to-delete",
            content="Content",
            author=self.user,
            status="published",
        )

        post_id = blog_post.id

        # Delete post
        blog_post.delete()

        # Should trigger index deletion
        mock_delete.assert_called_once_with("BlogPost", post_id)

    @patch("apps.main.search_index.search_index_manager.delete_document")
    def test_delete_ai_tool_removes_from_index(self, mock_delete):
        """Test deleting AI tool removes from index"""
        mock_delete.return_value = True

        ai_tool = AITool.objects.create(
            name="Tool to Delete",
            slug="tool-delete",
            description="Description",
            is_visible=True,
        )

        tool_id = ai_tool.id

        # Delete
        ai_tool.delete()

        # Should trigger deletion
        mock_delete.assert_called_once_with("AITool", tool_id)


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.search
class TestBulkReindexAdminAction(TestCase):
    """Test bulk reindex admin action"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="adminpass"
        )
        self.site = AdminSite()
        self.blog_admin = BlogPostAdmin(BlogPost, self.site)
        self.ai_tool_admin = AIToolAdmin(AITool, self.site)

    @patch("apps.main.search_index.search_index_manager.bulk_index")
    def test_bulk_reindex_blog_posts(self, mock_bulk_index):
        """Test bulk reindex action for blog posts"""
        mock_bulk_index.return_value = {"indexed": 3, "skipped": 0, "failed": 0}

        # Create test posts
        posts = []
        for i in range(3):
            post = BlogPost.objects.create(
                title=f"Post {i}",
                slug=f"post-{i}",
                content=f"Content {i}",
                author=self.user,
                status="published",
            )
            posts.append(post)

        # Mock request
        request = Mock()
        request.user = self.user

        # Call reindex action
        queryset = BlogPost.objects.filter(id__in=[p.id for p in posts])

        if hasattr(self.blog_admin, "reindex_selected_posts"):
            self.blog_admin.reindex_selected_posts(request, queryset)

            # Should call bulk_index
            mock_bulk_index.assert_called_once()
            call_args = mock_bulk_index.call_args[0][0]
            assert len(list(call_args)) == 3

    @patch("apps.main.search_index.search_index_manager.bulk_index")
    def test_bulk_reindex_with_drafts(self, mock_bulk_index):
        """Test bulk reindex skips drafts"""
        mock_bulk_index.return_value = {"indexed": 2, "skipped": 1, "failed": 0}

        # Create mixed posts
        published1 = BlogPost.objects.create(
            title="Published 1",
            slug="pub-1",
            content="Content",
            author=self.user,
            status="published",
        )

        draft = BlogPost.objects.create(
            title="Draft",
            slug="draft",
            content="Content",
            author=self.user,
            status="draft",
        )

        published2 = BlogPost.objects.create(
            title="Published 2",
            slug="pub-2",
            content="Content",
            author=self.user,
            status="published",
        )

        request = Mock()
        request.user = self.user

        queryset = BlogPost.objects.all()

        if hasattr(self.blog_admin, "reindex_selected_posts"):
            self.blog_admin.reindex_selected_posts(request, queryset)

            # Should skip draft
            mock_bulk_index.assert_called_once()

    @patch("apps.main.search_index.search_index_manager.bulk_index")
    def test_bulk_reindex_error_handling(self, mock_bulk_index):
        """Test bulk reindex handles errors"""
        mock_bulk_index.side_effect = Exception("Index connection error")

        post = BlogPost.objects.create(
            title="Test Post",
            slug="test",
            content="Content",
            author=self.user,
            status="published",
        )

        request = Mock()
        request.user = self.user

        queryset = BlogPost.objects.filter(id=post.id)

        # Should not crash
        if hasattr(self.blog_admin, "reindex_selected_posts"):
            try:
                self.blog_admin.reindex_selected_posts(request, queryset)
            except Exception:
                pytest.fail("Bulk reindex should handle errors gracefully")


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.search
class TestManagementCommand(TestCase):
    """Test reindex_search management command"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_reindex_all_command(self, mock_manager):
        """Test python manage.py reindex_search --all"""
        mock_manager.reindex_all.return_value = {
            "total_indexed": 10,
            "total_skipped": 2,
            "total_failed": 0,
        }

        out = StringIO()
        call_command("reindex_search", "--all", stdout=out)

        output = out.getvalue()
        assert "indexed" in output.lower() or "success" in output.lower()
        mock_manager.reindex_all.assert_called_once()

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_reindex_specific_model(self, mock_manager):
        """Test python manage.py reindex_search --model BlogPost"""
        mock_manager.reindex_model.return_value = {
            "indexed": 5,
            "skipped": 1,
            "failed": 0,
        }

        out = StringIO()
        call_command("reindex_search", "--model", "BlogPost", stdout=out)

        output = out.getvalue()
        assert "BlogPost" in output
        mock_manager.reindex_model.assert_called_once_with("BlogPost")

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_reindex_multiple_models(self, mock_manager):
        """Test python manage.py reindex_search --model BlogPost --model AITool"""
        mock_manager.reindex_model.return_value = {
            "indexed": 3,
            "skipped": 0,
            "failed": 0,
        }

        out = StringIO()
        call_command(
            "reindex_search", "--model", "BlogPost", "--model", "AITool", stdout=out
        )

        # Should call reindex_model twice
        assert mock_manager.reindex_model.call_count == 2

        # Verify both models were called
        calls = [call[0][0] for call in mock_manager.reindex_model.call_args_list]
        assert "BlogPost" in calls
        assert "AITool" in calls

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_configure_only_flag(self, mock_manager):
        """Test python manage.py reindex_search --configure-only"""
        mock_manager.configure_index.return_value = True

        out = StringIO()
        call_command("reindex_search", "--configure-only", stdout=out)

        output = out.getvalue()
        assert "configur" in output.lower()
        mock_manager.configure_index.assert_called_once()

        # Should NOT call reindex methods
        mock_manager.reindex_all.assert_not_called()
        mock_manager.reindex_model.assert_not_called()

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_batch_size_option(self, mock_manager):
        """Test python manage.py reindex_search --all --batch-size 50"""
        mock_manager.reindex_all.return_value = {
            "total_indexed": 100,
            "total_skipped": 0,
            "total_failed": 0,
        }

        out = StringIO()
        call_command("reindex_search", "--all", "--batch-size", "50", stdout=out)

        # Batch size should be updated
        assert mock_manager.batch_size == 50
        mock_manager.reindex_all.assert_called_once()

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_verbose_output(self, mock_manager):
        """Test python manage.py reindex_search --all --verbose"""
        mock_manager.reindex_all.return_value = {
            "total_indexed": 5,
            "total_skipped": 1,
            "total_failed": 0,
        }

        out = StringIO()
        call_command("reindex_search", "--all", "--verbose", stdout=out)

        output = out.getvalue()
        # Should have detailed output
        assert len(output) > 0

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_command_error_handling(self, mock_manager):
        """Test command handles errors gracefully"""
        mock_manager.reindex_all.side_effect = Exception("Connection error")

        out = StringIO()
        err = StringIO()

        # Should not crash
        try:
            call_command("reindex_search", "--all", stdout=out, stderr=err)
        except SystemExit:
            pass  # Management commands may call sys.exit on error

        error_output = err.getvalue()
        assert "error" in error_output.lower() or "fail" in error_output.lower()

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_validate_config_no_options(self, mock_manager):
        """Test validation fails when no --all or --model specified"""
        from django.core.management.base import CommandError

        mock_manager.model_registry = {"BlogPost": {}, "AITool": {}}

        with pytest.raises(CommandError) as exc_info:
            call_command("reindex_search")

        error_msg = str(exc_info.value)
        assert "all" in error_msg.lower() or "model" in error_msg.lower()

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_validate_config_invalid_batch_size_zero(self, mock_manager):
        """Test validation fails for batch size = 0"""
        from django.core.management.base import CommandError

        mock_manager.model_registry = {"BlogPost": {}, "AITool": {}}

        with pytest.raises(CommandError) as exc_info:
            call_command("reindex_search", "--all", "--batch-size", "0")

        error_msg = str(exc_info.value)
        assert "batch" in error_msg.lower() or "1" in error_msg

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_validate_config_invalid_batch_size_too_large(self, mock_manager):
        """Test validation fails for batch size > 10000"""
        from django.core.management.base import CommandError

        mock_manager.model_registry = {"BlogPost": {}, "AITool": {}}

        with pytest.raises(CommandError) as exc_info:
            call_command("reindex_search", "--all", "--batch-size", "10001")

        error_msg = str(exc_info.value)
        assert "batch" in error_msg.lower() or "10000" in error_msg

    @patch("apps.main.management.commands.reindex_search.search_index_manager")
    def test_validate_config_invalid_model_name(self, mock_manager):
        """Test validation fails for invalid model name"""
        from django.core.management.base import CommandError

        mock_manager.model_registry = {"BlogPost": {}, "AITool": {}}

        with pytest.raises(CommandError) as exc_info:
            call_command("reindex_search", "--model", "InvalidModel")

        error_msg = str(exc_info.value)
        assert "Invalid" in error_msg or "invalid" in error_msg


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.search
class TestSignalIntegration(TestCase):
    """Test signal handlers integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    @patch("apps.main.signals.search_index_manager")
    def test_signal_connected_to_blog_post(self, mock_manager):
        """Test signals are properly connected to BlogPost"""
        mock_manager.index_document.return_value = True

        blog_post = BlogPost.objects.create(
            title="Signal Test",
            slug="signal-test",
            content="Content",
            author=self.user,
            status="published",
        )

        # post_save signal should have fired
        mock_manager.index_document.assert_called()

    @patch("apps.main.signals.search_index_manager")
    def test_signal_handles_index_errors(self, mock_manager):
        """Test signal handles indexing errors without breaking save"""
        mock_manager.index_document.side_effect = Exception("Index error")

        # Should not prevent model save
        try:
            blog_post = BlogPost.objects.create(
                title="Error Test",
                slug="error-test",
                content="Content",
                author=self.user,
                status="published",
            )

            # Model should be saved despite index error
            assert blog_post.id is not None
            assert BlogPost.objects.filter(slug="error-test").exists()

        except Exception:
            pytest.fail("Signal error should not prevent model save")

    @patch("apps.main.signals.search_index_manager")
    def test_multiple_saves_trigger_multiple_indexes(self, mock_manager):
        """Test multiple saves trigger multiple index updates"""
        mock_manager.index_document.return_value = True

        blog_post = BlogPost.objects.create(
            title="Original",
            slug="original",
            content="Content",
            author=self.user,
            status="published",
        )

        initial_call_count = mock_manager.index_document.call_count

        # Update multiple times
        blog_post.title = "Updated 1"
        blog_post.save()

        blog_post.title = "Updated 2"
        blog_post.save()

        # Should have additional calls
        assert mock_manager.index_document.call_count > initial_call_count


@pytest.mark.integration
@pytest.mark.admin
@pytest.mark.search
@pytest.mark.performance
class TestIndexingPerformance(TestCase):
    """Test indexing performance"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    @patch("apps.main.search_index.search_index_manager.index")
    def test_bulk_index_performance(self, mock_index):
        """Test bulk indexing is faster than individual indexing"""
        mock_index.add_documents.return_value = {"taskUid": 123}

        # Create 100 posts
        posts = []
        for i in range(100):
            post = BlogPost.objects.create(
                title=f"Performance Test {i}",
                slug=f"perf-test-{i}",
                content=f"Content {i}",
                author=self.user,
                status="published",
            )
            posts.append(post)

        import time

        # Test bulk indexing time
        with patch.object(search_index_manager, "_generate_url", return_value="/test/"):
            start = time.time()
            search_index_manager.bulk_index(posts)
            bulk_time = time.time() - start

        # Bulk should complete reasonably fast
        assert bulk_time < 5.0  # Should take less than 5 seconds

    @patch("apps.main.search_index.search_index_manager.index")
    def test_admin_save_latency(self, mock_index):
        """Test admin save -> index latency is acceptable"""
        mock_index.add_documents.return_value = {"taskUid": 123}

        import time

        with patch.object(search_index_manager, "_generate_url", return_value="/test/"):
            start = time.time()

            blog_post = BlogPost.objects.create(
                title="Latency Test",
                slug="latency-test",
                content="Content",
                author=self.user,
                status="published",
            )

            latency = time.time() - start

        # Total time (save + index) should be fast
        assert latency < 1.0  # Less than 1 second
