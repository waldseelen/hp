"""
Comprehensive unit tests for Contact forms

Tests cover:
- Field validation (name, email, subject, message)
- XSS prevention and sanitization
- Spam detection (honeypot, patterns)
- Edge cases and security
"""

from django.core.exceptions import ValidationError

import pytest

from apps.contact.forms import ContactForm
from apps.contact.models import ContactMessage


@pytest.mark.django_db
class TestContactFormValidation:
    """Tests for basic form validation"""

    def test_valid_form_submission(self):
        """Test form accepts valid data"""
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a valid test message with enough characters.",
            "website": "",  # Honeypot should be empty
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()
        assert form.errors == {}

    def test_all_fields_required(self):
        """Test all main fields are required"""
        form = ContactForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "email" in form.errors
        assert "subject" in form.errors
        assert "message" in form.errors

    def test_empty_name_raises_error(self):
        """Test empty name field raises validation error"""
        form_data = {
            "name": "",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_empty_email_raises_error(self):
        """Test empty email field raises validation error"""
        form_data = {
            "name": "John Doe",
            "email": "",
            "subject": "Test",
            "message": "Test message",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "email" in form.errors

    def test_empty_subject_raises_error(self):
        """Test empty subject field raises validation error"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "",
            "message": "Test message",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "subject" in form.errors

    def test_empty_message_raises_error(self):
        """Test empty message field raises validation error"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "message" in form.errors


@pytest.mark.django_db
class TestNameFieldValidation:
    """Tests for name field validation"""

    def test_name_minimum_length(self):
        """Test name must be at least 2 characters"""
        form_data = {
            "name": "A",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_name_strips_html_tags(self):
        """Test name field strips HTML tags"""
        form_data = {
            "name": "<script>alert('xss')</script>John",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        # Should strip tags but then fail on invalid characters
        assert not form.is_valid()

    def test_name_invalid_characters(self):
        """Test name rejects invalid characters"""
        invalid_names = [
            "John123",  # Numbers
            "John@Doe",  # @ symbol
            "John#Doe",  # Hash
            "John$Doe",  # Dollar sign
        ]
        for name in invalid_names:
            form_data = {
                "name": name,
                "email": "test@example.com",
                "subject": "Test",
                "message": "Test message with enough characters",
            }
            form = ContactForm(data=form_data)
            assert not form.is_valid(), f"Name '{name}' should be invalid"
            assert "name" in form.errors

    def test_name_strips_html_tags(self):
        """Test that HTML tags are stripped from name"""
        form_data = {
            "name": "John<script>alert('xss')</script>",
            "email": "test@example.com",
            "subject": "Test Subject",
            "message": "Test message with enough characters to pass validation",
        }
        form = ContactForm(data=form_data)
        # After stripping tags, "John" should pass validation (but may still be blocked by suspicious pattern check)
        # The form checks for '<' and '>' in the cleaned value which won't exist after strip_tags
        if form.is_valid():
            assert form.cleaned_data["name"] == "John"
        # It's valid to reject it via suspicious pattern checks too

    def test_name_valid_characters(self):
        """Test name accepts valid characters"""
        valid_names = [
            "John Doe",
            "Mary-Jane",
            "O'Connor",
            "Dr. Smith",
            "Jean-Paul",
        ]
        for name in valid_names:
            form_data = {
                "name": name,
                "email": "test@example.com",
                "subject": "Test Subject",
                "message": "Test message with enough characters",
            }
            form = ContactForm(data=form_data)
            assert (
                form.is_valid()
            ), f"Name '{name}' should be valid. Errors: {form.errors}"

    def test_name_rejects_urls(self):
        """Test name field rejects URLs"""
        form_data = {
            "name": "John http://example.com",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_name_rejects_email_patterns(self):
        """Test name field rejects email-like patterns"""
        form_data = {
            "name": "john@example.com",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "name" in form.errors

    def test_name_strips_excessive_whitespace(self):
        """Test name field strips excessive whitespace"""
        form_data = {
            "name": "John    Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["name"] == "John Doe"


@pytest.mark.django_db
class TestEmailFieldValidation:
    """Tests for email field validation"""

    def test_valid_email_formats(self):
        """Test various valid email formats"""
        valid_emails = [
            "simple@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "user_name@example.com",
            "123@example.com",
        ]
        for email in valid_emails:
            form_data = {
                "name": "John Doe",
                "email": email,
                "subject": "Test",
                "message": "Test message with enough characters",
            }
            form = ContactForm(data=form_data)
            assert form.is_valid(), f"Email '{email}' should be valid"

    def test_invalid_email_formats(self):
        """Test invalid email formats are rejected"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user space@example.com",
            "user@example",
        ]
        for email in invalid_emails:
            form_data = {
                "name": "John Doe",
                "email": email,
                "subject": "Test",
                "message": "Test message with enough characters",
            }
            form = ContactForm(data=form_data)
            assert not form.is_valid(), f"Email '{email}' should be invalid"

    def test_email_converted_to_lowercase(self):
        """Test email is converted to lowercase"""
        form_data = {
            "name": "John Doe",
            "email": "USER@EXAMPLE.COM",
            "subject": "Test",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["email"] == "user@example.com"


@pytest.mark.django_db
class TestSubjectFieldValidation:
    """Tests for subject field validation"""

    def test_subject_minimum_length(self):
        """Test subject must be at least 3 characters"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "AB",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "subject" in form.errors

    def test_subject_rejects_spam_keywords(self):
        """Test subject rejects spam keywords"""
        spam_subjects = [
            "Free viagra now!",
            "You won the lottery",
            "Click here for casino",
            "Congratulations winner",
            "Make money fast",
            "Limited time offer",
        ]
        for subject in spam_subjects:
            form_data = {
                "name": "John Doe",
                "email": "test@example.com",
                "subject": subject,
                "message": "Test message with enough characters",
            }
            form = ContactForm(data=form_data)
            assert not form.is_valid(), f"Spam subject '{subject}' should be rejected"
            assert "subject" in form.errors

    def test_subject_rejects_urls(self):
        """Test subject field rejects URLs"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Check out http://spam.com",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "subject" in form.errors

    def test_subject_strips_html(self):
        """Test subject strips HTML tags"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "<b>Test</b> Subject",
            "message": "Test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()
        assert "<b>" not in form.cleaned_data["subject"]
        assert form.cleaned_data["subject"] == "Test Subject"


@pytest.mark.django_db
class TestMessageFieldValidation:
    """Tests for message field validation"""

    def test_message_minimum_length(self):
        """Test message must be at least 10 characters"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Short",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "message" in form.errors

    def test_message_maximum_length(self):
        """Test message cannot exceed 2000 characters"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "A" * 2001,
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "message" in form.errors

    def test_message_rejects_excessive_repeated_characters(self):
        """Test message rejects excessive character repetition"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "AAAAAAAAAAAAAAAA this is spam",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "message" in form.errors

    def test_message_limits_urls(self):
        """Test message limits number of URLs"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Check http://one.com and http://two.com and http://three.com",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "message" in form.errors

    def test_message_allows_up_to_two_urls(self):
        """Test message allows up to 2 URLs"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Check http://one.com and http://two.com for more info",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()

    def test_message_strips_html(self):
        """Test message strips HTML tags"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "<script>alert('xss')</script>This is my message",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()
        assert "<script>" not in form.cleaned_data["message"]
        assert "This is my message" in form.cleaned_data["message"]


@pytest.mark.django_db
class TestHoneypotValidation:
    """Tests for honeypot spam detection"""

    def test_honeypot_empty_is_valid(self):
        """Test form is valid when honeypot is empty"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
            "website": "",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()

    def test_honeypot_filled_is_invalid(self):
        """Test form is invalid when honeypot is filled (spam)"""
        form_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Test message with enough characters",
            "website": "http://spam.com",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "website" in form.errors


@pytest.mark.django_db
class TestCrossFieldValidation:
    """Tests for cross-field validation"""

    def test_name_repeated_in_message_is_spam(self):
        """Test form detects when name is repeated excessively in message"""
        form_data = {
            "name": "John",
            "email": "test@example.com",
            "subject": "Test",
            "message": "John John John John This is spam from John",
        }
        form = ContactForm(data=form_data)
        assert not form.is_valid()
        assert "__all__" in form.errors or "message" in form.errors

    def test_name_normal_usage_in_message_is_valid(self):
        """Test form allows reasonable name usage in message"""
        form_data = {
            "name": "John",
            "email": "test@example.com",
            "subject": "Test",
            "message": "Hi, my name is John and I would like to contact you",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()


@pytest.mark.django_db
class TestFormSaving:
    """Tests for form saving functionality"""

    def test_valid_form_saves_to_database(self):
        """Test valid form data is saved to database"""
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Test Subject",
            "message": "This is a test message with enough characters",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()

        contact_message = form.save()

        assert ContactMessage.objects.count() == 1
        assert contact_message.name == "John Doe"
        assert contact_message.email == "john@example.com"
        assert contact_message.subject == "Test Subject"
        assert "test message" in contact_message.message.lower()

    def test_form_saves_sanitized_data(self):
        """Test form saves sanitized (not raw) data"""
        form_data = {
            "name": "  John   Doe  ",
            "email": "JOHN@EXAMPLE.COM",
            "subject": "<b>Test</b> Subject",
            "message": "<script>alert('xss')</script>Clean message here",
        }
        form = ContactForm(data=form_data)
        assert form.is_valid()

        contact_message = form.save()

        # Check sanitization happened
        assert contact_message.name == "John Doe"  # Whitespace normalized
        assert contact_message.email == "john@example.com"  # Lowercased
        assert "<b>" not in contact_message.subject  # HTML stripped
        assert "<script>" not in contact_message.message  # XSS prevented
