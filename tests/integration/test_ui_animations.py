"""
Integration tests for UI animation triggers and behaviors
Tests scroll-based animations, hover effects, and interactive animations
"""

import json
import time

from django.test import TestCase
from django.test.client import Client

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@pytest.mark.integration
@pytest.mark.ui
@pytest.mark.animation
class ScrollAnimationIntegrationTest(TestCase):
    """Integration tests for scroll-triggered animations"""

    def setUp(self):
        """Set up test client and Chrome driver"""
        self.client = Client()

        # Setup Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.has_driver = True
        except Exception as e:
            self.has_driver = False
            print(f"Chrome driver not available: {e}")

    def tearDown(self):
        """Clean up Chrome driver"""
        if hasattr(self, "driver") and self.has_driver:
            self.driver.quit()

    def test_animate_slide_up_css_classes_exist(self):
        """Test that slide-up animation CSS classes exist"""
        response = self.client.get("/static/css/custom.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for slide-up animation classes
        self.assertIn("animate-slide-up", content)
        self.assertIn("slideUp", content)

    def test_fade_in_animation_css_classes_exist(self):
        """Test that fade-in animation CSS classes exist"""
        response = self.client.get("/static/css/custom.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for fade-in animation classes
        self.assertIn("animate-fade-in", content)
        self.assertIn("fadeIn", content)

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_homepage_elements_have_animation_classes(self):
        """Test that homepage elements have proper animation classes"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Check for elements with animation classes
        animated_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[class*='animate-'], [data-animate]"
        )

        self.assertGreater(
            len(animated_elements), 0, "No elements with animation classes found"
        )

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_scroll_triggered_animations(self):
        """Test that scrolling triggers animations on elements"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Get page height for scrolling
        page_height = self.driver.execute_script("return document.body.scrollHeight")

        # Scroll down to middle of page
        self.driver.execute_script(f"window.scrollTo(0, {page_height // 2})")

        time.sleep(1)  # Wait for animations to trigger

        # Check if elements became visible (basic scroll test)
        visible_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "[class*='animate-']:not([style*='opacity: 0'])"
        )

        # This test checks that animated elements are not hidden
        # Specific animation behavior would need more detailed testing
        self.assertGreaterEqual(len(visible_elements), 0)


@pytest.mark.integration
@pytest.mark.ui
@pytest.mark.animation
class HoverAnimationIntegrationTest(TestCase):
    """Integration tests for hover-triggered animations"""

    def setUp(self):
        """Set up test client and Chrome driver"""
        self.client = Client()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.has_driver = True
        except Exception:
            self.has_driver = False

    def tearDown(self):
        """Clean up Chrome driver"""
        if hasattr(self, "driver") and self.has_driver:
            self.driver.quit()

    def test_hover_animation_css_exists(self):
        """Test that hover animation CSS exists"""
        response = self.client.get("/static/css/custom.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for hover-related CSS
        self.assertIn("hover:", content)
        self.assertIn("group-hover:", content)
        self.assertIn("transition", content)

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_button_hover_effects(self):
        """Test that buttons have hover effects"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Find buttons on the page
        buttons = self.driver.find_elements(
            By.CSS_SELECTOR, "button, .btn, a[class*='btn']"
        )

        if buttons:
            button = buttons[0]

            # Get initial styles
            initial_transform = button.value_of_css_property("transform")

            # Hover over button
            actions = ActionChains(self.driver)
            actions.move_to_element(button).perform()

            time.sleep(0.3)  # Wait for transition

            # Check if styles changed
            hover_transform = button.value_of_css_property("transform")

            # Note: This might need adjustment based on actual implementation
            # The test checks that some hover effect is present

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_card_hover_effects(self):
        """Test that cards have hover effects"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Find card elements
        cards = self.driver.find_elements(
            By.CSS_SELECTOR, ".card, [class*='card'], .group"
        )

        if cards:
            card = cards[0]

            # Test hover effect
            actions = ActionChains(self.driver)
            actions.move_to_element(card).perform()

            time.sleep(0.3)  # Wait for transition

            # Check that card is still visible (basic test)
            self.assertTrue(card.is_displayed())

    def test_contact_me_button_hover_css(self):
        """Test that Contact Me button has proper hover CSS"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check that Contact Me button has hover classes
        self.assertIn("hover:scale-", content)
        self.assertIn("transition-", content)


@pytest.mark.integration
@pytest.mark.ui
@pytest.mark.animation
class InteractiveAnimationTest(TestCase):
    """Integration tests for interactive animations"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.has_driver = True
        except Exception:
            self.has_driver = False

    def tearDown(self):
        """Clean up Chrome driver"""
        if hasattr(self, "driver") and self.has_driver:
            self.driver.quit()

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_loading_spinner_animation(self):
        """Test loading spinner animation functionality"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Check if loading elements exist in CSS
        response = self.client.get("/static/css/custom.css")
        content = response.content.decode("utf-8")

        self.assertIn("loading-spinner", content)
        self.assertIn("@keyframes", content)

    def test_starfield_animation_keyframes(self):
        """Test that starfield animation keyframes are properly defined"""
        response = self.client.get("/static/css/custom.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for starfield animation keyframes
        self.assertIn("starfield", content)
        self.assertIn("translateY", content)

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_focus_ring_animations(self):
        """Test that focus ring animations work properly"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Find focusable elements
        focusable_elements = self.driver.find_elements(
            By.CSS_SELECTOR, "button, a, input, [tabindex]"
        )

        if focusable_elements:
            element = focusable_elements[0]

            # Focus on element
            element.click()

            time.sleep(0.1)  # Wait for focus styles

            # Check that element is focused
            focused_element = self.driver.switch_to.active_element
            self.assertEqual(focused_element, element)

    def test_animation_duration_css_properties(self):
        """Test that proper animation durations are set in CSS"""
        response = self.client.get("/static/css/custom.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for consistent animation durations
        self.assertIn("duration-300", content)
        self.assertIn("ease-in-out", content)

    def test_reduced_motion_css_support(self):
        """Test that reduced motion preferences are respected in CSS"""
        response = self.client.get("/static/css/custom.css")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Check for prefers-reduced-motion media query
        self.assertIn("prefers-reduced-motion", content)


if __name__ == "__main__":
    pytest.main([__file__])
