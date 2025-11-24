# Google Cloud Deployment Guide

Bu rehber, Django portfolio uygulamanızı Google Cloud'a deploy etmek için gerekli tüm adımları içerir.

## Ön Koşullar

1. **Google Cloud hesabı** (ücretsiz $300 kredi)
2. **Google Cloud CLI (gcloud)** kurulumu
3. **Docker** kurulumu (opsiyonel, local test için)
4. **PostgreSQL** veritabanı (Cloud SQL)

## 1. Google Cloud SDK Kurulumu

### Windows
```powershell
# Google Cloud SDK'yı indirin ve kurun
# https://cloud.google.com/sdk/docs/install

# Kurulum sonrası
gcloud init
gcloud auth login
```

### Linux/Mac
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

## 2. Google Cloud Projesi Oluşturma

```bash
# Yeni proje oluştur
gcloud projects create portfolio-site-123456 --name="Portfolio Site"

# Projeyi aktif et
gcloud config set project portfolio-site-123456

# Gerekli API'ları aktifleştir
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## 3. Cloud SQL (PostgreSQL) Kurulumu

```bash
# PostgreSQL instance oluştur
gcloud sql instances create portfolio-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=your-secure-password

# Veritabanı oluştur
gcloud sql databases create portfolio \
    --instance=portfolio-db

# Kullanıcı oluştur
gcloud sql users create portfolio-user \
    --instance=portfolio-db \
    --password=your-user-password

# Connection name'i al (önemli!)
gcloud sql instances describe portfolio-db --format="value(connectionName)"
# Output: your-project:us-central1:portfolio-db
```

## 4. Environment Variables & Secrets

### Secret Manager kullanarak güvenli değişkenler oluştur

```bash
# Secret key oluştur (Django için)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > secret_key.txt

# Secret Manager'a ekle
gcloud secrets create SECRET_KEY --data-file=secret_key.txt
rm secret_key.txt

# Database URL secret
echo "postgresql://portfolio-user:your-user-password@/portfolio?host=/cloudsql/your-project:us-central1:portfolio-db" | \
    gcloud secrets create DATABASE_URL --data-file=-

# Allowed hosts
echo "*.run.app,yourdomain.com" | gcloud secrets create ALLOWED_HOSTS --data-file=-

# Admin email
echo "bugraakin01@gmail.com" | gcloud secrets create ALLOWED_ADMIN_EMAIL --data-file=-
```

## 5. Docker Image Build & Push

### Yerel olarak test (opsiyonel)
```bash
# Build
docker build -f Dockerfile.gcloud -t portfolio-site .

# Test
docker run -p 8080:8080 \
    -e SECRET_KEY="test-key" \
    -e DATABASE_URL="sqlite:///db.sqlite3" \
    -e ALLOWED_HOSTS="localhost,127.0.0.1" \
    portfolio-site
```

### Google Container Registry'ye push
```bash
# Docker image'ı tag'le
docker tag portfolio-site gcr.io/portfolio-site-123456/portfolio-site:latest

# GCR'ye gönder
docker push gcr.io/portfolio-site-123456/portfolio-site:latest

# Veya Cloud Build ile otomatik build
gcloud builds submit --config cloudbuild.yaml
```

## 6. Cloud Run'a Deploy

### Manuel deployment
```bash
gcloud run deploy portfolio-site \
    --image gcr.io/portfolio-site-123456/portfolio-site:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=portfolio_site.settings" \
    --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,ALLOWED_HOSTS=ALLOWED_HOSTS:latest,ALLOWED_ADMIN_EMAIL=ALLOWED_ADMIN_EMAIL:latest" \
    --add-cloudsql-instances your-project:us-central1:portfolio-db
```

### Cloud Build ile otomatik deployment (önerilen)
```bash
# cloudbuild.yaml dosyasını düzenle (substitution değerlerini güncelle)
# Sonra deploy et
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_REGION=us-central1,_INSTANCE_CONNECTION_NAME=your-project:us-central1:portfolio-db
```

## 7. Database Migration

```bash
# Cloud Run service hesabına bağlan ve migration çalıştır
gcloud run jobs create migrate-db \
    --image gcr.io/portfolio-site-123456/portfolio-site:latest \
    --region us-central1 \
    --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
    --add-cloudsql-instances your-project:us-central1:portfolio-db \
    --command "python,manage.py,migrate,--noinput"

# Job'ı çalıştır
gcloud run jobs execute migrate-db --region us-central1
```

## 8. Superuser Oluşturma

```bash
# Cloud Shell veya local'den
gcloud run services proxy portfolio-site --port 8080 --region us-central1 &

# Başka bir terminal'de
python manage.py createsuperuser

# Veya script ile
gcloud run jobs create create-superuser \
    --image gcr.io/portfolio-site-123456/portfolio-site:latest \
    --region us-central1 \
    --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
    --add-cloudsql-instances your-project:us-central1:portfolio-db \
    --set-env-vars "DJANGO_SUPERUSER_USERNAME=bugraakin01,DJANGO_SUPERUSER_EMAIL=bugraakin01@gmail.com,DJANGO_SUPERUSER_PASSWORD=your-password" \
    --command "python,manage.py,createsuperuser,--noinput"

gcloud run jobs execute create-superuser --region us-central1
```

## 9. Custom Domain Bağlama

```bash
# Domain doğrulama
gcloud domains verify yourdomain.com

# Cloud Run'a domain ekle
gcloud run domain-mappings create \
    --service portfolio-site \
    --domain yourdomain.com \
    --region us-central1

# DNS kayıtlarını güncelle (Cloud Console'da gösterilen değerlerle)
```

## 10. SSL/TLS Sertifikası

Cloud Run otomatik olarak managed SSL sertifikası sağlar. Custom domain eklediğinizde otomatik oluşturulur.

## 11. Environment Variables Güncelleme

```bash
# Mevcut değişkenleri görüntüle
gcloud run services describe portfolio-site --region us-central1

# Yeni değişken ekle
gcloud run services update portfolio-site \
    --region us-central1 \
    --set-env-vars "DEBUG=False,ENVIRONMENT=production"

# Secret'ı güncelle
gcloud secrets versions add SECRET_KEY --data-file=new_secret.txt
```

## 12. Monitoring & Logging

```bash
# Logs görüntüle
gcloud run services logs read portfolio-site --region us-central1 --limit 50

# Gerçek zamanlı logs
gcloud run services logs tail portfolio-site --region us-central1

# Cloud Console'da monitoring
# https://console.cloud.google.com/run
```

## 13. Auto-scaling Ayarları

```bash
# Min/max instance ayarla
gcloud run services update portfolio-site \
    --region us-central1 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 80

# CPU ve memory
gcloud run services update portfolio-site \
    --region us-central1 \
    --cpu 2 \
    --memory 2Gi
```

## 14. Backup Stratejisi

```bash
# Cloud SQL otomatik backup
gcloud sql instances patch portfolio-db \
    --backup-start-time 03:00

# Manuel backup
gcloud sql backups create --instance portfolio-db

# Backup'ları listele
gcloud sql backups list --instance portfolio-db
```

## 15. CI/CD Pipeline (GitHub Actions)

`.github/workflows/deploy-gcloud.yml` dosyası oluştur:

```yaml
name: Deploy to Google Cloud Run

on:
  push:
    branches: [main]

env:
  PROJECT_ID: portfolio-site-123456
  SERVICE_NAME: portfolio-site
  REGION: us-central1

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Build and push Docker image
        run: |
          gcloud builds submit --config cloudbuild.yaml
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
            --region $REGION
```

## 16. Maliyet Optimizasyonu

```bash
# Cold start'ı azalt (min-instances=1 ama maliyet artar)
gcloud run services update portfolio-site \
    --region us-central1 \
    --min-instances 1

# Veya Startup CPU boost kullan
gcloud run services update portfolio-site \
    --region us-central1 \
    --cpu-boost

# Memory ve CPU'yu optimize et
gcloud run services update portfolio-site \
    --region us-central1 \
    --memory 1Gi \
    --cpu 1
```

## 17. Güvenlik Best Practices

1. **IAM Permissions**: En az yetki prensibi
2. **Secret Manager**: Tüm hassas veriler için
3. **VPC Connector**: Private Cloud SQL erişimi
4. **Cloud Armor**: DDoS koruması
5. **Identity-Aware Proxy**: Admin paneli için

## 18. Troubleshooting

```bash
# Service logs
gcloud run services logs read portfolio-site --region us-central1 --limit 100

# Build logs
gcloud builds log [BUILD_ID]

# Cloud SQL logs
gcloud sql operations list --instance portfolio-db

# Health check
curl https://portfolio-site-xxxxx.run.app/health/

# Shell access (debug için)
gcloud run services proxy portfolio-site --port 8080 --region us-central1
```

## 19. Rollback

```bash
# Önceki revision'a geri dön
gcloud run services update-traffic portfolio-site \
    --region us-central1 \
    --to-revisions PREVIOUS_REVISION=100

# Revision'ları listele
gcloud run revisions list --service portfolio-site --region us-central1
```

## 20. Faydalı Komutlar

```bash
# Service URL'i al
gcloud run services describe portfolio-site --region us-central1 --format="value(status.url)"

# Service silme
gcloud run services delete portfolio-site --region us-central1

# Cloud SQL instance silme
gcloud sql instances delete portfolio-db

# Secret silme
gcloud secrets delete SECRET_KEY
```

## Maliyetler (Tahmini)

- **Cloud Run**: İlk 2 milyon istek ücretsiz, sonrası $0.40/milyon istek
- **Cloud SQL**: db-f1-micro ~$7/ay
- **Storage**: 5GB ücretsiz
- **Network**: İlk 1GB ücretsiz

**Toplam tahmini maliyet**: $10-30/ay (trafik miktarına göre)

## Önemli Notlar

1. `your-project` ve `portfolio-site-123456` yerine kendi proje ID'nizi kullanın
2. Tüm şifreleri güçlü yapın ve Secret Manager kullanın
3. Production'da `DEBUG=False` olmalı
4. `ALLOWED_HOSTS` doğru şekilde ayarlayın
5. HTTPS sertifikası otomatik oluşturulur
6. Cloud SQL için Cloud SQL Proxy kullanılır

## Destek

Sorun yaşarsanız:
- Google Cloud Console Logs: https://console.cloud.google.com/logs
- Cloud Run Documentation: https://cloud.google.com/run/docs
- Stack Overflow: [google-cloud-run] tag'i

Deploy başarıyla tamamlandığında:
```
Service [portfolio-site] revision [portfolio-site-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://portfolio-site-xxxxx-uc.a.run.app
```

✅ Deployment tamamlandı!
