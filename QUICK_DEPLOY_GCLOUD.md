# 🚀 Google Cloud Hızlı Deployment Rehberi

## Hızlı Başlangıç (5 Dakika)

### 1. Google Cloud CLI Kurulumu
```bash
# Windows için: https://cloud.google.com/sdk/docs/install
# Mac/Linux için:
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### 2. Proje Oluştur ve Ayarla
```bash
# Değişkenleri ayarla
export PROJECT_ID="portfolio-site-$(date +%s)"
export REGION="us-central1"
export SERVICE_NAME="portfolio-site"

# Proje oluştur
gcloud projects create $PROJECT_ID --name="Portfolio Site"
gcloud config set project $PROJECT_ID

# Billing hesabı bağla (GCP Console'dan gerekli)
# https://console.cloud.google.com/billing

# API'ları aktifleştir
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com
```

### 3. PostgreSQL Database Oluştur
```bash
# Database instance oluştur
gcloud sql instances create portfolio-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --root-password="$(openssl rand -base64 32)"

# Database ve user oluştur
gcloud sql databases create portfolio --instance=portfolio-db
gcloud sql users create portfolio-user \
    --instance=portfolio-db \
    --password="$(openssl rand -base64 32)"

# Connection name'i al
INSTANCE_CONNECTION=$(gcloud sql instances describe portfolio-db --format="value(connectionName)")
echo "Instance Connection: $INSTANCE_CONNECTION"
```

### 4. Secrets Oluştur
```bash
# Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" | \
    gcloud secrets create SECRET_KEY --data-file=-

# Database URL (yukarıdaki şifreleri kullan)
DB_PASSWORD="your-password-from-step-3"
echo "postgresql://portfolio-user:$DB_PASSWORD@/portfolio?host=/cloudsql/$INSTANCE_CONNECTION" | \
    gcloud secrets create DATABASE_URL --data-file=-

# Allowed hosts
echo "*.run.app" | gcloud secrets create ALLOWED_HOSTS --data-file=-

# Admin email
echo "bugraakin01@gmail.com" | gcloud secrets create ALLOWED_ADMIN_EMAIL --data-file=-
```

### 5. Build ve Deploy
```bash
# Cloud Build ile deploy et
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_REGION=$REGION,_INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION

# Veya manuel olarak
docker build -f Dockerfile.gcloud -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest .
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 1 \
    --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,ALLOWED_HOSTS=ALLOWED_HOSTS:latest" \
    --add-cloudsql-instances $INSTANCE_CONNECTION
```

### 6. Database Migration
```bash
# Migration job oluştur ve çalıştır
gcloud run jobs create migrate-db \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
    --add-cloudsql-instances $INSTANCE_CONNECTION \
    --command "python,manage.py,migrate,--noinput"

gcloud run jobs execute migrate-db --region $REGION --wait
```

### 7. Superuser Oluştur
```bash
# Superuser job oluştur
gcloud run jobs create create-superuser \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" \
    --add-cloudsql-instances $INSTANCE_CONNECTION \
    --set-env-vars "DJANGO_SUPERUSER_USERNAME=bugraakin01,DJANGO_SUPERUSER_EMAIL=bugraakin01@gmail.com,DJANGO_SUPERUSER_PASSWORD=9CXb8|)£Y=o3@0AdV_M{P&=" \
    --command "python,manage.py,createsuperuser,--noinput"

gcloud run jobs execute create-superuser --region $REGION --wait
```

### 8. URL'i Al ve Test Et
```bash
# Service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
echo "🎉 Deployment tamamlandı!"
echo "URL: $SERVICE_URL"
echo "Admin Panel: $SERVICE_URL/admin"

# Health check
curl $SERVICE_URL/health/
```

## Tek Satır Deployment Script

Tüm deployment'ı tek script ile çalıştır:

```bash
#!/bin/bash
# deploy.sh

set -e

PROJECT_ID="portfolio-site-$(date +%s)"
REGION="us-central1"
SERVICE_NAME="portfolio-site"

echo "🚀 Starting deployment..."

# 1. Proje oluştur
gcloud projects create $PROJECT_ID --name="Portfolio Site"
gcloud config set project $PROJECT_ID

# 2. API'ları aktifleştir
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com containerregistry.googleapis.com

# 3. Database
DB_ROOT_PASSWORD=$(openssl rand -base64 32)
DB_USER_PASSWORD=$(openssl rand -base64 32)
gcloud sql instances create portfolio-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=$REGION --root-password="$DB_ROOT_PASSWORD"
gcloud sql databases create portfolio --instance=portfolio-db
gcloud sql users create portfolio-user --instance=portfolio-db --password="$DB_USER_PASSWORD"
INSTANCE_CONNECTION=$(gcloud sql instances describe portfolio-db --format="value(connectionName)")

# 4. Secrets
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" | gcloud secrets create SECRET_KEY --data-file=-
echo "postgresql://portfolio-user:$DB_USER_PASSWORD@/portfolio?host=/cloudsql/$INSTANCE_CONNECTION" | gcloud secrets create DATABASE_URL --data-file=-
echo "*.run.app" | gcloud secrets create ALLOWED_HOSTS --data-file=-

# 5. Build & Deploy
gcloud builds submit --config cloudbuild.yaml --substitutions=_REGION=$REGION,_INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION

# 6. Migration
gcloud run jobs create migrate-db --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest --region $REGION --set-secrets "SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest" --add-cloudsql-instances $INSTANCE_CONNECTION --command "python,manage.py,migrate,--noinput"
gcloud run jobs execute migrate-db --region $REGION --wait

# 7. URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")

echo "✅ Deployment complete!"
echo "URL: $SERVICE_URL"
echo "Project ID: $PROJECT_ID"
echo "DB Password: $DB_USER_PASSWORD"
```

Script'i çalıştır:
```bash
chmod +x deploy.sh
./deploy.sh
```

## PowerShell Versiyonu (Windows)

```powershell
# deploy.ps1
$PROJECT_ID = "portfolio-site-$(Get-Date -Format 'yyyyMMddHHmmss')"
$REGION = "us-central1"
$SERVICE_NAME = "portfolio-site"

Write-Host "🚀 Starting deployment..." -ForegroundColor Green

# Proje oluştur
gcloud projects create $PROJECT_ID --name="Portfolio Site"
gcloud config set project $PROJECT_ID

# API'ları aktifleştir
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com containerregistry.googleapis.com

# Database oluştur
$DB_PASSWORD = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
gcloud sql instances create portfolio-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=$REGION --root-password=$DB_PASSWORD
gcloud sql databases create portfolio --instance=portfolio-db
gcloud sql users create portfolio-user --instance=portfolio-db --password=$DB_PASSWORD

# Instance connection
$INSTANCE_CONNECTION = gcloud sql instances describe portfolio-db --format="value(connectionName)"

# Build ve deploy
gcloud builds submit --config cloudbuild.yaml --substitutions="_REGION=$REGION,_INSTANCE_CONNECTION_NAME=$INSTANCE_CONNECTION"

# URL al
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "URL: $SERVICE_URL" -ForegroundColor Cyan
Write-Host "Project ID: $PROJECT_ID" -ForegroundColor Cyan
```

Çalıştır:
```powershell
.\deploy.ps1
```

## CI/CD ile Otomatik Deployment

### GitHub Secrets Ekle:
1. GitHub repo → Settings → Secrets and variables → Actions
2. Şu secret'ları ekle:
   - `GCP_PROJECT_ID`: Google Cloud proje ID'niz
   - `GCP_SA_KEY`: Service account JSON key
   - `CLOUD_SQL_CONNECTION_NAME`: your-project:region:instance-name

### Service Account Oluştur:
```bash
# Service account oluştur
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# İzinleri ver
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"

# Key oluştur
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# key.json içeriğini GCP_SA_KEY secret'ına ekle
```

### Push ve Deploy:
```bash
git add .
git commit -m "Deploy to Google Cloud"
git push origin main
```

Artık her push'da otomatik deploy olacak! 🎉

## Faydalı Komutlar

```bash
# Logs görüntüle
gcloud run services logs read $SERVICE_NAME --region $REGION --limit 50

# Service bilgisi
gcloud run services describe $SERVICE_NAME --region $REGION

# Güncelleme
gcloud builds submit --config cloudbuild.yaml

# Rollback
gcloud run services update-traffic $SERVICE_NAME --region $REGION --to-revisions PREVIOUS_REVISION=100

# Temizlik (dikkat!)
gcloud run services delete $SERVICE_NAME --region $REGION
gcloud sql instances delete portfolio-db
gcloud projects delete $PROJECT_ID
```

## Sorun Giderme

```bash
# Health check başarısız
curl https://your-service.run.app/health/ -v

# Database bağlantı sorunu
gcloud sql instances describe portfolio-db

# Build hataları
gcloud builds log [BUILD_ID]

# Container logs
gcloud run services logs tail $SERVICE_NAME --region $REGION
```

## Maliyet Optimizasyonu

```bash
# Min instance 0 yap (cold start olabilir)
gcloud run services update $SERVICE_NAME --region $REGION --min-instances 0

# Memory azalt
gcloud run services update $SERVICE_NAME --region $REGION --memory 1Gi --cpu 1

# Database tier düşür (production için önerilmez)
gcloud sql instances patch portfolio-db --tier=db-f1-micro
```

✅ Hazır! Artık Google Cloud'da çalışan bir Django uygulamanız var!
