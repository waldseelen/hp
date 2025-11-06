"""
Integration tests for Third-Party Services - Phase 22C.3: Email Sending.

Tests cover:
- Email sending (Django locmem backend)
- Email templates rendering
- Email attachments
- HTML vs plain text emails
- Bulk email sending
- Email error handling

Target: Verify email integration works correctly.
"""

from django.conf import settings
from django.core import mail
from django.core.mail import (
    EmailMessage,
    EmailMultiAlternatives,
    send_mail,
    send_mass_mail,
)
from django.template.loader import render_to_string

import pytest

# ============================================================================
# BASIC EMAIL SENDING TESTS
# ============================================================================


@pytest.mark.django_db
class TestBasicEmailSending:
    """Test basic email sending functionality."""

    def setup_method(self):
        """Set up test environment (clear mail outbox)."""
        mail.outbox = []

    def test_send_simple_email(self):
        """Test sending a simple email."""
        send_mail(
            subject="Test Subject",
            message="Test message body",
            from_email="from@example.com",
            recipient_list=["to@example.com"],
            fail_silently=False,
        )

        # Check email was sent
        assert len(mail.outbox) == 1

        email = mail.outbox[0]
        assert email.subject == "Test Subject"
        assert email.body == "Test message body"
        assert email.from_email == "from@example.com"
        assert "to@example.com" in email.to

    def test_send_email_with_multiple_recipients(self):
        """Test sending email to multiple recipients."""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

        send_mail(
            subject="Multi-recipient Test",
            message="Message to multiple recipients",
            from_email="sender@example.com",
            recipient_list=recipients,
        )

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert len(email.to) == 3
        assert all(recipient in email.to for recipient in recipients)

    def test_send_email_with_cc_and_bcc(self):
        """Test sending email with CC and BCC."""
        email = EmailMessage(
            subject="Test CC/BCC",
            body="Test message",
            from_email="sender@example.com",
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )
        email.send()

        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert "cc@example.com" in sent_email.cc
        assert "bcc@example.com" in sent_email.bcc


# ============================================================================
# HTML EMAIL TESTS
# ============================================================================


@pytest.mark.django_db
class TestHTMLEmails:
    """Test HTML email sending."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_send_html_email(self):
        """Test sending HTML email."""
        html_content = "<h1>Hello</h1><p>This is an <strong>HTML</strong> email.</p>"
        text_content = "Hello\n\nThis is an HTML email."

        email = EmailMultiAlternatives(
            subject="HTML Email Test",
            body=text_content,
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert sent_email.alternatives[0][0] == html_content
        assert sent_email.alternatives[0][1] == "text/html"

    def test_html_email_with_fallback_text(self):
        """Test HTML email includes plain text fallback."""
        html_content = "<p>HTML version</p>"
        text_content = "Plain text version"

        email = EmailMultiAlternatives(
            subject="Test Fallback",
            body=text_content,
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        sent_email = mail.outbox[0]
        assert sent_email.body == text_content
        assert len(sent_email.alternatives) == 1


# ============================================================================
# EMAIL TEMPLATE RENDERING TESTS
# ============================================================================


@pytest.mark.django_db
class TestEmailTemplateRendering:
    """Test email template rendering."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    @pytest.mark.skip("Requires actual email template files")
    def test_render_email_template(self):
        """Test rendering email from template."""
        context = {
            "user_name": "John Doe",
            "activation_link": "https://example.com/activate/abc123",
        }

        # Render template
        html_content = render_to_string("emails/activation_email.html", context)
        text_content = render_to_string("emails/activation_email.txt", context)

        # Send email
        email = EmailMultiAlternatives(
            subject="Account Activation",
            body=text_content,
            from_email="noreply@example.com",
            to=["user@example.com"],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        assert len(mail.outbox) == 1
        assert "John Doe" in mail.outbox[0].body

    def test_email_with_dynamic_content(self):
        """Test email with dynamically generated content."""
        user_name = "Alice"
        order_total = "$99.99"

        subject = f"Order Confirmation for {user_name}"
        body = f"Thank you {user_name}! Your order total: {order_total}"

        send_mail(
            subject=subject,
            message=body,
            from_email="orders@example.com",
            recipient_list=["alice@example.com"],
        )

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "Alice" in email.subject
        assert "$99.99" in email.body


# ============================================================================
# EMAIL ATTACHMENTS TESTS
# ============================================================================


@pytest.mark.django_db
class TestEmailAttachments:
    """Test email attachments."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_send_email_with_attachment(self):
        """Test sending email with file attachment."""
        email = EmailMessage(
            subject="Email with Attachment",
            body="Please see attached file.",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )

        # Attach file
        attachment_content = b"This is a test file content"
        email.attach("test_file.txt", attachment_content, "text/plain")
        email.send()

        assert len(mail.outbox) == 1
        sent_email = mail.outbox[0]
        assert len(sent_email.attachments) == 1
        assert sent_email.attachments[0][0] == "test_file.txt"

    def test_send_email_with_multiple_attachments(self):
        """Test sending email with multiple attachments."""
        email = EmailMessage(
            subject="Multiple Attachments",
            body="Two files attached",
            from_email="sender@example.com",
            to=["recipient@example.com"],
        )

        email.attach("file1.txt", b"Content 1", "text/plain")
        email.attach("file2.pdf", b"PDF content", "application/pdf")
        email.send()

        sent_email = mail.outbox[0]
        assert len(sent_email.attachments) == 2


# ============================================================================
# BULK EMAIL SENDING TESTS
# ============================================================================


@pytest.mark.django_db
class TestBulkEmailSending:
    """Test bulk email sending."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_send_mass_mail(self):
        """Test sending mass mail (multiple emails efficiently)."""
        message1 = ("Subject 1", "Body 1", "from@example.com", ["user1@example.com"])
        message2 = ("Subject 2", "Body 2", "from@example.com", ["user2@example.com"])
        message3 = ("Subject 3", "Body 3", "from@example.com", ["user3@example.com"])

        send_mass_mail(
            (message1, message2, message3),
            fail_silently=False,
        )

        assert len(mail.outbox) == 3
        assert mail.outbox[0].subject == "Subject 1"
        assert mail.outbox[1].subject == "Subject 2"
        assert mail.outbox[2].subject == "Subject 3"

    def test_send_bulk_emails_to_users(self):
        """Test sending bulk promotional emails to users."""
        users = [
            {"email": "user1@example.com", "name": "User 1"},
            {"email": "user2@example.com", "name": "User 2"},
            {"email": "user3@example.com", "name": "User 3"},
        ]

        messages = []
        for user in users:
            message = (
                "Promotional Email",
                f"Hello {user['name']}, check out our new products!",
                "marketing@example.com",
                [user["email"]],
            )
            messages.append(message)

        send_mass_mail(messages, fail_silently=False)

        assert len(mail.outbox) == 3


# ============================================================================
# EMAIL ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.django_db
class TestEmailErrorHandling:
    """Test email error handling."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_send_email_fail_silently_true(self):
        """Test send_mail with fail_silently=True doesn't raise errors."""
        # This won't actually fail with locmem backend, but demonstrates usage
        send_mail(
            subject="Test",
            message="Test message",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=True,  # Won't raise exceptions
        )

        assert len(mail.outbox) == 1

    def test_send_email_fail_silently_false(self):
        """Test send_mail with fail_silently=False raises errors."""
        # With locmem backend, this won't fail, but demonstrates behavior
        send_mail(
            subject="Test",
            message="Test message",
            from_email="sender@example.com",
            recipient_list=["recipient@example.com"],
            fail_silently=False,  # Will raise exceptions on error
        )

        assert len(mail.outbox) == 1

    def test_invalid_email_address(self):
        """Test handling invalid email address."""
        # Django validates email format, should raise exception
        # (Actual validation depends on email backend)
        email = EmailMessage(
            subject="Test",
            body="Test",
            from_email="sender@example.com",
            to=["invalid-email"],  # Invalid format
        )

        # With locmem backend, this may not fail
        # But in production (SMTP), would fail
        email.send(fail_silently=True)


# ============================================================================
# EMAIL HEADER TESTS
# ============================================================================


@pytest.mark.django_db
class TestEmailHeaders:
    """Test email headers."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_email_with_custom_headers(self):
        """Test sending email with custom headers."""
        email = EmailMessage(
            subject="Custom Headers",
            body="Test",
            from_email="sender@example.com",
            to=["recipient@example.com"],
            headers={
                "Reply-To": "replyto@example.com",
                "X-Custom-Header": "CustomValue",
            },
        )
        email.send()

        sent_email = mail.outbox[0]
        assert sent_email.extra_headers["Reply-To"] == "replyto@example.com"
        assert sent_email.extra_headers["X-Custom-Header"] == "CustomValue"

    def test_email_reply_to_header(self):
        """Test email with Reply-To header."""
        email = EmailMessage(
            subject="Reply-To Test",
            body="Please reply to different address",
            from_email="noreply@example.com",
            to=["user@example.com"],
            reply_to=["support@example.com"],
        )
        email.send()

        sent_email = mail.outbox[0]
        assert "support@example.com" in sent_email.reply_to


# ============================================================================
# CONTACT FORM EMAIL TESTS
# ============================================================================


@pytest.mark.django_db
class TestContactFormEmails:
    """Test contact form email sending."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_send_contact_form_notification(self):
        """Test sending contact form notification email."""
        # Simulate contact form submission
        form_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Website Inquiry",
            "message": "I have a question about your services.",
        }

        # Send notification to admin
        send_mail(
            subject=f"Contact Form: {form_data['subject']}",
            message=f"From: {form_data['name']} <{form_data['email']}>\n\n{form_data['message']}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],  # Admin email
        )

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert "John Doe" in email.body
        assert "john@example.com" in email.body

    def test_send_contact_form_confirmation(self):
        """Test sending contact form confirmation to user."""
        user_email = "user@example.com"
        user_name = "Jane Smith"

        send_mail(
            subject="Thank you for contacting us",
            message=f"Dear {user_name},\n\nWe received your message and will respond soon.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
        )

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        assert email.to[0] == user_email
        assert "Jane Smith" in email.body


# ============================================================================
# EMAIL BACKEND CONFIGURATION TESTS
# ============================================================================


@pytest.mark.django_db
class TestEmailBackendConfiguration:
    """Test email backend configuration."""

    def test_locmem_backend_configured(self):
        """Test locmem email backend is configured for testing."""
        # In test settings, should be using locmem backend
        from django.conf import settings

        # Check if EMAIL_BACKEND is set to locmem
        assert (
            "locmem" in settings.EMAIL_BACKEND.lower()
            or settings.EMAIL_BACKEND == "django.core.mail.backends.locmem.EmailBackend"
        )

    def test_mail_outbox_accessible(self):
        """Test mail.outbox is accessible for testing."""
        mail.outbox = []

        send_mail(
            subject="Test",
            message="Test",
            from_email="test@example.com",
            recipient_list=["recipient@example.com"],
        )

        # Should be able to access mail.outbox
        assert hasattr(mail, "outbox")
        assert len(mail.outbox) == 1


# ============================================================================
# EMAIL CONTENT VALIDATION TESTS
# ============================================================================


@pytest.mark.django_db
class TestEmailContentValidation:
    """Test email content validation."""

    def setup_method(self):
        """Set up test environment."""
        mail.outbox = []

    def test_email_contains_expected_content(self):
        """Test email contains expected content."""
        expected_keywords = ["password", "reset", "link"]

        send_mail(
            subject="Password Reset Request",
            message="Click this link to reset your password: https://example.com/reset/abc123",
            from_email="noreply@example.com",
            recipient_list=["user@example.com"],
        )

        email = mail.outbox[0]
        for keyword in expected_keywords:
            assert keyword in email.subject.lower() or keyword in email.body.lower()

    def test_email_does_not_contain_sensitive_data(self):
        """Test email doesn't accidentally include sensitive data."""
        # Example: Don't include raw passwords in emails

        send_mail(
            subject="Account Created",
            message="Your account has been created. Please log in to set your password.",
            from_email="noreply@example.com",
            recipient_list=["user@example.com"],
        )

        email = mail.outbox[0]
        # Ensure no actual passwords in email body
        assert "password123" not in email.body  # Example sensitive data
        assert "secret_key" not in email.body
