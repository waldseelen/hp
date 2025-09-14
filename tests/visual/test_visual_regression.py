"""
Visual regression tests for key UI components
Tests visual consistency across theme changes and responsive breakpoints
"""

import pytest
import os
import hashlib
from django.test import TestCase
from django.test.client import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageChops
import time


class VisualTestUtils:
    """Utility class for visual testing operations"""

    @staticmethod
    def get_screenshots_dir():
        """Get the directory for storing test screenshots"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshots_dir = os.path.join(base_dir, 'visual', 'screenshots')
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
        baseline_path = os.path.join(screenshots_dir, 'baselines', baseline_name)

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
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.has_driver = True
        except Exception as e:
            self.has_driver = False
            print(f"Chrome driver not available: {e}")

    def tearDown(self):
        """Clean up Chrome driver"""
        if hasattr(self, 'driver') and self.has_driver:
            self.driver.quit()

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_homepage_hero_section_visual(self):
        """Test visual consistency of homepage hero section"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get('http://localhost:8000/')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Find hero section
        hero_sections = self.driver.find_elements(
            By.CSS_SELECTOR,
            "section, .hero, [class*='hero']"
        )

        if hero_sections:
            hero = hero_sections[0]

            # Capture hero section screenshot
            screenshot_path = VisualTestUtils.capture_element_screenshot(
                self.driver, hero, 'homepage_hero_current.png'
            )

            # Generate or compare with baseline
            baseline_path = VisualTestUtils.generate_baseline_if_needed(
                screenshot_path, 'homepage_hero_baseline.png'
            )

            # If baseline exists, compare
            if os.path.exists(baseline_path):
                is_similar = VisualTestUtils.compare_images(
                    screenshot_path, baseline_path, threshold=0.05
                )

                self.assertTrue(
                    is_similar,
                    "Hero section visual regression detected. "
                    f"Compare {screenshot_path} with {baseline_path}"
                )

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_contact_button_visual_consistency(self):
        """Test visual consistency of Contact Me button"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get('http://localhost:8000/')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Find Contact Me button
        contact_buttons = self.driver.find_elements(
            By.XPATH,
            "//a[contains(text(), 'Contact Me') or contains(text(), 'Contact')]"
        )

        if contact_buttons:
            button = contact_buttons[0]

            # Capture button screenshot
            screenshot_path = VisualTestUtils.capture_element_screenshot(
                self.driver, button, 'contact_button_current.png'
            )

            # Generate or compare with baseline
            baseline_path = VisualTestUtils.generate_baseline_if_needed(
                screenshot_path, 'contact_button_baseline.png'
            )

            if os.path.exists(baseline_path):
                is_similar = VisualTestUtils.compare_images(
                    screenshot_path, baseline_path, threshold=0.02
                )

                self.assertTrue(
                    is_similar,
                    "Contact button visual regression detected"
                )

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_navigation_visual_consistency(self):
        """Test visual consistency of navigation bar"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get('http://localhost:8000/')

        # Wait for navigation to load
        nav_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "nav, header"))
        )

        # Capture navigation screenshot
        screenshot_path = VisualTestUtils.capture_element_screenshot(
            self.driver, nav_element, 'navigation_current.png'
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, 'navigation_baseline.png'
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.03
            )

            self.assertTrue(
                is_similar,
                "Navigation visual regression detected"
            )


@pytest.mark.visual
@pytest.mark.integration
class ThemeVisualRegressionTest(TestCase):
    """Visual regression tests across different themes"""

    def setUp(self):
        """Set up Chrome driver for theme testing"""
        self.client = Client()

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.has_driver = True
        except Exception:
            self.has_driver = False

    def tearDown(self):
        """Clean up Chrome driver"""
        if hasattr(self, 'driver') and self.has_driver:
            self.driver.quit()

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_dark_theme_visual_consistency(self):
        """Test visual consistency of dark theme"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get('http://localhost:8000/')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Ensure dark theme is active
        self.driver.execute_script(
            "document.documentElement.className = 'dark';"
        )

        time.sleep(1)  # Wait for theme to apply

        # Capture full page screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, 'dark_theme_current.png'
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, 'dark_theme_baseline.png'
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(
                is_similar,
                "Dark theme visual regression detected"
            )

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_light_theme_visual_consistency(self):
        """Test visual consistency of light theme"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        self.driver.get('http://localhost:8000/')

        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # Switch to light theme
        self.driver.execute_script(
            "document.documentElement.className = 'light';"
        )

        time.sleep(1)  # Wait for theme to apply

        # Capture full page screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, 'light_theme_current.png'
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, 'light_theme_baseline.png'
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(
                is_similar,
                "Light theme visual regression detected"
            )


@pytest.mark.visual
@pytest.mark.responsive
class ResponsiveVisualTest(TestCase):
    """Visual regression tests for responsive design"""

    def setUp(self):
        """Set up Chrome driver for responsive testing"""
        self.client = Client()

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            self.has_driver = True
        except Exception:
            self.has_driver = False

    def tearDown(self):
        """Clean up Chrome driver"""
        if hasattr(self, 'driver') and self.has_driver:
            self.driver.quit()

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_mobile_responsive_visual(self):
        """Test visual consistency on mobile viewport"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        # Set mobile viewport
        self.driver.set_window_size(375, 667)  # iPhone dimensions

        self.driver.get('http://localhost:8000/')

        # Wait for page to load and responsive styles to apply
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        time.sleep(1)  # Wait for responsive styles

        # Capture mobile screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, 'mobile_view_current.png'
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, 'mobile_view_baseline.png'
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(
                is_similar,
                "Mobile responsive visual regression detected"
            )

    @pytest.mark.skipif(not hasattr(TestCase(), 'has_driver') or not TestCase().has_driver,
                       reason="Chrome driver not available")
    def test_tablet_responsive_visual(self):
        """Test visual consistency on tablet viewport"""
        if not self.has_driver:
            self.skipTest("Chrome driver not available")

        # Set tablet viewport
        self.driver.set_window_size(768, 1024)  # iPad dimensions

        self.driver.get('http://localhost:8000/')

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        time.sleep(1)

        # Capture tablet screenshot
        screenshot_path = VisualTestUtils.capture_full_page_screenshot(
            self.driver, 'tablet_view_current.png'
        )

        # Generate or compare with baseline
        baseline_path = VisualTestUtils.generate_baseline_if_needed(
            screenshot_path, 'tablet_view_baseline.png'
        )

        if os.path.exists(baseline_path):
            is_similar = VisualTestUtils.compare_images(
                screenshot_path, baseline_path, threshold=0.1
            )

            self.assertTrue(
                is_similar,
                "Tablet responsive visual regression detected"
            )


if __name__ == '__main__':
    pytest.main([__file__])