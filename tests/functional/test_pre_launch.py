"""
Pre-launch functional tests.
Tests homepage, blog, contact form, and admin panel accessibility.
"""

from django.test import Client
from django.utils import timezone

import pytest

from apps.blog.models import Post
from apps.main.models import Admin

pytestmark = pytest.mark.django_db


# noqa: C901
def test_homepage_loads():
    """Test homepage loads correctly"""
    client = Client()
    response = client.get("/")
    assert response.status_code == 200


def test_blog_functional():
    """Test blog list and detail pages"""
    client = Client()

    # Create test data
    admin = Admin.objects.filter(username="testadmin").first()
    if not admin:
        admin = Admin.objects.create(username="testadmin", email="test@test.com")

    post = Post.objects.filter(status="published").first()
    if not post:
        post = Post.objects.create(
            title="Test Post",
            content="Test content",
            status="published",
            published_at=timezone.now(),
            author=admin,
        )

    # Test blog list
    response = client.get("/blog/")
    assert response.status_code == 200

    # Test blog detail
    response_detail = client.get(f"/blog/{post.slug}/")
    assert response_detail.status_code == 200


def test_contact_form_working():
    """Test contact form GET and POST"""
    client = Client()

    # Test GET
    response = client.get("/contact/")
    assert response.status_code == 200

    # Test POST with valid data
    form_data = {
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Test Subject",
        "message": "Test message with enough characters to pass validation",
    }
    response_post = client.post("/contact/", data=form_data)
    assert response_post.status_code in [200, 302]


def test_admin_panel_accessible():
    """Test admin panel is accessible"""
    client = Client()
    response = client.get("/admin/")
    assert response.status_code in [200, 302]


# Legacy combined test for backward compatibility
def test_pre_launch_checks():
    """Run all pre-launch functional tests (legacy)"""
    print("=" * 70)
    print("PRE-LAUNCH FUNCTIONAL TESTS")
    print("=" * 70)

    # Setup
    client = Client()
    results = []

    def test_result(name, passed, details=""):
        """Record test result"""
        status = "[PASS]" if passed else "[FAIL]"
        color = "✓" if passed else "✗"
        results.append((name, passed, details))
        print(f"{status} {color} {name}")
        if details:
            print(f"     Details: {details}")

    # Test 1: Homepage loads correctly
    print("\n1. Testing Homepage...")
    try:
        response = client.get("/")
        passed = response.status_code == 200
        test_result(
            "Homepage loads correctly", passed, f"Status: {response.status_code}"
        )
    except Exception as e:
        test_result("Homepage loads correctly", False, str(e))

    # Test 2: Blog page functional
    print("\n2. Testing Blog...")
    try:
        # Create test admin and post
        admin = Admin.objects.filter(username="testadmin").first()
        if not admin:
            admin = Admin.objects.create(username="testadmin", email="test@test.com")

        post = Post.objects.filter(status="published").first()
        if not post:
            post = Post.objects.create(
                title="Test Post",
                content="Test content",
                status="published",
                published_at=timezone.now(),
                author=admin,
            )

        # Test blog list
        response = client.get("/blog/")
        blog_list_ok = response.status_code == 200

        # Test blog detail
        response_detail = client.get(f"/blog/{post.slug}/")
        blog_detail_ok = response_detail.status_code == 200

        passed = blog_list_ok and blog_detail_ok
        test_result(
            "Blog page functional",
            passed,
            f"List: {response.status_code}, Detail: {response_detail.status_code}",
        )
    except Exception as e:
        test_result("Blog page functional", False, str(e))

    # Test 3: Contact form working
    print("\n3. Testing Contact Form...")
    try:
        # Test GET
        response = client.get("/contact/")
        get_ok = response.status_code == 200

        # Test POST with valid data
        form_data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message with enough characters to pass validation",
        }
        response_post = client.post("/contact/", data=form_data)
        post_ok = response_post.status_code in [200, 302]  # Success or redirect

        passed = get_ok and post_ok
        test_result(
            "Contact form working",
            passed,
            f"GET: {response.status_code}, POST: {response_post.status_code}",
        )
    except Exception as e:
        test_result("Contact form working", False, str(e))

    # Test 4: Admin panel accessible
    print("\n4. Testing Admin Panel...")
    try:
        response = client.get("/admin/")
        # Should redirect to login or show admin page
        passed = response.status_code in [200, 302]
        test_result("Admin panel accessible", passed, f"Status: {response.status_code}")
    except Exception as e:
        test_result("Admin panel accessible", False, str(e))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    total = len(results)
    passed_count = sum(1 for _, passed, _ in results if passed)
    failed_count = total - passed_count

    print(f"Total Tests: {total}")
    print(f"Passed: {passed_count} ✓")
    print(f"Failed: {failed_count} ✗")
    print(f"Success Rate: {(passed_count / total * 100):.1f}%")
    print("=" * 70)

    # Assert all passed
    assert failed_count == 0, f"{failed_count} tests failed"
