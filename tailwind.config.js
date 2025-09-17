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
        // Primary brand colors (gold/khaki theme)
        primary: {
          50: '#fefdf8',
          100: '#fdf9ed',
          200: '#f9f1d4',
          300: '#f4e6a4',
          400: '#FFD700',
          500: '#c8b560',
          600: '#a89550',
          700: '#8b7355',
          800: '#6b705c',
          900: '#4a4e3a'
        },
        // Secondary colors (grays for dark theme)
        secondary: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827'
        },
        // Semantic colors for UI components
        success: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b'
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f'
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d'
        },
        info: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a'
        },
        // Cybersecurity theme colors
        cyber: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d'
        },
        // AI/Tech theme colors
        tech: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a'
        },
        // Music theme colors
        music: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7c2d12',
          800: '#6b21a8',
          900: '#581c87'
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