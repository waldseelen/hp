# 1. Zemin: Node.js 22 kullan (Uyarıları da çözer)
FROM node:22-alpine

# 2. Çalışma masasını hazırla
WORKDIR /app

# 3. Dosyaları kopyala
COPY package*.json ./

# 4. KURULUM (Sihirli Dokunuş Burası)
# --include=dev diyerek "Geliştirici araçlarını (Vite) da zorla yükle" diyoruz.
RUN npm install --include=dev

# 5. Projenin geri kalanını kopyala
COPY . .

# 6. Uygulamayı derle (Build)
RUN npm run build

# 7. PORT ayarını yap
ENV PORT=8080
EXPOSE 8080

# 8. Uygulamayı başlat
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "8080"]
