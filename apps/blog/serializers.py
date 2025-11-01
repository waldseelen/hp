"""
BLOG SERIALIZERS - BLOG API SERİALİZATION (Blog REST API Veri Dönüştürücüleri)
===============================================================================

Bu dosya, blog sisteminin REST API endpoint'leri için veri serialization
işlemlerini yönetir. Django model verilerinin JSON formatına dönüştürülmesi
ve API response'larının oluşturulması sağlanır.

TANIMLI SERİALİZER SINIFLARI:
- PostSerializer: Blog yazıları için tam serialization (detay görünümleri)
- PostListSerializer: Blog yazıları için hafif serialization (liste görünümleri)
- BlogSeriesSerializer: Blog serileri için serialization

POSTSERIALIZER ÖZELLİKLERİ:
- Tam alan serializasyonu (content, excerpt, tags vb.)
- author_name: Yazar kullanıcı adını ekler (read-only)
- category_display: Kategori görüntü adını ekler (read-only)
- reading_time: Okuma süresi hesaplama (SerializerMethodField)
- Read-only alanlar: author, created_at, updated_at, views

POSTLISTSERIALIZER ÖZELLİKLERİ:
- Performans odaklı hafif serialization
- Liste görünümleri için optimize edilmiş alan seçimi
- Content alanı dahil edilmez (boyut optimizasyonu)
- Temel bilgiler ve meta veriler

BLOGSERIESSERIALIZER ÖZELLİKLERİ:
- Seri temel bilgileri
- post_count: Serideki yazı sayısı hesaplama
- İlişkili yazı sayısı dinamik hesaplama

CUSTOM METHODLAR:
- get_reading_time(): Okuma süresi hesaplama algoritması
  * İçerik kelime sayısı / 200 (ortalama okuma hızı)
  * Minimum 1 dakika garantisi
- get_post_count(): Seri yazı sayısı hesaplama

API KULLANIM DURUMLARI:
- Blog yazıları listeleme (PostListSerializer)
- Blog yazı detayları (PostSerializer)
- Blog serileri API (BlogSeriesSerializer)
- JSON export/import işlemleri
- Frontend framework entegrasyonu

İLİŞKİLER VE BAĞIMLILIKLAR:
- blog.models: Post, BlogSeries modelleri
- Django REST Framework: ModelSerializer inheritance
- blog.views: API ViewSet'lerde kullanım
- Frontend: React/Vue.js vb. framework'ler için JSON data
"""

from rest_framework import serializers

from .models import BlogSeries, Post


class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.username", read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    reading_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "excerpt",
            "featured_image",
            "category",
            "category_display",
            "tags",
            "author",
            "author_name",
            "created_at",
            "updated_at",
            "status",
            "reading_time",
            "views",
        ]
        read_only_fields = ["author", "created_at", "updated_at", "views"]

    def get_reading_time(self, obj):
        """Calculate estimated reading time based on content length"""
        if obj.content:
            word_count = len(obj.content.split())
            # Average reading speed: 200 words per minute
            reading_time = max(1, round(word_count / 200))
            return reading_time
        return 1


class BlogSeriesSerializer(serializers.ModelSerializer):
    post_count = serializers.SerializerMethodField()

    class Meta:
        model = BlogSeries
        fields = ["id", "name", "description", "post_count"]

    def get_post_count(self, obj):
        return obj.post_set.count()


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""

    author_name = serializers.CharField(source="author.username", read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    reading_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "featured_image",
            "category",
            "category_display",
            "author_name",
            "created_at",
            "reading_time",
            "views",
        ]

    def get_reading_time(self, obj):
        if obj.content:
            word_count = len(obj.content.split())
            reading_time = max(1, round(word_count / 200))
            return reading_time
        return 1
