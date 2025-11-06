"""
Unit tests for Portfolio Content Models - Part 2.

Tests cover:
- BlogCategory (6 categories, color/icon management)
- BlogPost (status workflow, slug generation, reading time)
- MusicPlaylist (Spotify embed auto-generation)
- SpotifyCurrentTrack (real-time playback tracking)
- UsefulResource (5 types, 8 categories, ratings)

Target: 18 comprehensive tests for extended content features.
"""

from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.utils import timezone

import pytest

from apps.portfolio.models import (
    Admin,
    BlogCategory,
    BlogPost,
    MusicPlaylist,
    SpotifyCurrentTrack,
    UsefulResource,
)

# ============================================================================
# BLOGCATEGORY MODEL TESTS (6 Categories, Color/Icon)
# ============================================================================


@pytest.mark.django_db
class TestBlogCategoryModel:
    """Test BlogCategory model - categories, styling, ordering."""

    def test_blogcategory_creation(self):
        """Test basic BlogCategory creation."""
        category = BlogCategory.objects.create(
            name="philosophy",
            display_name="Felsefe",
            description="Philosophical discussions",
            color="#FF5733",
        )
        assert category.name == "philosophy"
        assert category.display_name == "Felsefe"
        assert category.color == "#FF5733"
        assert category.is_visible

    def test_blogcategory_all_categories(self):
        """Test all 6 blog categories."""
        categories = [
            ("philosophy", "Felsefe"),
            ("history", "Tarih"),
            ("sociology", "Sosyoloji"),
            ("technology", "Teknoloji"),
            ("personal", "Kişisel"),
            ("other", "Diğer"),
        ]
        for name, display in categories:
            cat = BlogCategory.objects.create(
                name=name,
                display_name=display,
            )
            assert cat.name == name
            assert cat.display_name == display

    def test_blogcategory_default_color(self):
        """Test default category color."""
        category = BlogCategory.objects.create(
            name="technology",
            display_name="Teknoloji",
        )
        assert category.color == "#3B82F6"  # Default blue

    def test_blogcategory_ordering(self):
        """Test category ordering by order field."""
        BlogCategory.objects.create(name="philosophy", display_name="C", order=3)
        BlogCategory.objects.create(name="history", display_name="A", order=1)
        BlogCategory.objects.create(name="sociology", display_name="B", order=2)

        ordered = list(BlogCategory.objects.all())
        assert ordered[0].display_name == "A"
        assert ordered[1].display_name == "B"
        assert ordered[2].display_name == "C"


# ============================================================================
# BLOGPOST MODEL TESTS (Status Workflow, Slug, Reading Time)
# ============================================================================


@pytest.mark.django_db
class TestBlogPostModel:
    """Test BlogPost model - status workflow, auto-fields."""

    @pytest.fixture
    def author(self):
        """Create author for blog posts."""
        return Admin.objects.create_user(
            username="blog_author",
            email="author@example.com",
            name="Blog Author",
            password="pass",
        )

    @pytest.fixture
    def category(self):
        """Create category for blog posts."""
        return BlogCategory.objects.create(
            name="technology",
            display_name="Teknoloji",
        )

    def test_blogpost_creation_draft(self, author, category):
        """Test BlogPost creation with draft status."""
        post = BlogPost.objects.create(
            title="Test Post",
            category=category,
            excerpt="Test excerpt",
            content="Test content",
            author=author,
        )
        assert post.status == "draft"
        assert post.published_at is None
        assert post.view_count == 0

    def test_blogpost_slug_auto_generation(self, author, category):
        """Test automatic slug generation from title."""
        post = BlogPost.objects.create(
            title="My Test Blog Post",
            category=category,
            excerpt="Excerpt",
            content="Content",
            author=author,
        )
        assert post.slug  # Should be auto-generated
        assert "test" in post.slug.lower()

    def test_blogpost_reading_time_calculation(self, author, category):
        """Test reading time calculation (200 words/min)."""
        # Create 400-word content (should be 2 minutes)
        content = " ".join(["word"] * 400)
        post = BlogPost.objects.create(
            title="Long Post",
            category=category,
            excerpt="Long",
            content=content,
            author=author,
        )
        assert post.reading_time == 2  # 400 words / 200 wpm = 2 min

    def test_blogpost_status_workflow(self, author, category):
        """Test status transitions: draft → published → archived."""
        post = BlogPost.objects.create(
            title="Workflow Test",
            category=category,
            excerpt="Test",
            content="Test",
            author=author,
        )
        assert post.status == "draft"

        # Publish
        post.status = "published"
        post.save()
        assert post.status == "published"

        # Archive
        post.status = "archived"
        post.save()
        assert post.status == "archived"


# ============================================================================
# MUSICPLAYLIST MODEL TESTS (Spotify Embed Auto-Generation)
# ============================================================================


@pytest.mark.django_db
class TestMusicPlaylistModel:
    """Test MusicPlaylist model - platform support, Spotify embed."""

    def test_musicplaylist_creation(self):
        """Test basic MusicPlaylist creation."""
        playlist = MusicPlaylist.objects.create(
            name="Coding Music",
            description="Music for coding sessions",
            platform="spotify",
            url="https://open.spotify.com/playlist/abc123",
        )
        assert playlist.name == "Coding Music"
        assert playlist.platform == "spotify"
        assert playlist.is_visible

    def test_musicplaylist_spotify_embed_auto_generation(self):
        """Test automatic Spotify embed URL generation."""
        playlist = MusicPlaylist.objects.create(
            name="Test Playlist",
            platform="spotify",
            url="https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M?si=abc",
        )
        assert playlist.embed_url  # Should be auto-generated
        assert "embed" in playlist.embed_url
        assert "37i9dQZF1DXcBWIGoYBM5M" in playlist.embed_url

    def test_musicplaylist_non_spotify_no_embed(self):
        """Test no embed URL for non-Spotify platforms."""
        playlist = MusicPlaylist.objects.create(
            name="YouTube Playlist",
            platform="youtube",
            url="https://youtube.com/playlist?list=xyz",
        )
        assert not playlist.embed_url

    def test_musicplaylist_ordering(self):
        """Test playlist ordering by order field."""
        MusicPlaylist.objects.create(
            name="C", platform="spotify", url="https://c.com", order=3
        )
        MusicPlaylist.objects.create(
            name="A", platform="spotify", url="https://a.com", order=1
        )
        MusicPlaylist.objects.create(
            name="B", platform="spotify", url="https://b.com", order=2
        )

        ordered = list(MusicPlaylist.objects.all())
        assert ordered[0].name == "A"
        assert ordered[1].name == "B"
        assert ordered[2].name == "C"


# ============================================================================
# SPOTIFYCURRENTTRACK MODEL TESTS (Real-Time Playback)
# ============================================================================


@pytest.mark.django_db
class TestSpotifyCurrentTrackModel:
    """Test SpotifyCurrentTrack model - real-time playback tracking."""

    def test_spotify_track_creation(self):
        """Test SpotifyCurrentTrack creation."""
        track = SpotifyCurrentTrack.objects.create(
            track_name="Bohemian Rhapsody",
            artist_name="Queen",
            album_name="A Night at the Opera",
            track_url="https://open.spotify.com/track/abc",
            is_playing=True,
            duration_ms=354000,
        )
        assert track.track_name == "Bohemian Rhapsody"
        assert track.artist_name == "Queen"
        assert track.is_playing

    def test_spotify_track_playback_progress(self):
        """Test playback progress tracking."""
        track = SpotifyCurrentTrack.objects.create(
            track_name="Test Track",
            artist_name="Test Artist",
            is_playing=True,
            progress_ms=120000,  # 2 minutes
            duration_ms=240000,  # 4 minutes total
        )
        assert track.progress_ms == 120000
        assert track.duration_ms == 240000

    def test_spotify_track_string_representation(self):
        """Test track __str__ method."""
        track = SpotifyCurrentTrack.objects.create(
            track_name="Test Track",
            artist_name="Test Artist",
        )
        str_repr = str(track)
        assert "Test Track" in str_repr
        assert "Test Artist" in str_repr


# ============================================================================
# USEFULRESOURCE MODEL TESTS (5 Types, 8 Categories)
# ============================================================================


@pytest.mark.django_db
class TestUsefulResourceModel:
    """Test UsefulResource model - types, categories, ratings."""

    def test_usefulresource_creation(self):
        """Test basic UsefulResource creation."""
        resource = UsefulResource.objects.create(
            name="VS Code",
            description="Code editor",
            url="https://code.visualstudio.com",
            type="app",
            category="development",
        )
        assert resource.name == "VS Code"
        assert resource.type == "app"
        assert resource.category == "development"
        assert resource.is_free

    def test_usefulresource_all_types(self):
        """Test all 5 resource types."""
        types = ["website", "app", "tool", "extension", "other"]
        for res_type in types:
            resource = UsefulResource.objects.create(
                name=f"Test {res_type}",
                description="Test",
                url=f"https://{res_type}.com",
                type=res_type,
            )
            assert resource.type == res_type

    def test_usefulresource_all_categories(self):
        """Test all 8 resource categories."""
        categories = [
            "development",
            "design",
            "productivity",
            "ai",
            "learning",
            "entertainment",
            "utility",
            "other",
        ]
        for cat in categories:
            resource = UsefulResource.objects.create(
                name=f"Test {cat}",
                description="Test",
                url=f"https://{cat}.com",
                category=cat,
            )
            assert resource.category == cat

    def test_usefulresource_rating_system(self):
        """Test rating system (0-5 scale)."""
        resource = UsefulResource.objects.create(
            name="Highly Rated",
            description="Great resource",
            url="https://example.com",
            rating=4.5,
        )
        assert resource.rating == 4.5

    def test_usefulresource_free_vs_paid(self):
        """Test free vs paid resource distinction."""
        free = UsefulResource.objects.create(
            name="Free Resource",
            description="Free",
            url="https://free.com",
            is_free=True,
        )
        paid = UsefulResource.objects.create(
            name="Paid Resource",
            description="Paid",
            url="https://paid.com",
            is_free=False,
        )
        assert free.is_free
        assert not paid.is_free

    def test_usefulresource_featured_flag(self):
        """Test featured resource functionality."""
        resource = UsefulResource.objects.create(
            name="Featured",
            description="Featured resource",
            url="https://example.com",
            is_featured=True,
        )
        assert resource.is_featured

    def test_usefulresource_ordering(self):
        """Test resource ordering by category, order, name."""
        UsefulResource.objects.create(
            name="B",
            description="Test",
            url="https://b.com",
            category="design",
            order=2,
        )
        UsefulResource.objects.create(
            name="A",
            description="Test",
            url="https://a.com",
            category="design",
            order=1,
        )
        UsefulResource.objects.create(
            name="Z",
            description="Test",
            url="https://z.com",
            category="development",
            order=1,
        )

        ordered = list(UsefulResource.objects.all())
        # Should be ordered by category, then order, then name
        assert ordered[0].name == "A"  # design, order=1
        assert ordered[1].name == "B"  # design, order=2
        assert ordered[2].name == "Z"  # development, order=1
