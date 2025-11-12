"""
Main Views Module - Tüm View Fonksiyonlarının Merkezi İmportları
===============================================================================

Bu modül, apps/main uygulamasının tüm view fonksiyonlarını merkezi bir noktadan
export eder. Bu sayede import işlemleri basitleşir ve kod düzeni iyileşir.

MODÜL YAPISI:
- home_views.py: Ana sayfa görünümü
- info_views.py: Kişisel bilgiler ve müzik sayfaları
- tools_views.py: AI araçları, güvenlik ve faydalı kaynaklar
- auth_views.py: Kimlik doğrulama işlemleri
- search_views.py: Arama işlevselliği
- categories.py: Kategori görünümleri
- shorturl.py: Kısa URL yönlendirmeleri

KULLANIM:
    from apps.main.views import home, personal_view, ai_tools_view
    # veya
    from apps.main import views
    views.home(request)
"""

# Auth views
from .auth_views import logout_view

# Home views
from .home_views import home

# Info views
from .info_views import music_view, personal_view

# Main views (projects/portfolio)
from .main_views import project_detail_view, projects_view

# Tools views
from .tools_views import ai_tools_view, cybersecurity_view, useful_view

# Tüm viewları export et
__all__ = [
    # Home
    "home",
    # Info
    "personal_view",
    "music_view",
    # Tools
    "ai_tools_view",
    "cybersecurity_view",
    "useful_view",
    # Projects
    "projects_view",
    "project_detail_view",
    # Auth
    "logout_view",
]
