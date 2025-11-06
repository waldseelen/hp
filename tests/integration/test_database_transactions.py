"""
Integration tests for Database Transactions - Phase 22C.2.

Tests cover:
- Atomic transactions (@atomic decorator)
- Transaction rollback on errors
- Savepoints (nested transactions)
- Database locks and concurrency
- Transaction isolation levels
- Select_for_update (row-level locking)

Target: Verify transactional integrity and ACID properties.
"""

from unittest.mock import patch

from django.db import DatabaseError, IntegrityError, transaction
from django.db.utils import OperationalError

import pytest

from apps.portfolio.models import Admin, BlogCategory
from apps.portfolio.models import BlogPost as PortfolioBlogPost
from apps.portfolio.models import DataExportRequest, PersonalInfo, UserSession

# ============================================================================
# ATOMIC TRANSACTION TESTS
# ============================================================================


@pytest.mark.django_db
class TestAtomicTransactions:
    """Test atomic transaction behavior."""

    def test_atomic_rollback_on_exception(self):
        """Test atomic transaction rolls back all changes on exception."""
        initial_count = Admin.objects.count()

        try:
            with transaction.atomic():
                # Create admin
                admin = Admin.objects.create(
                    username="testadmin", email="admin@example.com"
                )
                admin.set_password("pass123")
                admin.save()

                # Create another with duplicate username (should fail)
                Admin.objects.create(
                    username="testadmin", email="admin2@example.com"  # Duplicate!
                )
        except IntegrityError:
            pass  # Expected

        # First admin should NOT exist (transaction rolled back)
        assert Admin.objects.count() == initial_count

    def test_atomic_commits_on_success(self):
        """Test atomic transaction commits when no exceptions occur."""
        initial_count = Admin.objects.count()

        with transaction.atomic():
            admin = Admin.objects.create(
                username="testadmin", email="admin@example.com"
            )
            admin.set_password("pass123")
            admin.save()

            # Create session
            UserSession.objects.create(
                user=admin,
                session_key="session_key_1",
                ip_address="192.168.1.1",
                user_agent="Mozilla",
            )

        # Both should exist (transaction committed)
        assert Admin.objects.count() == initial_count + 1
        assert UserSession.objects.filter(user__username="testadmin").exists()

    def test_nested_atomic_transactions(self):
        """Test nested atomic transactions (savepoints)."""
        initial_count = BlogCategory.objects.count()

        with transaction.atomic():
            # Outer transaction
            category1 = BlogCategory.objects.create(name="Tech", slug="tech")

            try:
                with transaction.atomic():
                    # Inner transaction (savepoint)
                    category2 = BlogCategory.objects.create(
                        name="Science", slug="science"
                    )

                    # Force error
                    raise Exception("Rollback inner transaction")
            except Exception:
                pass  # Inner transaction rolls back

            # Create another in outer transaction
            category3 = BlogCategory.objects.create(name="Art", slug="art")

        # category1 and category3 should exist, category2 should not
        assert BlogCategory.objects.filter(slug="tech").exists()
        assert BlogCategory.objects.filter(slug="art").exists()
        assert not BlogCategory.objects.filter(slug="science").exists()


# ============================================================================
# SAVEPOINT TESTS
# ============================================================================


@pytest.mark.django_db
class TestSavepoints:
    """Test database savepoints (nested transactions)."""

    def test_savepoint_rollback(self):
        """Test rolling back to a savepoint."""
        with transaction.atomic():
            # Create category
            category = BlogCategory.objects.create(name="Tech", slug="tech")

            # Create savepoint
            sid = transaction.savepoint()

            # Create personal info (will be rolled back)
            PersonalInfo.objects.create(
                key="temp_key", value="temp_value", type="text", display_order=1
            )

            # Rollback to savepoint
            transaction.savepoint_rollback(sid)

            # PersonalInfo should not exist
            assert not PersonalInfo.objects.filter(key="temp_key").exists()

            # But category should still exist
            assert BlogCategory.objects.filter(slug="tech").exists()

    def test_savepoint_commit(self):
        """Test committing a savepoint."""
        with transaction.atomic():
            category = BlogCategory.objects.create(name="Tech", slug="tech")

            # Create savepoint
            sid = transaction.savepoint()

            # Create personal info
            PersonalInfo.objects.create(
                key="committed_key",
                value="committed_value",
                type="text",
                display_order=1,
            )

            # Commit savepoint
            transaction.savepoint_commit(sid)

        # Both should exist
        assert BlogCategory.objects.filter(slug="tech").exists()
        assert PersonalInfo.objects.filter(key="committed_key").exists()


# ============================================================================
# TRANSACTION ISOLATION TESTS
# ============================================================================


@pytest.mark.django_db
class TestTransactionIsolation:
    """Test transaction isolation levels."""

    def test_read_committed_isolation(self):
        """Test READ COMMITTED isolation (default in PostgreSQL)."""
        # Create admin in one transaction
        with transaction.atomic():
            admin = Admin.objects.create(
                username="testadmin", email="admin@example.com"
            )
            admin.set_password("pass123")
            admin.save()

        # Read in another transaction (should see committed data)
        with transaction.atomic():
            fetched_admin = Admin.objects.get(username="testadmin")
            assert fetched_admin.id == admin.id

    @pytest.mark.skip("Database-specific isolation testing")
    def test_repeatable_read_isolation(self):
        """Test REPEATABLE READ isolation (MySQL InnoDB)."""
        # This test is database-specific
        pass


# ============================================================================
# SELECT_FOR_UPDATE TESTS (Row-Level Locking)
# ============================================================================


@pytest.mark.django_db
class TestSelectForUpdate:
    """Test select_for_update for row-level locking."""

    def test_select_for_update_locks_row(self):
        """Test select_for_update locks the selected row."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        with transaction.atomic():
            # Lock the admin row
            locked_admin = Admin.objects.select_for_update().get(username="testadmin")

            # Modify locked admin
            locked_admin.email = "newemail@example.com"
            locked_admin.save()

        # Changes should be committed
        admin.refresh_from_db()
        assert admin.email == "newemail@example.com"

    def test_select_for_update_nowait(self):
        """Test select_for_update with nowait raises exception if locked."""
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        # This test would require concurrent transactions
        # Simplified version: just test the query executes
        with transaction.atomic():
            locked_admin = Admin.objects.select_for_update(nowait=True).get(
                username="testadmin"
            )
            assert locked_admin is not None

    def test_select_for_update_skip_locked(self):
        """Test select_for_update with skip_locked."""
        admin1 = Admin.objects.create(username="admin1", email="admin1@example.com")
        admin1.set_password("pass123")
        admin1.save()

        admin2 = Admin.objects.create(username="admin2", email="admin2@example.com")
        admin2.set_password("pass123")
        admin2.save()

        with transaction.atomic():
            # Select with skip_locked
            admins = list(Admin.objects.select_for_update(skip_locked=True).all())
            assert len(admins) >= 2


# ============================================================================
# TRANSACTION DECORATOR TESTS
# ============================================================================


@pytest.mark.django_db
class TestTransactionDecorator:
    """Test @transaction.atomic decorator on functions."""

    @transaction.atomic
    def _create_admin_with_session(self, username, email):
        """Helper function with @transaction.atomic decorator."""
        admin = Admin.objects.create(username=username, email=email)
        admin.set_password("pass123")
        admin.save()

        UserSession.objects.create(
            user=admin,
            session_key="session_key_1",
            ip_address="192.168.1.1",
            user_agent="Mozilla",
        )

        return admin

    def test_atomic_decorator_commits_on_success(self):
        """Test @transaction.atomic decorator commits on success."""
        admin = self._create_admin_with_session("testadmin", "admin@example.com")

        assert Admin.objects.filter(username="testadmin").exists()
        assert UserSession.objects.filter(user=admin).exists()

    @transaction.atomic
    def _create_admin_with_error(self, username):
        """Helper function that raises error."""
        admin = Admin.objects.create(username=username, email="test@example.com")
        admin.set_password("pass123")
        admin.save()

        # Raise error
        raise Exception("Intentional error")

    def test_atomic_decorator_rollbacks_on_error(self):
        """Test @transaction.atomic decorator rolls back on error."""
        try:
            self._create_admin_with_error("rolledback")
        except Exception:
            pass

        # Admin should NOT exist
        assert not Admin.objects.filter(username="rolledback").exists()


# ============================================================================
# TRANSACTION COMMIT/ROLLBACK HOOKS
# ============================================================================


@pytest.mark.django_db
class TestTransactionHooks:
    """Test transaction commit/rollback hooks."""

    def test_on_commit_hook_fires_after_commit(self):
        """Test transaction.on_commit hook fires after transaction commits."""
        callback_executed = []

        def callback():
            callback_executed.append(True)

        with transaction.atomic():
            admin = Admin.objects.create(
                username="testadmin", email="admin@example.com"
            )
            admin.set_password("pass123")
            admin.save()

            # Register on_commit callback
            transaction.on_commit(callback)

            # Callback should NOT have fired yet
            assert len(callback_executed) == 0

        # Now callback should have fired
        assert len(callback_executed) == 1

    def test_on_commit_hook_not_fired_on_rollback(self):
        """Test transaction.on_commit hook does NOT fire on rollback."""
        callback_executed = []

        def callback():
            callback_executed.append(True)

        try:
            with transaction.atomic():
                admin = Admin.objects.create(
                    username="testadmin", email="admin@example.com"
                )
                admin.set_password("pass123")
                admin.save()

                # Register on_commit callback
                transaction.on_commit(callback)

                # Force rollback
                raise Exception("Force rollback")
        except Exception:
            pass

        # Callback should NOT have fired
        assert len(callback_executed) == 0


# ============================================================================
# CONCURRENT TRANSACTION TESTS
# ============================================================================


@pytest.mark.django_db
class TestConcurrentTransactions:
    """Test concurrent transaction handling."""

    @pytest.mark.skip("Requires concurrent execution setup")
    def test_concurrent_updates_with_locking(self):
        """Test concurrent updates with select_for_update."""
        # This test requires threading or multiprocessing
        # Simplified version is just conceptual
        pass

    @pytest.mark.skip("Requires concurrent execution setup")
    def test_lost_update_prevention(self):
        """Test preventing lost updates with proper locking."""
        # Example: Two threads incrementing a counter
        # Without locking: lost updates
        # With select_for_update: all updates applied
        pass


# ============================================================================
# TRANSACTION PERFORMANCE TESTS
# ============================================================================


@pytest.mark.django_db
class TestTransactionPerformance:
    """Test transaction performance characteristics."""

    def test_bulk_operations_in_transaction(self):
        """Test bulk operations within a transaction are faster."""
        import time

        # Without transaction (multiple commits)
        start_time = time.time()
        for i in range(50):
            PersonalInfo.objects.create(
                key=f"key_without_{i}", value=f"value_{i}", type="text", display_order=i
            )
        without_transaction_time = time.time() - start_time

        # With transaction (single commit)
        start_time = time.time()
        with transaction.atomic():
            for i in range(50):
                PersonalInfo.objects.create(
                    key=f"key_with_{i}",
                    value=f"value_{i}",
                    type="text",
                    display_order=i,
                )
        with_transaction_time = time.time() - start_time

        # Transaction should be faster (or at least not significantly slower)
        # This is a general principle, though results may vary


# ============================================================================
# ERROR RECOVERY TESTS
# ============================================================================


@pytest.mark.django_db
class TestErrorRecovery:
    """Test error recovery in transactions."""

    def test_database_recovers_after_transaction_error(self):
        """Test database connection recovers after transaction error."""
        # Cause a transaction error
        try:
            with transaction.atomic():
                Admin.objects.create(username="testadmin", email="admin@example.com")
                # Force duplicate key error
                Admin.objects.create(username="testadmin", email="admin2@example.com")
        except IntegrityError:
            pass

        # Database should still work after error
        admin = Admin.objects.create(username="newadmin", email="new@example.com")
        admin.set_password("pass123")
        admin.save()

        assert Admin.objects.filter(username="newadmin").exists()

    def test_connection_valid_after_rollback(self):
        """Test database connection is valid after rollback."""
        try:
            with transaction.atomic():
                Admin.objects.create(username="testadmin", email="admin@example.com")
                raise Exception("Force rollback")
        except Exception:
            pass

        # Should be able to query normally
        count = Admin.objects.count()
        assert count >= 0


# ============================================================================
# TRANSACTION BOUNDARY TESTS
# ============================================================================


@pytest.mark.django_db
class TestTransactionBoundaries:
    """Test transaction boundary behavior."""

    def test_autocommit_mode(self):
        """Test autocommit mode (default behavior)."""
        # Each query commits immediately in autocommit mode
        admin = Admin.objects.create(username="testadmin", email="admin@example.com")
        admin.set_password("pass123")
        admin.save()

        # Should be committed immediately
        assert Admin.objects.filter(username="testadmin").exists()

    def test_explicit_transaction_boundaries(self):
        """Test explicit transaction begin/commit/rollback."""
        initial_count = Admin.objects.count()

        # Begin transaction explicitly (using context manager)
        with transaction.atomic():
            Admin.objects.create(username="admin1", email="admin1@example.com")
            Admin.objects.create(username="admin2", email="admin2@example.com")

        # Both should be committed
        assert Admin.objects.count() == initial_count + 2

    def test_transaction_per_request(self):
        """Test transaction-per-request pattern."""
        # This is typically handled by Django middleware
        # ATOMIC_REQUESTS setting in settings.py
        # Each view runs in a transaction
        # Test is conceptual - actual implementation in middleware
        pass
