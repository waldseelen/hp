#!/usr/bin/env python
"""
Simple security verification tests
"""
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings.development')
django.setup()

from apps.contact.forms import ContactForm
from apps.main.file_validators import FileTypeValidator, SecureFileValidator
from apps.main.api_views import validate_performance_data, validate_notification_data
from django.core.files.uploadedfile import SimpleUploadedFile


def test_contact_form():
    print("Testing Contact Form...")
    
    # Test valid data
    valid_data = {
        'name': 'John Doe',
        'email': 'john@example.com', 
        'subject': 'Test Subject',
        'message': 'This is a valid test message.',
        'website': ''
    }
    
    form = ContactForm(data=valid_data)
    if form.is_valid():
        print("PASS: Valid form accepted")
    else:
        print(f"FAIL: Valid form rejected: {form.errors}")
        return False
    
    # Test XSS prevention
    xss_data = valid_data.copy()
    xss_data['name'] = '<script>alert("xss")</script>Hacker'
    xss_data['message'] = 'Message with <script>evil()</script> code'
    
    form = ContactForm(data=xss_data)
    if form.is_valid():
        clean_data = form.cleaned_data
        if '<script>' not in clean_data['name'] and '<script>' not in clean_data['message']:
            print("PASS: XSS content sanitized")
        else:
            print("FAIL: XSS not properly sanitized")
            return False
    else:
        print("PASS: XSS form rejected")
    
    # Test honeypot spam detection
    spam_data = valid_data.copy()
    spam_data['website'] = 'http://spam.com'
    
    form = ContactForm(data=spam_data)
    if not form.is_valid():
        print("PASS: Honeypot spam detection working")
    else:
        print("FAIL: Honeypot failed to detect spam")
        return False
    
    return True


def test_file_security():
    print("Testing File Security...")
    
    # Test valid image (minimal PNG)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x007n\xf9$\x00\x00\x00\nIDAT\x08\x1dc\xf8\x00\x00\x00\x01\x00\x01s\x93\x00\x00\x00\x00IEND\xaeB`\x82'
    
    valid_file = SimpleUploadedFile("test.png", png_data, content_type="image/png")
    
    try:
        validator = FileTypeValidator()
        validator(valid_file)
        print("PASS: Valid PNG file accepted")
    except Exception as e:
        print(f"FAIL: Valid PNG rejected: {e}")
        return False
    
    # Test executable rejection
    exe_data = b'MZ\x90\x00'  # PE header
    exe_file = SimpleUploadedFile("virus.exe", exe_data, content_type="application/octet-stream")
    
    try:
        validator = SecureFileValidator()
        validator(exe_file)
        print("FAIL: Executable file was accepted!")
        return False
    except Exception as e:
        print("PASS: Executable file rejected")
    
    # Test double extension
    double_ext_file = SimpleUploadedFile("image.jpg.exe", b"fake", content_type="image/jpeg")
    
    try:
        validator = SecureFileValidator()
        validator(double_ext_file)
        print("FAIL: Double extension file accepted!")
        return False
    except Exception as e:
        print("PASS: Double extension attack prevented")
    
    return True


def test_api_validation():
    print("Testing API Validation...")
    
    # Test valid performance data
    valid_data = {
        'metric_type': 'lcp',
        'value': 1500.5,
        'url': 'https://example.com'
    }
    
    result = validate_performance_data(valid_data)
    if 'error' not in result:
        print("PASS: Valid performance data accepted")
    else:
        print(f"FAIL: Valid data rejected: {result['error']}")
        return False
    
    # Test invalid metric
    invalid_data = {
        'metric_type': 'invalid_metric',
        'value': 1500
    }
    
    result = validate_performance_data(invalid_data)
    if 'error' in result:
        print("PASS: Invalid metric type rejected")
    else:
        print("FAIL: Invalid metric type accepted")
        return False
    
    # Test XSS in URL
    xss_data = {
        'metric_type': 'lcp',
        'value': 1500,
        'url': 'javascript:alert("xss")'
    }
    
    result = validate_performance_data(xss_data)
    if 'error' in result:
        print("PASS: XSS URL rejected")
    else:
        print("FAIL: XSS URL accepted")
        return False
    
    # Test notification validation
    valid_notification = {
        'topics': ['blog_posts'],
        'title': 'Test Title',
        'message': 'Test message'
    }
    
    result = validate_notification_data(valid_notification)
    if 'error' not in result:
        print("PASS: Valid notification data accepted")
    else:
        print(f"FAIL: Valid notification rejected: {result['error']}")
        return False
    
    return True


def main():
    print("SECURITY VERIFICATION TESTS")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 3
    
    if test_contact_form():
        tests_passed += 1
    print()
    
    if test_file_security():
        tests_passed += 1
    print()
    
    if test_api_validation():
        tests_passed += 1
    print()
    
    print("=" * 40)
    if tests_passed == total_tests:
        print(f"SUCCESS: All {total_tests} test groups passed!")
        print("Security implementation verified and working correctly.")
        return True
    else:
        print(f"PARTIAL: {tests_passed}/{total_tests} test groups passed.")
        print("Some security features may need attention.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)