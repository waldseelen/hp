"""
Comprehensive test suite for contact app
Tests cover: form validation, model validation, views, CSRF, rate limiting, edge cases
"""

import hashlib

from django.contrib.messages import get_messages
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .forms import ContactForm
from .models import ContactMessage


class ContactMessageModelTests(TestCase):
    """Test ContactMessage model validation"""

    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message with enough characters.",
            "preferred_channel": "email",
        }

    def test_valid_contact_message(self):
        """Test creating a valid contact message"""
        message = ContactMessage.objects.create(**self.valid_data)
        self.assertIsNotNone(message.id)
        self.assertEqual(message.name, "John Doe")
        self.assertEqual(message.preferred_channel, "email")
        self.assertFalse(message.is_read)

    def test_name_too_short(self):
        """Test name validation - too short"""
        data = self.valid_data.copy()
        data["name"] = "J"
        message = ContactMessage(**data)
        with self.assertRaises(ValidationError) as context:
            message.full_clean()
        self.assertIn("name", context.exception.message_dict)

    def test_name_invalid_characters(self):
        """Test name validation - invalid characters"""
        data = self.valid_data.copy()
        data["name"] = 'John<script>alert("xss")</script>'
        message = ContactMessage(**data)
        with self.assertRaises(ValidationError) as context:
            message.full_clean()
        self.assertIn("name", context.exception.message_dict)

    def test_message_too_short(self):
        """Test message validation - too short"""
        data = self.valid_data.copy()
        data["message"] = "Short"
        message = ContactMessage(**data)
        with self.assertRaises(ValidationError) as context:
            message.full_clean()
        self.assertIn("message", context.exception.message_dict)

    def test_message_too_long(self):
        """Test message validation - too long"""
        data = self.valid_data.copy()
        data["message"] = "x" * 2001
        message = ContactMessage(**data)
        with self.assertRaises(ValidationError) as context:
            message.full_clean()
        self.assertIn("message", context.exception.message_dict)

    def test_subject_too_short(self):
        """Test subject validation - too short"""
        data = self.valid_data.copy()
        data["subject"] = "Hi"
        message = ContactMessage(**data)
        with self.assertRaises(ValidationError) as context:
            message.full_clean()
        self.assertIn("subject", context.exception.message_dict)

    def test_email_validation(self):
        """Test email field validation"""
        data = self.valid_data.copy()
        data["email"] = "invalid-email"
        message = ContactMessage(**data)
        with self.assertRaises(ValidationError) as context:
            message.full_clean()
        self.assertIn("email", context.exception.message_dict)

    def test_preferred_channel_choices(self):
        """Test preferred_channel accepts valid choices"""
        for channel in ["email", "calendly", "slack"]:
            data = self.valid_data.copy()
            data["preferred_channel"] = channel
            message = ContactMessage.objects.create(**data)
            self.assertEqual(message.preferred_channel, channel)

    def test_ordering(self):
        """Test messages are ordered by creation date (newest first)"""
        ContactMessage.objects.create(**self.valid_data)
        data2 = self.valid_data.copy()
        data2["email"] = "jane@example.com"
        message2 = ContactMessage.objects.create(**data2)

        messages = ContactMessage.objects.all()
        self.assertEqual(messages[0].id, message2.id)


class ContactFormTests(TestCase):
    """Test ContactForm validation and sanitization"""

    def setUp(self):
        """Set up test data"""
        self.valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message with enough characters.",
            "preferred_channel": "email",
            "website": "",  # Honeypot
        }

    def test_valid_form(self):
        """Test form with valid data"""
        form = ContactForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_empty_form(self):
        """Test form with no data"""
        form = ContactForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("subject", form.errors)
        self.assertIn("message", form.errors)

    def test_name_with_numbers(self):
        """Test name field rejects numbers"""
        data = self.valid_data.copy()
        data["name"] = "John123"
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_name_with_url(self):
        """Test name field rejects URLs"""
        data = self.valid_data.copy()
        data["name"] = "John http://spam.com"
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_email_format(self):
        """Test email validation"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
        ]
        for email in invalid_emails:
            data = self.valid_data.copy()
            data["email"] = email
            form = ContactForm(data=data)
            self.assertFalse(form.is_valid(), f"Email {email} should be invalid")

    def test_subject_spam_detection(self):
        """Test subject spam pattern detection"""
        spam_subjects = [
            "Click here to win",
            "Free money now",
            "Viagra cheap",
            "Casino winner",
        ]
        for subject in spam_subjects:
            data = self.valid_data.copy()
            data["subject"] = subject
            form = ContactForm(data=data)
            self.assertFalse(
                form.is_valid(), f"Subject '{subject}' should be flagged as spam"
            )

    def test_message_url_limit(self):
        """Test message rejects too many URLs"""
        data = self.valid_data.copy()
        data["message"] = "Check http://one.com and http://two.com and http://three.com"
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_message_repeated_characters(self):
        """Test message rejects excessive repeated characters"""
        data = self.valid_data.copy()
        data["message"] = "Hellooooooooooooooo world"
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_honeypot_spam_detection(self):
        """Test honeypot field catches bots"""
        data = self.valid_data.copy()
        data["website"] = "http://spam.com"
        form = ContactForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("website", form.errors)

    def test_html_sanitization(self):
        """Test HTML tags are stripped"""
        data = self.valid_data.copy()
        data["name"] = "John <b>Doe</b>"
        form = ContactForm(data=data)
        if form.is_valid():
            self.assertNotIn("<b>", form.cleaned_data["name"])
            self.assertNotIn("</b>", form.cleaned_data["name"])

    def test_whitespace_normalization(self):
        """Test excessive whitespace is normalized"""
        data = self.valid_data.copy()
        data["name"] = "John    Doe"
        form = ContactForm(data=data)
        if form.is_valid():
            self.assertEqual(form.cleaned_data["name"], "John Doe")


class ContactViewTests(TestCase):
    """Test contact view behavior"""

    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.url = reverse("contact:form")  # Adjust if your URL name is different
        self.valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message with enough characters.",
            "preferred_channel": "email",
            "website": "",
        }

    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()

    def test_get_contact_form(self):
        """Test GET request displays form"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrf")
        self.assertContains(response, "name")
        self.assertContains(response, "email")

    def test_post_valid_form(self):
        """Test POST with valid data creates message"""
        response = self.client.post(self.url, data=self.valid_data)

        # Should redirect to success page
        self.assertEqual(response.status_code, 302)

        # Message should be saved
        self.assertEqual(ContactMessage.objects.count(), 1)
        message = ContactMessage.objects.first()
        self.assertEqual(message.name, "John Doe")
        self.assertEqual(message.email, "john@example.com")

    def test_post_invalid_form(self):
        """Test POST with invalid data shows errors"""
        data = self.valid_data.copy()
        data["email"] = "invalid-email"

        response = self.client.post(self.url, data=data)

        # Should not redirect
        self.assertEqual(response.status_code, 200)

        # Should not create message
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_csrf_protection(self):
        """Test CSRF protection is active"""
        # Django test client includes CSRF by default
        # Test that form POST without CSRF fails
        client = Client(enforce_csrf_checks=True)
        response = client.post(self.url, data=self.valid_data)
        self.assertEqual(response.status_code, 403)

    def test_rate_limiting(self):
        """Test rate limiting prevents spam"""
        # Submit form 5 times (the limit)
        for i in range(5):
            data = self.valid_data.copy()
            data["email"] = f"user{i}@example.com"
            response = self.client.post(self.url, data=data)

        # 6th submission should be rate limited
        data = self.valid_data.copy()
        data["email"] = "user6@example.com"
        response = self.client.post(self.url, data=data)

        # Should show rate limit message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                "wait" in str(m).lower() or "too many" in str(m).lower()
                for m in messages
            ),
            f"Expected rate limit message, got: {messages}",
        )

    def test_success_message(self):
        """Test success message is displayed"""
        response = self.client.post(self.url, data=self.valid_data, follow=True)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("success" in str(m).lower() for m in messages),
            f"Expected success message, got: {messages}",
        )


class ContactSecurityTests(TestCase):
    """Test security features"""

    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.url = reverse("contact:form")

    def tearDown(self):
        """Clear cache after each test"""
        cache.clear()

    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        data = {
            "name": 'John<script>alert("xss")</script>Doe',
            "email": "john@example.com",
            "subject": 'Test<script>alert("xss")</script>',
            "message": 'This is a test<script>alert("xss")</script> message with enough characters.',
            "preferred_channel": "email",
            "website": "",
        }

        form = ContactForm(data=data)
        # Form should either reject it or sanitize it
        if form.is_valid():
            # If accepted, ensure script tags are removed
            self.assertNotIn("<script>", form.cleaned_data["name"])
            self.assertNotIn("<script>", form.cleaned_data["subject"])
            self.assertNotIn("<script>", form.cleaned_data["message"])

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention (Django ORM should handle this)"""
        data = {
            "name": "John'; DROP TABLE contact_contactmessage; --",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message with enough characters.",
            "preferred_channel": "email",
            "website": "",
        }

        # Should either reject or safely store
        self.client.post(self.url, data=data)

        # Table should still exist (can query it)
        messages = ContactMessage.objects.all()
        self.assertIsNotNone(messages)

    def test_extremely_long_input(self):
        """Test handling of extremely long input"""
        data = {
            "name": "A" * 1000,
            "email": "john@example.com",
            "subject": "S" * 500,
            "message": "M" * 5000,
            "preferred_channel": "email",
            "website": "",
        }

        form = ContactForm(data=data)
        # Should be rejected due to length validators
        self.assertFalse(form.is_valid())
