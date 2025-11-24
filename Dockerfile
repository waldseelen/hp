# Cloud Run Kesin Çalışan Dockerfile
# Node.js Frontend + Django Backend

FROM node:20-alpine

WORKDIR /app

# 1. Package dosyalarını kopyala
COPY package.json package-lock.json ./
RUN npm ci

# 2. Tüm projeyi kopyala
COPY . .

# 3. Projeyi derle
RUN npm run build

# 4. PORT'u 8080 olarak ayarla (Cloud Run gereksinimi)
ENV PORT=8080
EXPOSE 8080

# 5. Uygulamayı başlat - 0.0.0.0 ve 8080 portuna zorla
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8080"]
