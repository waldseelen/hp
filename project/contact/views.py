import hashlib

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .models import ContactMessage


def get_client_ip(request):
    """Get the client's IP address from request headers"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def contact_form(request):
    if request.method == "POST":
        # Simple rate limiting: 5 requests per minute per IP
        client_ip = get_client_ip(request)
        cache_key = f"contact_rate_limit_{hashlib.md5(client_ip.encode()).hexdigest()}"
        request_count = cache.get(cache_key, 0)

        if request_count >= 5:
            messages.error(
                request, "Çok fazla mesaj gönderdiniz. Lütfen bir dakika bekleyin."
            )
            return render(request, "contact/form.html")

        # Increment counter
        cache.set(cache_key, request_count + 1, 60)  # 60 seconds
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        website = request.POST.get("website")  # Honeypot field

        # Check honeypot field - if filled, it's likely spam
        if website:
            messages.error(request, "Geçersiz form gönderimi.")
            return redirect("contact:form")

        if name and email and subject and message:
            # Save to database
            contact_message = ContactMessage.objects.create(
                name=name, email=email, subject=subject, message=message
            )

            # Send email notification (optional)
            try:
                send_mail(
                    subject=f"Yeni İletişim Mesajı: {subject}",
                    message=f"Gönderen: {name} <{email}>\n\nMesaj:\n{message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=["bugraakin01@gmail.com"],
                    fail_silently=True,
                )
            except:
                pass  # Email sending is optional

            messages.success(request, "Mesajınız başarıyla gönderildi!")
            return redirect("contact:success")
        else:
            messages.error(request, "Lütfen tüm gerekli alanları doldurun.")

    return render(request, "contact/form.html")


def contact_success(request):
    return render(request, "contact/success.html")
