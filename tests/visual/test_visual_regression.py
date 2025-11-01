"""
Visual regression tests for key UI components
Tests visual consistency across theme changes and responsive breakpoints
"""

import hashlib
import os
import time

from django.test import TestCase
from django.test.client import Client

import pytest
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class VisualTestUtils:
    """Utility class for visual testing operations"""

    @staticmethod
    def get_screenshots_dir():
        """Get the directory for storing test screenshots"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshots_dir = os.path.join(base_dir, "visual", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir

    @staticmethod
    def capture_element_screenshot(driver, element, filename):
        """Capture screenshot of a specific element"""
        screenshots_dir = VisualTestUtils.get_screenshots_dir()
        filepath = os.path.join(screenshots_dir, filename)

        # Scroll element into view
        driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(0.5)

        # Take screenshot of the element
        element.screenshot(filepath)
        return filepath

    @staticmethod
    def capture_full_page_screenshot(driver, filename):
        """Capture full page screenshot"""
        screenshots_dir = VisualTestUtils.get_screenshots_dir()
        filepath = os.path.join(screenshots_dir, filename)

        # Set window size for consistent screenshots
        driver.set_window_size(1920, 1080)

        # Capture full page
        driver.save_screenshot(filepath)
        return filepath

    @staticmethod
    def compare_images(image1_path, image2_path, threshold=0.1):
        """Compare two images and return similarity score"""
        try:
            img1 = Image.open(image1_path)
            img2 = Image.open(image2_path)

            # Ensure images are same size
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            # Calculate difference
            diff = ImageChops.difference(img1, img2)
            stat = diff.histogram()

            # Calculate percentage difference
            total_pixels = img1.size[0] * img1.size[1]
            non_zero_pixels = sum(stat[1:])
            difference_ratio = non_zero_pixels / total_pixels

            return difference_ratio < threshold

        except Exception as e:
            print(f"Error comparing images: {e}")
            return False

    @staticmethod
    def generate_baseline_if_needed(filepath, baseline_name):
        """Generate baseline image if it doesn't exist"""
        screenshots_dir = VisualTestUtils.get_screenshots_dir()
        baseline_path = os.path.join(screenshots_dir, "baselines", baseline_name)

        os.makedirs(os.path.dirname(baseline_path), exist_ok=True)

        if not os.path.exists(baseline_path):
            # Copy current screenshot as baseline
            if os.path.exists(filepath):
                import shutil

                shutil.copy2(filepath, baseline_path)
                print(f"Generated baseline: {baseline_name}")

        return baseline_path


@pytest.mark.visual
@pytest.mark.integration
class HomepageVisualRegressionTest(TestCase):
    """Visual regression tests for homepage components"""

    def setUp(self):
        """Set up Chrome driver for visual testing"""
        self.client = Client()

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

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

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_homepage_hero_section_visual(self):
        """Test visual consistency of homepage hero section"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Find hero section
        hero_sections = self.driver.find_elements(
            By.CSS_SELECTOR, "section, .hero, [class*='hero']"
        )

        if hero_sections:
            hero = hero_sections[0]

            # Capture hero section screenshot
            screenshot_path = VisualTestUtils.capture_element_screenshot(
                self.driver, hero, "homepage_hero_current.png"
            )

            # Generate or compare with baseline
            baseline_path = VisualTestUtils.generate_baseline_if_needed(
                screenshot_path, "homepage_hero_baseline.png"
            )

            # If baseline exists, compare
            if os.path.exists(baseline_path):
                is_similar = VisualTestUtils.compare_images(
                    screenshot_path, baseline_path, threshold=0.05
                )

                self.assertTrue(
                    is_similar,
                    "Hero section visual regression detected. "
                    f"Compare {screenshot_path} with {baseline_path}",
                )

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_contact_button_visual_consistency(self):
        """Test visual consistency of Contact Me button"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Find Contact Me button
        contact_buttons = self.driver.find_elements(
            By.XPATH,
            "//a[contains(text(), 'Contact Me') or contains(text(), 'Contact')]",
        )

        if contact_buttons:
            button = contact_buttons[0]

            # Capture button screenshot
            screenshot_path = VisualTestUtils.capture_element_screenshot(
                self.driver, button, "contact_button_current.png"
            )

            # Generate or compare with baseline
            baseline_path = VisualTestUtils.generate_baseline_if_needed(
                screenshot_path, "contact_button_baseline.png"
            )

            if os.path.exists(baseline_path):
                is_similar = VisualTestUtils.compare_images(
                    screenshot_path, baseline_path, threshold=0.02
                )

                self.assertTrue(is_similar, "Contact button visual regression detected")

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_navigation_visual_consistency(self):
        """Test visual consistency of navigation bar"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for navigation to load
        nav_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "nav, header"))
        )

        # Capture navigation screenshot
        screenshot_path = VisualTestUtils.capture_element_screenshot(
            self.driver, nav_element, "navigation_current.png"
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, "navigation_baseline.png"
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.03
            )

            self.assertTrue(is_similar, "Navigation visual regression detected")


@pytest.mark.visual
@pytest.mark.integration
class ThemeVisualRegressionTest(TestCase):
    """Visual regression tests across different themes"""

    def setUp(self):
        """Set up Chrome driver for theme testing"""
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

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_dark_theme_visual_consistency(self):
        """Test visual consistency of dark theme"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Ensure dark theme is active
        self.driver.execute_script("document.documentElement.className = 'dark';")

        time.sleep(1)  # Wait for theme to apply

        # Capture full page screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, "dark_theme_current.png"
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, "dark_theme_baseline.png"
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(is_similar, "Dark theme visual regression detected")

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_light_theme_visual_consistency(self):
        """Test visual consistency of light theme"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get("http://localhost:8000/")

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Switch to light theme
        self.driver.execute_script("document.documentElement.className = 'light';")

        time.sleep(1)  # Wait for theme to apply

        # Capture full page screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, "light_theme_current.png"
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, "light_theme_baseline.png"
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(is_similar, "Light theme visual regression detected")


@pytest.mark.visual
@pytest.mark.responsive
class ResponsiveVisualTest(TestCase):
    """Visual regression tests for responsive design"""

    def setUp(self):
        """Set up Chrome driver for responsive testing"""
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
    def test_mobile_responsive_visual(self):
        """Test visual consistency on mobile viewport"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        # Set mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone dimensions

        self.driver.get("http://localhost:8000/")

        # Wait for page to load and responsive styles to apply
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        time.sleep(1)  # Wait for responsive styles

        # Capture mobile screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, "mobile_view_current.png"
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, "mobile_view_baseline.png"
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(is_similar, "Mobile responsive visual regression detected")

    @pytest.mark.skipif(
        not hasattr(TestCase(), "has_driver") or not TestCase().has_driver,
        reason="Chrome driver not available",
    )
    def test_tablet_responsive_visual(self):
        """Test visual consistency on tablet viewport"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        # Set tablet viewport
        self.driver.set_window_size(768, 1024)  # iPad dimensions

        self.driver.get("http://localhost:8000/")

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        time.sleep(1)

        # Capture tablet screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, "tablet_view_current.png"
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, "tablet_view_baseline.png"
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(is_similar, "Tablet responsive visual regression detected")


@pytest.mark.visual
@pytest.mark.ui
class Phase7UIEffectsVisualTest(TestCase):
    """Visual regression tests for Phase 7 UI effects"""

    def setUp(self):
        """Set up for Phase 7 visual testing"""
        self.client = Client()

    def test_glassmorphism_navigation_css_presence(self):
        """Test that glassmorphism navigation CSS is present and consistent"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for glassmorphism navigation properties
        glassmorphism_properties = [
            "backdrop-filter",
            "-webkit-backdrop-filter",
            "nav-container",
            "blur(",
            "saturate(",
        ]

        for prop in glassmorphism_properties:
            self.assertIn(
                prop, content, f"Glassmorphism property {prop} should be present"
            )

    def test_aurora_background_css_presence(self):
        """Test that aurora background CSS is present and consistent"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for aurora background properties
        aurora_properties = [
            "aurora-background",
            "gradient-mesh",
            "organic-blobs",
            "shimmer-overlay",
            "aurora-movement",
            "blob-movement",
        ]

        for prop in aurora_properties:
            self.assertIn(prop, content, f"Aurora property {prop} should be present")

    def test_parallax_system_css_presence(self):
        """Test that parallax system CSS is present and consistent"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for parallax system properties
        parallax_properties = [
            "parallax-container",
            "parallax-layer",
            "scroll-parallax",
            "parallax-aurora",
            "parallax-stars",
            "parallax-geometric",
            "will-change",
            "transform-style",
            "backface-visibility",
        ]

        for prop in parallax_properties:
            self.assertIn(prop, content, f"Parallax property {prop} should be present")

    def test_custom_cursor_css_presence(self):
        """Test that custom cursor CSS is present and consistent"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for custom cursor properties
        cursor_properties = [
            "custom-cursor",
            "cursor-particle",
            "cursor-trail",
            "cursor.hover",
            "cursor.click",
            "cursor.text",
            "cursor-ripple",
        ]

        for prop in cursor_properties:
            self.assertIn(prop, content, f"Cursor property {prop} should be present")

    def test_modern_typography_css_presence(self):
        """Test that modern typography CSS is present and consistent"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for typography properties
        typography_properties = [
            "heading-premium",
            "heading-2",
            "heading-3",
            "body-text",
            "body-small",
            "Inter",
            "--text-",
        ]

        for prop in typography_properties:
            self.assertIn(
                prop, content, f"Typography property {prop} should be present"
            )

    def test_homepage_phase7_integration(self):
        """Test that homepage integrates all Phase 7 features"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for Phase 7 integration in HTML
        phase7_features = [
            "nav-container",
            "parallax-container",
            "aurora-background",
            "gradient-mesh",
            "heading-premium",
            "heading-2",
            "parallax.js",
            "cursor.js",
            "animations.js",
        ]

        for feature in phase7_features:
            self.assertIn(
                feature, content, f"Phase 7 feature {feature} should be integrated"
            )

    def test_accessibility_features_presence(self):
        """Test that accessibility features are maintained in Phase 7"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for accessibility features
        accessibility_features = [
            "prefers-reduced-motion",
            "prefers-contrast",
            "hover: none",
            "pointer: coarse",
            "focus:",
            "aria-",
        ]

        for feature in accessibility_features:
            self.assertIn(
                feature, content, f"Accessibility feature {feature} should be present"
            )

    def test_performance_optimizations_presence(self):
        """Test that performance optimizations are maintained"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for performance optimizations
        performance_features = [
            "will-change",
            "transform3d",
            "translateZ",
            "backface-visibility",
            "transform-style",
            "gpu-accelerated",
        ]

        for feature in performance_features:
            self.assertIn(
                feature, content, f"Performance feature {feature} should be present"
            )


@pytest.mark.visual
@pytest.mark.ui
class Phase7VisualIntegrityTest(TestCase):
    """Test visual integrity of Phase 7 implementation"""

    def setUp(self):
        """Set up for visual integrity testing"""
        self.client = Client()

    def test_css_file_size_reasonable(self):
        """Test that CSS file size is reasonable after Phase 7 additions"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        # Check file size is reasonable (under 3MB for all features)
        content_length = len(response.content)
        self.assertLess(content_length, 3 * 1024 * 1024, "CSS file should be under 3MB")
        self.assertGreater(
            content_length, 100 * 1024, "CSS file should have substantial content"
        )

    def test_javascript_files_load_correctly(self):
        """Test that all Phase 7 JavaScript files load correctly"""
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

            # Check reasonable file size
            content_length = len(response.content)
            self.assertGreater(
                content_length, 1000, f"{js_file} should have substantial content"
            )

    def test_no_css_conflicts(self):
        """Test that there are no obvious CSS conflicts"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check that critical classes are not overridden
        critical_patterns = [
            ".nav-container",
            ".parallax-container",
            ".custom-cursor",
            ".aurora-background",
        ]

        for pattern in critical_patterns:
            # Count occurrences - should not be duplicated excessively
            count = content.count(pattern)
            self.assertGreater(count, 0, f"{pattern} should be present")
            self.assertLess(
                count, 10, f"{pattern} should not be excessively duplicated"
            )

    def test_theme_compatibility_maintained(self):
        """Test that theme switching still works with Phase 7"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for theme switching infrastructure
        theme_features = ["darkMode", "x-data", "dark:", "theme-toggle"]

        for feature in theme_features:
            self.assertIn(
                feature, content, f"Theme feature {feature} should be maintained"
            )

    def test_responsive_design_maintained(self):
        """Test that responsive design works with Phase 7 features"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for responsive utilities
        responsive_features = ["@media", "sm:", "md:", "lg:", "xl:"]

        for feature in responsive_features:
            self.assertIn(
                feature, content, f"Responsive feature {feature} should be maintained"
            )

    def test_fallback_support_present(self):
        """Test that fallbacks are present for Phase 7 features"""
        response = self.client.get("/static/css/output.css")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode("utf-8")

        # Check for fallback support
        fallback_features = [
            "-webkit-backdrop-filter",  # Webkit fallback
            "prefers-reduced-motion",  # Motion preference fallback
            "hover: none",  # Touch device fallback
            "@supports",  # Feature detection
        ]

        for feature in fallback_features:
            self.assertIn(
                feature, content, f"Fallback feature {feature} should be present"
            )


if __name__ == "__main__":
    pytest.main([__file__])
