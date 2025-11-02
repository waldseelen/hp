"""
INFO VIEWS - Kişisel Bilgi ve Müzik Görünüm Mantıkları
===============================================================================

Bu modül, kişisel bilgiler (hakkımda) ve müzik sayfalarının görünüm mantıklarını içerir.

TANIMLI GÖRÜNÜMLER:
- personal_view(): Hakkımda sayfası - kişisel bilgiler, sosyal bağlantılar
- music_view(): Müzik sayfası - playlistler, şu an çalan müzik

CACHE STRATEJISI:
- Kişisel sayfa: 15 dakika (900 saniye)
- Müzik sayfası: 5 dakika (300 saniye - dinamik içerik)
"""

import logging

from django.core.cache import cache
from django.shortcuts import render

from ..models import MusicPlaylist, PersonalInfo, SocialLink, SpotifyCurrentTrack

logger = logging.getLogger(__name__)


def personal_view(request):
    """
    About/Personal page view with personal information.
    """
    try:
        cache_key = "personal_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            personal_info = PersonalInfo.objects.filter(
                is_visible=True,
                key__in=["about", "skills", "experience", "education", "bio"],
            ).order_by("order", "key")

            social_links = SocialLink.objects.filter(is_visible=True).order_by(
                "order", "platform"
            )

            cached_data = {
                "personal_info": list(personal_info),
                "social_links": list(social_links),
            }

            cache.set(cache_key, cached_data, 900)

        context = {
            "personal_info": cached_data["personal_info"],
            "social_links": cached_data["social_links"],
            "page_title": "Hakkımda",
            "meta_description": "Kişisel bilgiler, yetenekler ve deneyimler",
        }

        return render(request, "pages/portfolio/personal.html", context)

    except Exception as e:
        logger.error(f"Error in personal view: {str(e)}")
        context = {
            "personal_info": [],
            "social_links": [],
            "page_title": "Hakkımda",
            "meta_description": "Kişisel bilgiler",
        }
        return render(request, "pages/portfolio/personal.html", context)


def music_view(request):
    """
    Music page view with playlists and current track.
    """
    try:
        cache_key = "music_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Get visible playlists
            playlists = MusicPlaylist.objects.filter(is_visible=True).order_by(
                "order", "name"
            )

            # Get featured playlists
            featured_playlists = playlists.filter(is_featured=True)[:3]

            # Get current Spotify track if available
            current_track = SpotifyCurrentTrack.objects.first()

            cached_data = {
                "playlists": list(playlists),
                "featured_playlists": list(featured_playlists),
                "current_track": current_track,
            }

            cache.set(cache_key, cached_data, 300)  # 5 minutes cache

        context = {
            "playlists": cached_data["playlists"],
            "featured_playlists": cached_data["featured_playlists"],
            "current_track": cached_data["current_track"],
            "page_title": "Müzik",
            "meta_description": "Müzik playlistleri, şu an çaldığım şarkılar ve favori sanatçılar",
        }

        return render(request, "pages/portfolio/music.html", context)

    except Exception as e:
        logger.error(f"Error in music view: {str(e)}")
        context = {
            "playlists": [],
            "featured_playlists": [],
            "current_track": None,
            "page_title": "Müzik",
            "meta_description": "Müzik",
        }
        return render(request, "pages/portfolio/music.html", context)
