"""
Integration tests for UI/UX features from Phase 7
Tests the integration between components, theme switching, and animations
"""

import json
import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, TestCase, override_settings
from django.urls import reverse

import pytest
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.integration
@pytest.mark.ui
class ThemeSwitcherIntegrationTests(TestCase):
    """Integration tests for theme switching functionality"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_theme_switcher_css_variables_integration(self):
        """Test that theme switcher properly integrates with CSS variables"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for theme manager integration
        self.assertIn("darkMode", content)
        self.assertIn("x-data", content)

    def test_theme_persistence_across_pages(self):
        """Test that theme choice persists across different pages"""
        # This would require JavaScript execution, so we test the foundation
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # Check for theme persistence mechanism
        content = response.content.decode("utf-8")
        self.assertIn("localStorage", content)

    def test_theme_affects_all_ui_components(self):
        """Test that theme switching affects all UI components"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check that all major UI components use theme classes
        self.assertIn("nav-container", content)
        self.assertIn("card-", content)
        self.assertIn("dark:", content)


@pytest.mark.integration
@pytest.mark.ui
class AnimationTriggersIntegrationTests(TestCase):
    """Integration tests for animation triggers and interactions"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_scroll_animations_integration(self):
        """Test that scroll animations are properly integrated"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for scroll animation classes and JavaScript
        self.assertIn("scroll-reveal", content)
        self.assertIn("animations.js", content)

    def test_parallax_and_animations_integration(self):
        """Test that parallax and regular animations work together"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check that both systems are present
        self.assertIn("parallax.js", content)
        self.assertIn("animations.js", content)
        self.assertIn("scroll-parallax", content)
        self.assertIn("scroll-reveal", content)

    def test_cursor_and_hover_animations_integration(self):
        """Test that custom cursor integrates with hover animations"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for cursor and hover integration
        self.assertIn("cursor.js", content)
        self.assertIn("hover:", content)

    def test_reduced_motion_affects_all_animations(self):
        """Test that reduced motion preference affects all animation systems"""
        response = self.client.get("/static/css/output.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for reduced motion support across all systems
        motion_queries = content.count("prefers-reduced-motion")
        self.assertGreater(
            motion_queries,
            3,
            "Multiple animation systems should respect motion preferences",
        )


@pytest.mark.integration
@pytest.mark.ui
class UISystemsIntegrationTests(TestCase):
    """Integration tests for overall UI systems working together"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_glassmorphism_and_parallax_integration(self):
        """Test that glassmorphism navigation works with parallax background"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check that both systems coexist
        self.assertIn("nav-container", content)
        self.assertIn("parallax-container", content)
        self.assertIn("backdrop-filter", response.content.decode("utf-8"))

    def test_aurora_backgrounds_and_content_visibility(self):
        """Test that aurora backgrounds don't interfere with content readability"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for proper z-index layering
        self.assertIn("z-10", content)  # Content layer
        self.assertIn("z-[-1]", content) or self.assertIn(
            "-z-10", content
        )  # Background layer

    def test_typography_and_animations_integration(self):
        """Test that new typography integrates with animation systems"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check that typography classes are used with animations
        self.assertIn("heading-2", content)
        self.assertIn("scroll-reveal", content)

    def test_all_javascript_systems_load_correctly(self):
        """Test that all JavaScript systems can load without conflicts"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for all JavaScript files
        required_scripts = ["animations.js", "parallax.js", "cursor.js"]
        for script in required_scripts:
            self.assertIn(script, content, f"{script} should be included")


@pytest.mark.integration
@pytest.mark.ui
@pytest.mark.slow
class PerformanceIntegrationTests(TestCase):
    """Integration tests for performance of UI systems"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_css_file_size_reasonable(self):
        """Test that CSS file size is reasonable with all effects"""
        response = self.client.get("/static/css/output.css")

        self.assertEqual(response.status_code, 200)

        # Check that CSS file isn't unreasonably large (under 2MB)
        content_length = len(response.content)
        self.assertLess(content_length, 2 * 1024 * 1024, "CSS file should be under 2MB")

    def test_javascript_files_load_efficiently(self):
        """Test that JavaScript files can be loaded efficiently"""
        js_files = [
            "/static/js/animations.js",
            "/static/js/parallax.js",
            "/static/js/cursor.js",
        ]

        for js_file in js_files:
            response = self.client.get(js_file)
            self.assertEqual(
                response.status_code, 200, f"{js_file} should load successfully"
            )

            # Check reasonable file size (under 500KB each)
            content_length = len(response.content)
            self.assertLess(
                content_length, 500 * 1024, f"{js_file} should be under 500KB"
            )

    def test_gpu_acceleration_classes_present(self):
        """Test that GPU acceleration is properly implemented"""
        response = self.client.get("/static/css/output.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for GPU acceleration properties
        gpu_properties = ["transform3d", "will-change", "backface-visibility"]
        for prop in gpu_properties:
            self.assertIn(
                prop, content, f"GPU acceleration property {prop} should be present"
            )


if __name__ == "__main__":
    pytest.main([__file__])
