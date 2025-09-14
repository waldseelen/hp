/**
 * TAILWIND.CONFIG.JS - Tailwind CSS Konfigürasyon Dosyası (Django Portfolio Projesi)
 * ===============================================================================
 *
 * Bu dosya Django portfolio projesinin Tailwind CSS konfigürasyonunu tanımlar.
 * Modern, responsive ve dark theme destekli tasarım sistemini yapılandırır.
 * 
 * TEMEL KONFİGÜRASYONLAR:
 * - Content: Django template dosyalarını tarar (./templates/**/*.html)
 * - Dark Mode: Class-based dark mode desteği ('class' stratejisi)
 * - Custom Colors: Primary ve secondary renk paletleri
 * - Animations: Fade-in, slide-up ve starfield animasyonları
 * 
 * RENK PALETLERİ:
 * - Primary (50-900): Ana tema renkleri (khaki/altın tonları)
 * - Secondary (800-900): Koyu tema için gri tonları
 * 
 * ANİMASYON SİSTEMİ:
 * - fade-in: Yumuşak görünüm geçişleri
 * - slide-up: Yukarı kayma efekti
 * - starfield: Arka plan yıldız animasyonu
 * 
 * BUILD KOMUTU:
 * npm run build:css (input.css -> output.css)
 * 
 * KULLANIM ALANLARI:
 * - Django template dosyalarında class-based styling
 * - Responsive design breakpoints
 * - Dark/light theme switching
 * - Modern UI component styling
 * 
 * @type {import('tailwindcss').Config}
 */
module.exports = {
  content: ['./templates/**/*.html', './**/templates/**/*.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#fefdf8',
          100: '#fdf9ed',
          200: '#f9f1d4',
          300: '#f4e6a4',
          400: '#f0e68c',
          500: '#c8b560',
          600: '#a89550',
          700: '#8b7355',
          800: '#6b705c',
          900: '#4a4e3a'
        },
        secondary: {
          800: '#1f2937',
          900: '#111827'
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'starfield': 'starfield 20s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        starfield: {
          '0%': { transform: 'translateY(0px)' },
          '100%': { transform: 'translateY(-100px)' },
        }
      }
    },
  },
  plugins: [],
}