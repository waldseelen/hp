"""
AUTH VIEWS - Kimlik Doğrulama İşlemleri
===============================================================================

Bu modül, kimlik doğrulama ile ilgili görünüm mantıklarını içerir.

TANIMLI GÖRÜNÜMLER:
- logout_view(): Çıkış işlemi yönetimi
"""

import logging

from django.contrib.auth import logout
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def logout_view(request):
    """
    Logout view with proper cleanup.
    """
    try:
        logout(request)
        return redirect("admin:login")
    except Exception as e:
        logger.error(f"Error in logout view: {str(e)}")
        return redirect("admin:login")
