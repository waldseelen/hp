# Generated migration for Hobby model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_project'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hobby',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Hobi/İlgi Alanı')),
                ('category', models.CharField(choices=[('sports', 'Spor'), ('music', 'Müzik'), ('art', 'Sanat'), ('technology', 'Teknoloji'), ('reading', 'Okuma'), ('gaming', 'Oyun'), ('travel', 'Seyahat'), ('photography', 'Fotoğrafçılık'), ('cooking', 'Yemek'), ('fitness', 'Fitness'), ('learning', 'Öğrenme'), ('social', 'Sosyal'), ('creative', 'Yaratıcı'), ('outdoor', 'Doğa'), ('other', 'Diğer')], max_length=20, verbose_name='Kategori')),
                ('description', models.TextField(blank=True, verbose_name='Açıklama')),
                ('interest_level', models.IntegerField(choices=[(1, 'Az İlgili'), (2, 'İlgili'), (3, 'Çok İlgili'), (4, 'Tutkulu'), (5, 'Obsesif')], default=3, verbose_name='İlgi Seviyesi')),
                ('years_involved', models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, verbose_name='Kaç Yıldır')),
                ('frequency', models.CharField(blank=True, max_length=50, verbose_name='Sıklık (örn: Haftalık, Aylık)')),
                ('icon_class', models.CharField(blank=True, max_length=100, verbose_name='Icon CSS Sınıfı')),
                ('emoji', models.CharField(blank=True, max_length=10, verbose_name='Emoji')),
                ('color', models.CharField(default='#10B981', max_length=7, verbose_name='Renk (Hex)')),
                ('image', models.ImageField(blank=True, null=True, upload_to='hobbies/', verbose_name='Görsel')),
                ('achievements', models.TextField(blank=True, verbose_name='Başarılar/Deneyimler')),
                ('website_url', models.URLField(blank=True, verbose_name='İlgili Website')),
                ('social_media_links', models.JSONField(blank=True, default=dict, verbose_name='Sosyal Medya Linkleri')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktif mi?')),
                ('current_focus', models.CharField(blank=True, max_length=200, verbose_name='Şu Anki Odak')),
                ('is_featured', models.BooleanField(default=False, verbose_name='Öne Çıkarılsın mı?')),
                ('is_visible', models.BooleanField(default=True, verbose_name='Görünür mü?')),
                ('order', models.IntegerField(default=0, verbose_name='Sıralama')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma Tarihi')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Güncellenme Tarihi')),
                ('related_projects', models.ManyToManyField(blank=True, to='main.project', verbose_name='İlgili Projeler')),
            ],
            options={
                'verbose_name': 'Hobi/İlgi Alanı',
                'verbose_name_plural': 'Hobiler/İlgi Alanları',
                'ordering': ['-is_featured', 'category', 'order', 'name'],
            },
        ),
    ]
