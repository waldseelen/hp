"""
Admin utilities for enhanced content management with TinyMCE integration.
Provides mixins for WYSIWYG editing and content management features.
"""

from django.contrib import admin

from apps.main.sanitizer import ContentSanitizer


class TinyMCEAdminMixin(admin.ModelAdmin):
    """
    Mixin to integrate TinyMCE WYSIWYG editor into Django admin.
    Automatically uses TinyMCE for TextField content fields.
    """

    # List of text fields that should use TinyMCE
    tinymce_fields = ()

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)
        self._customize_tinymce_fields()

    def _customize_tinymce_fields(self):
        """Apply custom TinyMCE configuration to specified fields."""
        if self.tinymce_fields:
            # TinyMCE is configured globally via settings.py
            # and applied automatically to all TextField fields
            pass

    def save_model(self, request, obj, form, change):
        """
        Save model with content sanitization if needed.
        Override in subclass to handle specific sanitization.
        """
        super().save_model(request, obj, form, change)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """
        Enhance the change form with additional context for TinyMCE.
        """
        context = super().render_change_form(
            request, context, add, change, form_url, obj
        )
        return context


class SanitizedContentAdminMixin(TinyMCEAdminMixin):
    """
    Enhanced mixin that combines TinyMCE with automatic content sanitization.
    Useful for fields that should be sanitized on save.
    """

    # Specify which fields should be sanitized
    sanitized_fields: tuple = ()

    # Default sanitization type ('html', 'markdown', 'text')
    sanitization_type = "html"

    def save_model(self, request, obj, form, change):
        """
        Save model with content sanitization.
        """
        # Sanitize specified fields
        for field_name in self.sanitized_fields:
            if hasattr(obj, field_name):
                original_content = getattr(obj, field_name)
                if original_content:
                    sanitized = ContentSanitizer.sanitize_by_type(
                        original_content, self.sanitization_type
                    )
                    setattr(obj, field_name, sanitized)

        super().save_model(request, obj, form, change)

    def render_change_form(
        self, request, context, add=False, change=False, form_url="", obj=None
    ):
        """
        Add sanitization info to the admin form.
        """
        context = super().render_change_form(
            request, context, add, change, form_url, obj
        )
        context["sanitization_enabled"] = True
        context["sanitized_fields"] = list(self.sanitized_fields)
        return context


class ContentRevisionMixin(admin.ModelAdmin):
    """
    Mixin to track content revisions (requires django-reversion).
    Provides version history tracking for content changes.
    """

    # Specify which fields should be tracked for revisions
    track_fields = "__all__"  # Can be a tuple of field names

    def get_readonly_fields(self, request, obj=None):
        """
        Add version history as read-only field if viewing change form.
        """
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # Viewing existing object
            readonly.append("version_history")
            return tuple(readonly)
        return tuple(readonly)

    def version_history(self, obj):
        """
        Display version history for the object.
        This requires django-reversion to be installed and configured.
        """
        try:
            from reversion.models import Version

            versions = Version.objects.get_for_object(obj)
            return f"{versions.count()} version(s) available"
        except ImportError:
            return "Version tracking requires django-reversion"

    version_history.short_description = "Content History"
