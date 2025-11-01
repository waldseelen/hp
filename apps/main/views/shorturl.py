import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from ..models import ShortURL


def redirect_short_url(request, short_code):
    """Redirect short URL to original URL"""
    short_url = get_object_or_404(ShortURL, short_code=short_code, is_active=True)

    # Check if expired
    if short_url.is_expired():
        raise Http404("Bu kısa URL'in süresi dolmuş.")

    # Check if password protected
    if short_url.password:
        password = request.GET.get("p") or request.POST.get("password")
        if password != short_url.password:
            return render(request, "shorturl/password.html", {"short_url": short_url})

    # Log the click
    short_url.increment_clicks()

    # TODO: Track click details (IP, user agent, referer) in URLClick model
    # This would require creating a URLClick model with foreign key to ShortURL

    return redirect(short_url.original_url)


@staff_member_required
def shorturl_create(request):
    """Create a new short URL"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            original_url = data.get("url")
            title = data.get("title", "")
            description = data.get("description", "")
            password = data.get("password", "")
            expires_at = data.get("expires_at")

            if not original_url:
                return JsonResponse({"error": "URL gerekli"}, status=400)

            # Parse expires_at if provided
            if expires_at:
                from datetime import datetime

                expires_at = datetime.fromisoformat(expires_at)

            short_url = ShortURL.objects.create(
                original_url=original_url,
                title=title,
                description=description,
                password=password,
                expires_at=expires_at,
                created_by=request.user,
            )

            return JsonResponse(
                {
                    "success": True,
                    "short_code": short_url.short_code,
                    "short_url": short_url.get_short_url(),
                    "original_url": short_url.original_url,
                }
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, "shorturl/create.html")


@staff_member_required
def shorturl_list(request):
    """List all short URLs"""
    short_urls = ShortURL.objects.all()
    return render(request, "shorturl/list.html", {"short_urls": short_urls})


@staff_member_required
def shorturl_detail(request, short_code):
    """View short URL details and analytics"""
    short_url = get_object_or_404(ShortURL, short_code=short_code)

    return render(request, "shorturl/detail.html", {"short_url": short_url})


@staff_member_required
def shorturl_delete(request, short_code):
    """Delete a short URL"""
    short_url = get_object_or_404(ShortURL, short_code=short_code)

    if request.method == "POST":
        short_url.delete()
        messages.success(request, f'Kısa URL "{short_code}" silindi.')
        return redirect("main:shorturl_list")

    return render(request, "shorturl/delete.html", {"short_url": short_url})


def get_client_ip(request):
    """Get the client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


@csrf_exempt
def shorturl_api(request):
    """API endpoint for creating short URLs"""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    if not request.user.is_staff:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        data = json.loads(request.body)
        original_url = data.get("url")

        if not original_url:
            return JsonResponse({"error": "URL required"}, status=400)

        # Check if URL already exists
        existing = ShortURL.objects.filter(
            original_url=original_url, is_active=True
        ).first()

        if existing:
            return JsonResponse(
                {
                    "short_code": existing.short_code,
                    "short_url": existing.get_short_url(),
                    "original_url": existing.original_url,
                    "exists": True,
                }
            )

        # Create new short URL
        short_url = ShortURL.objects.create(
            original_url=original_url,
            title=data.get("title", ""),
            created_by=request.user,
        )

        return JsonResponse(
            {
                "short_code": short_url.short_code,
                "short_url": short_url.get_short_url(),
                "original_url": short_url.original_url,
                "exists": False,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
