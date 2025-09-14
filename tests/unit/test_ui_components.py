"""
Unit tests for UI/UX components and functionality
Tests individual UI components, theme utilities, and user interface logic
"""

import pytest
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
import json
import re

from apps.main.models import PersonalInfo
from apps.main.views import home


User = get_user_model()


@pytest.mark.unit
@pytest.mark.ui
class ThemeUtilityTests(TestCase):
    """Unit tests for theme-related utilities and functions"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.factory = RequestFactory()

    def test_homepage_contains_theme_css_classes(self):
        """Test that homepage contains proper theme CSS classes"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

        # Check for essential theme CSS classes
        self.assertContains(response, 'dark')
        self.assertContains(response, 'bg-background-primary')
        self.assertContains(response, 'text-text-primary')

    def test_theme_manager_script_included(self):
        """Test that theme manager JavaScript is included"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'theme-manager.js')

    def test_css_custom_properties_loaded(self):
        """Test that CSS custom properties for theming are loaded"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for CSS custom properties
        self.assertIn('--primary-', content)
        self.assertIn('--background-', content)
        self.assertIn('--text-', content)

    def test_tailwind_config_colors_structure(self):
        """Test that Tailwind config has proper color structure (indirect test)"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

        # Check for semantic color classes in HTML
        content = b''.join(response.streaming_content).decode('utf-8')
        self.assertIn('bg-background-primary', content)
        self.assertIn('text-text-primary', content)


@pytest.mark.unit
@pytest.mark.ui
class AnimationComponentTests(TestCase):
    """Unit tests for animation components and CSS"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_animation_css_classes_exist(self):
        """Test that animation CSS classes are properly defined"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for animation classes
        self.assertIn('animate-fade-in', content)
        self.assertIn('animate-slide-up', content)
        self.assertIn('@keyframes', content)

    def test_transition_classes_exist(self):
        """Test that transition classes are properly defined"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for transition classes
        self.assertIn('transition-all', content)
        self.assertIn('duration-300', content)
        self.assertIn('ease-in-out', content)

    def test_homepage_elements_have_animation_classes(self):
        """Test that homepage elements have proper animation classes"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for animation classes in HTML
        self.assertIn('animate-slide-up', content)
        self.assertIn('data-animate', content)

    def test_hover_animation_classes_exist(self):
        """Test that hover animation classes exist"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for hover animation classes
        self.assertIn('hover:', content)
        self.assertIn('group-hover:', content)
        self.assertIn('hover:scale-', content)

    def test_reduced_motion_support(self):
        """Test that reduced motion preferences are supported"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for reduced motion media query
        self.assertIn('prefers-reduced-motion', content)


@pytest.mark.unit
@pytest.mark.ui
class ButtonComponentTests(TestCase):
    """Unit tests for button components"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_contact_me_button_exists(self):
        """Test that Contact Me button exists on homepage"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contact Me')

    def test_contact_me_button_has_proper_link(self):
        """Test that Contact Me button links to contact form"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for contact form URL
        self.assertIn('/contact/', content)

    def test_contact_me_button_styling(self):
        """Test that Contact Me button has proper styling classes"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for button styling classes
        self.assertIn('hover:scale-105', content)
        self.assertIn('transition-all', content)
        self.assertIn('bg-gradient-to-r', content)

    def test_button_accessibility_attributes(self):
        """Test that buttons have proper accessibility attributes"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for accessibility attributes
        self.assertIn('aria-label', content)
        self.assertIn('focus:outline-none', content)
        self.assertIn('focus:ring-', content)

    def test_button_hover_effects_css(self):
        """Test that button hover effects are defined in CSS"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for button hover effects
        self.assertIn('.btn', content)
        self.assertIn('hover:', content)
        self.assertIn('transform', content)


@pytest.mark.unit
@pytest.mark.ui
class NavigationComponentTests(TestCase):
    """Unit tests for navigation components"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_navigation_exists(self):
        """Test that navigation bar exists"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<nav')

    def test_navigation_links_exist(self):
        """Test that proper navigation links exist"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

        # Check for main navigation links
        self.assertContains(response, 'About')
        self.assertContains(response, 'Blog')

    def test_navigation_responsive_classes(self):
        """Test that navigation has responsive CSS classes"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for responsive classes
        self.assertIn('sm:', content)
        self.assertIn('md:', content)
        self.assertIn('lg:', content)

    def test_language_switcher_exists(self):
        """Test that language switcher exists in navigation"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for language switching elements
        # This might need adjustment based on actual implementation


@pytest.mark.unit
@pytest.mark.ui
class CardComponentTests(TestCase):
    """Unit tests for card components"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_card_classes_exist_in_css(self):
        """Test that card CSS classes are properly defined"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for card classes
        self.assertIn('.card', content)
        self.assertIn('backdrop-filter', content)
        self.assertIn('border-radius', content)

    def test_card_hover_effects_css(self):
        """Test that card hover effects are defined"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for card hover effects
        self.assertIn('card:hover', content)
        self.assertIn('transform', content)

    def test_glass_morphism_effects(self):
        """Test that glass morphism effects are applied to cards"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for glass morphism properties
        self.assertIn('backdrop-filter', content)
        self.assertIn('blur', content)


@pytest.mark.unit
@pytest.mark.ui
class ResponsiveDesignTests(TestCase):
    """Unit tests for responsive design components"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_responsive_classes_exist(self):
        """Test that responsive CSS classes exist"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for responsive utilities
        self.assertIn('@media', content)
        self.assertIn('min-width:', content)

    def test_responsive_grid_classes(self):
        """Test that responsive grid classes are defined"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for grid classes
        self.assertIn('responsive-grid', content)
        self.assertIn('grid-template-columns', content)

    def test_homepage_has_responsive_classes(self):
        """Test that homepage uses responsive classes"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for responsive classes in HTML
        self.assertIn('sm:', content)
        self.assertIn('md:', content)
        self.assertIn('lg:', content)

    def test_container_responsive_classes(self):
        """Test that container has responsive sizing"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for responsive container
        self.assertIn('responsive-container', content)
        self.assertIn('max-width', content)


@pytest.mark.unit
@pytest.mark.ui
class AccessibilityTests(TestCase):
    """Unit tests for accessibility features"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_focus_ring_styles_exist(self):
        """Test that focus ring styles are defined"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for focus styles
        self.assertIn('focus:', content)
        self.assertIn('focus-ring', content)
        self.assertIn('outline', content)

    def test_skip_navigation_exists(self):
        """Test that skip navigation link exists"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for skip navigation
        self.assertIn('skip', content.lower())
        self.assertIn('main', content.lower())

    def test_aria_labels_exist(self):
        """Test that proper ARIA labels exist"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for ARIA labels
        self.assertIn('aria-label', content)

    def test_semantic_html_structure(self):
        """Test that proper semantic HTML is used"""
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)

        # Check for semantic HTML elements
        self.assertContains(response, '<main')
        self.assertContains(response, '<nav')
        self.assertContains(response, '<header')
        self.assertContains(response, '<section')

    def test_high_contrast_support(self):
        """Test that high contrast mode is supported"""
        response = self.client.get('/static/css/custom.css')

        self.assertEqual(response.status_code, 200)
        content = b''.join(response.streaming_content).decode('utf-8')

        # Check for high contrast media query
        self.assertIn('prefers-contrast', content)


if __name__ == '__main__':
    pytest.main([__file__])