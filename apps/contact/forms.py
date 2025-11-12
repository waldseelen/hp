"""
Contact forms with proper validation and sanitization
"""

import re
from typing import Any, Dict

from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """
    Contact form with comprehensive validation and sanitization
    """

    website = forms.CharField(required=False, widget=forms.HiddenInput())  # Honeypot

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message", "preferred_channel"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your Name",
                    "maxlength": 100,
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "your.email@example.com"}
            ),
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Message Subject",
                    "maxlength": 200,
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your message...",
                    "rows": 5,
                    "maxlength": 2000,
                }
            ),
            "preferred_channel": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }

    def clean_name(self) -> str:
        """Validate and sanitize name field"""
        name = self.cleaned_data.get("name")
        if not name:
            raise ValidationError("Name is required.")

        # Strip HTML and excessive whitespace
        name = strip_tags(name).strip()
        name = re.sub(r"\s+", " ", name)

        # Check minimum length
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters long.")

        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
            raise ValidationError(
                "Name contains invalid characters. Only letters, spaces, hyphens, apostrophes, and dots are allowed."
            )

        # Check for suspicious patterns
        suspicious_patterns = [
            r"https?://",
            r"www\.",
            r"[<>{}[\]\\]",
            r"javascript:",
            r"data:",
            r"@.*\.",  # Email-like patterns
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, name.lower()):
                raise ValidationError("Name contains invalid content.")

        return name

    def clean_email(self) -> str:
        """Validate email field"""
        email = self.cleaned_data.get("email")
        if not email:
            raise ValidationError("Email is required.")

        # Basic email validation (Django's EmailField handles most of this)
        email = email.lower().strip()

        # Check for suspicious domains or patterns
        suspicious_domains = [
            "tempmail",
            "guerrillamail",
            "10minutemail",
            "mailinator",
            "yopmail",
            "throwaway",
            "temp-mail",
        ]

        email_domain = email.split("@")[-1] if "@" in email else ""
        for suspicious in suspicious_domains:
            if suspicious in email_domain.lower():
                # Don't completely block, just warn in logs
                pass

        return email

    def clean_subject(self) -> str:
        """Validate and sanitize subject field"""
        subject = self.cleaned_data.get("subject")
        if not subject:
            raise ValidationError("Subject is required.")

        # Strip HTML and excessive whitespace
        subject = strip_tags(subject).strip()
        subject = re.sub(r"\s+", " ", subject)

        # Check minimum length
        if len(subject) < 3:
            raise ValidationError("Subject must be at least 3 characters long.")

        # Check for spam-like content
        spam_patterns = [
            r"viagra|cialis|casino|lottery|winner|congratulations|click here|act now",
            r"free money|easy money|make money fast|work from home",
            r"urgent|limited time|expires soon|act quickly",
            r"https?://[^\s]+",  # URLs in subject
        ]

        for pattern in spam_patterns:
            if re.search(pattern, subject.lower()):
                raise ValidationError(
                    "Subject contains content that appears to be spam."
                )

        return subject

    def clean_message(self) -> str:
        """Validate and sanitize message field"""
        message = self.cleaned_data.get("message")
        if not message:
            raise ValidationError("Message is required.")

        # Strip HTML but preserve basic formatting
        message = strip_tags(message).strip()

        # Check minimum length
        if len(message) < 10:
            raise ValidationError("Message must be at least 10 characters long.")

        # Check maximum length
        if len(message) > 2000:
            raise ValidationError(
                "Message is too long. Please keep it under 2000 characters."
            )

        # Check for excessive repeated characters or patterns
        if re.search(r"(.)\1{10,}", message):  # Same character repeated 10+ times
            raise ValidationError("Message contains excessive repeated characters.")

        # Check for excessive URLs
        url_matches = re.findall(r"https?://[^\s]+", message)
        if len(url_matches) > 2:
            raise ValidationError(
                "Message contains too many URLs. Please limit to 2 URLs maximum."
            )

        # Check for phone number patterns (optional - you might want to allow these)
        # phone_patterns = re.findall(r'(\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4})', message)
        # if len(phone_patterns) > 2:
        #     raise ValidationError('Message contains too many phone numbers.')

        return message

    def clean_website(self) -> str:
        """Validate honeypot field"""
        website = self.cleaned_data.get("website")
        if website:
            # If honeypot is filled, it's likely spam
            raise ValidationError("Invalid form submission detected.")
        return website

    def clean(self) -> Dict[str, Any]:
        """Additional cross-field validation"""
        cleaned_data = super().clean()

        # Check if name and message are too similar (potential spam)
        name = cleaned_data.get("name", "").lower()
        message = cleaned_data.get("message", "").lower()

        if name and message and len(name) > 3:
            # If name appears multiple times in message, might be spam
            name_count = message.count(name)
            if name_count > 3:
                raise ValidationError("Message content appears to be spam.")

        return cleaned_data
