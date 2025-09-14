from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
import hashlib
import logging
from .models import ContactMessage
from .forms import ContactForm
from apps.main.analytics import analytics


def get_client_ip(request):
    """Get the client's IP address from request headers"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


@csrf_protect
@require_http_methods(["GET", "POST"])
def contact_form(request):
    """Enhanced contact form with proper validation and security"""
    logger = logging.getLogger(__name__)
    
    # Track page view
    analytics.track_page_view(request, request.path, 'Contact Form')
    
    if request.method == 'POST':
        # Track form submission attempt
        analytics.track_event(request, 'contact_form_submit_attempt')
        
        # Rate limiting: 5 requests per minute per IP
        client_ip = get_client_ip(request)
        cache_key = f"contact_rate_limit_{hashlib.md5(client_ip.encode()).hexdigest()}"
        request_count = cache.get(cache_key, 0)
        
        if request_count >= 5:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            analytics.track_event(request, 'contact_form_rate_limited')
            messages.error(request, 'Too many messages sent. Please wait a minute before trying again.')
            return render(request, 'contact/form.html', {'form': ContactForm()})
        
        # Process form with validation
        form = ContactForm(request.POST)
        
        if form.is_valid():
            try:
                # Increment rate limit counter
                cache.set(cache_key, request_count + 1, 60)  # 60 seconds
                
                # Save the validated and sanitized data
                contact_message = form.save()
                
                # Track successful form submission (conversion)
                analytics.track_conversion(request, 'contact_form_submission')
                analytics.track_event(request, 'contact_form_success')
                
                # Log successful submission (without sensitive data)
                logger.info(f"Contact message submitted successfully from IP: {client_ip}")
                
                # Send email notification (optional)
                try:
                    send_mail(
                        subject=f'New Contact Message: {contact_message.subject}',
                        message=f'From: {contact_message.name} <{contact_message.email}>\n\nMessage:\n{contact_message.message}',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[getattr(settings, 'CONTACT_EMAIL', 'admin@example.com')],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.warning(f"Failed to send contact email: {e}")
                
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('contact:success')
                
            except Exception as e:
                logger.error(f"Error saving contact message: {e}")
                messages.error(request, 'An error occurred while processing your message. Please try again.')
        else:
            # Track form validation failures
            analytics.track_event(request, 'contact_form_validation_failed', {'errors': len(form.errors)})
            
            # Log validation failures (without sensitive data)
            logger.info(f"Contact form validation failed from IP: {client_ip}")
            
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.title()}: {error}")
    else:
        form = ContactForm()
    
    return render(request, 'contact/form.html', {'form': form})


def contact_success(request):
    return render(request, 'contact/success.html')
