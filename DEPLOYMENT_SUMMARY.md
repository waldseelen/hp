# 🚀 Google Cloud Deployment - Özet

## ✅ Hazır Dosyalar

### 1. **Dockerfile** (Ana build dosyası)
- Google Cloud Run için optimize edilmiş
- Multi-stage build (Node.js + Python)
- Port 8080 (Cloud Run default)
- Health checks dahil
- Non-root user (güvenlik)

### 2. **cloudbuild.yaml** (Otomatik build)
- GitHub'a push yaptığında otomatik çalışır
- Docker image build eder
- Container Registry'ye gönderir
- Database migration yapar
- Cloud Run'a deploy eder

### 3. **.gcloudignore** (Exclude dosyaları)
- Deploy edilmeyecek dosyaları belirler
- `.gitignore` gibi çalışır

### 4. **.github/workflows/deploy-gcloud.yml** (GitHub Actions CI/CD)
- Her `git push` sonrası otomatik deploy
- Build → Push → Deploy → Migrate → Health Check

### 5. **scripts/gcloud-start.sh** (Startup script)
- Container başladığında çalışır
- Database connection check
- Migrations
- Gunicorn başlatma

### 6. **DEPLOYMENT_GUIDE_GCLOUD.md** (Detaylı rehber)
- 20 adımlı tam rehber
- Tüm komutlar ve açıklamalar

### 7. **QUICK_DEPLOY_GCLOUD.md** (Hızlı başlangıç)
- 5 dakikada deployment
- Tek script ile kurulum

## 🎯 Deployment Adımları

### Seçenek 1: GitHub Actions ile Otomatik (Önerilen)

1. **GitHub Secrets Ekle:**
   - `GCP_PROJECT_ID`: Google Cloud proje ID'niz
   - `GCP_SA_KEY`: Service account JSON key
   - `CLOUD_SQL_CONNECTION_NAME`: `project:region:instance`

2. **Push yap:**
   ```bash
   git add .
   git commit -m "Deploy to Google Cloud"
   git push origin main
   ```

3. **Bitir!** GitHub Actions her şeyi otomatik yapar.

### Seçenek 2: Manuel Cloud Build

```bash
# Google Cloud'a login
gcloud auth login
gcloud config set project YOUR-PROJECT-ID

# Deploy
gcloud builds submit --config cloudbuild.yaml
```

## 📋 İlk Kurulum (Tek Sefer)

### 1. Google Cloud Projesi Oluştur
```bash
gcloud projects create portfolio-site-123456 --name="Portfolio Site"
gcloud config set project portfolio-site-123456
```

### 2. API'ları Aktifleştir
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. PostgreSQL Oluştur
```bash
gcloud sql instances create portfolio-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1
```

### 4. Secrets Oluştur
```bash
# SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" | \
    gcloud secrets create SECRET_KEY --data-file=-

# DATABASE_URL
echo "postgresql://user:pass@/db?host=/cloudsql/project:region:instance" | \
    gcloud secrets create DATABASE_URL --data-file=-

# ALLOWED_HOSTS
echo "*.run.app" | gcloud secrets create ALLOWED_HOSTS --data-file=-
```

### 5. İlk Deploy
```bash
gcloud builds submit --config cloudbuild.yaml
```

## 🔄 Güncellemeler

Her kod değişikliğinde:
```bash
git add .
git commit -m "Update feature"
git push origin main
```

GitHub Actions otomatik olarak:
1. ✅ Build yapar
2. ✅ Test eder
3. ✅ Deploy eder
4. ✅ Migration çalıştırır
5. ✅ Health check yapar

## 📊 Monitoring

```bash
# Logs
gcloud run services logs read portfolio-site --region us-central1

# Status
gcloud run services describe portfolio-site --region us-central1

# URL
gcloud run services describe portfolio-site --region us-central1 --format="value(status.url)"
```

## 🛠️ Troubleshooting

```bash
# Build logs
gcloud builds log [BUILD_ID]

# Container logs
gcloud run services logs tail portfolio-site --region us-central1

# Health check
curl https://your-service.run.app/health/
```

## 💰 Maliyetler

- **Cloud Run**: İlk 2 milyon istek ücretsiz
- **Cloud SQL**: db-f1-micro ~$7/ay
- **Storage**: İlk 5GB ücretsiz
- **Toplam**: ~$10-20/ay

## ⚠️ Önemli Notlar

1. ✅ **Dockerfile** artık Cloud Run için hazır (eski Railway versiyonu `Dockerfile.railway` olarak yedeklendi)
2. ✅ **cloudbuild.yaml** otomatik build için hazır
3. ✅ **GitHub Actions** her push'da otomatik deploy yapar
4. ✅ Manuel script'lere gerek yok (ama `QUICK_DEPLOY_GCLOUD.md`'de emergency için var)
5. ⚠️ **Secrets** Google Cloud Console'dan eklemen gerekiyor
6. ⚠️ **Billing** hesabı aktif olmalı

## 🎉 Sonuç

Artık projen Google Cloud'a deploy edilmeye hazır! 

**En kolay yol:**
1. Google Cloud Console'dan proje oluştur
2. Billing bağla
3. Secrets ekle
4. GitHub'a push yap → Otomatik deploy!

Detaylar için: `DEPLOYMENT_GUIDE_GCLOUD.md` veya `QUICK_DEPLOY_GCLOUD.md`
