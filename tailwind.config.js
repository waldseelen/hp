/**
 * TAILWIND.CONFIG.JS - Tailwind CSS Konfigürasyon Dosyası (Django Portfolio Projesi)
 * ===============================================================================
 *
 * Bu dosya Django portfolio projesinin Tailwind CSS konfigürasyonunu tanımlar.
 * Modern, responsive ve dark theme destekli tasarım sistemini yapılandırır.
 *
 * TEMEL KONFİGÜRASYONLAR:
 * - Content: Django template dosyalarını tarar (./templates/**/*.html)
 * - Dark Mode: Class - based dark mode desteği('class' stratejisi)
    * - Custom Colors: Primary ve secondary renk paletleri
        * - Animations: Fade -in, slide - up ve starfield animasyonları
            *
 * RENK PALETLERİ:
 * - Primary(50 - 900): Ana tema renkleri(khaki / altın tonları)
    * - Secondary(800 - 900): Koyu tema için gri tonları
        *
 * ANİMASYON SİSTEMİ:
 * - fade -in: Yumuşak görünüm geçişleri
    * - slide - up: Yukarı kayma efekti
        * - starfield: Arka plan yıldız animasyonu
            *
 * BUILD KOMUTU:
 * npm run build: css(input.css -> output.css)
    *
 * KULLANIM ALANLARI:
 * - Django template dosyalarında class-based styling
    * - Responsive design breakpoints
        * - Dark / light theme switching
            * - Modern UI component styling
                *
 * @type { import('tailwindcss').Config }
 */
module.exports = {
    content: ['./templates/**/*.html', './**/templates/**/*.html', './static/css/components/**/*.css'],
    darkMode: 'class',
    theme: {
        extend: {
            fontFamily: {
                'sans': ['Inter', 'system-ui', 'sans-serif'],
                'mono': ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
                'display': ['Inter', 'system-ui', 'sans-serif'],
            },
            fontSize: {
                'xs': ['0.75rem', { lineHeight: '1rem' }],
                'sm': ['0.875rem', { lineHeight: '1.25rem' }],
                'base': ['1rem', { lineHeight: '1.5rem' }],
                'lg': ['1.125rem', { lineHeight: '1.75rem' }],
                'xl': ['1.25rem', { lineHeight: '1.75rem' }],
                '2xl': ['1.5rem', { lineHeight: '2rem' }],
                '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
                '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
                '5xl': ['3rem', { lineHeight: '1' }],
                '6xl': ['3.75rem', { lineHeight: '1' }],
                '7xl': ['4.5rem', { lineHeight: '1' }],
                '8xl': ['6rem', { lineHeight: '1' }],
                '9xl': ['8rem', { lineHeight: '1' }],
            },
            spacing: {
                '18': '4.5rem',
                '88': '22rem',
                '128': '32rem',
                '144': '36rem',
            },
            colors: {
                primary: {
                    50: '#fef9e8',
                    100: '#fdeec2',
                    200: '#fbe291',
                    300: '#f6d55f',
                    400: '#f5d85c',
                    500: '#e6c547',
                    600: '#c9a73b',
                    700: '#a9862f',
                    800: '#866724',
                    900: '#6c521d'
                },
                secondary: {
                    50: '#f8fafc',
                    100: '#e2e8f0',
                    200: '#cbd5f5',
                    300: '#a8b7d6',
                    400: '#94a3b8',
                    500: '#64748b',
                    600: '#475569',
                    700: '#334155',
                    800: '#16213b',
                    900: '#0b1220'
                },
                accent: {
                    100: '#dbeafe',
                    200: '#bfdbfe',
                    300: '#93c5fd',
                    400: '#60a5fa',
                    500: '#3b82f6',
                    600: '#2563eb'
                },
                surface: {
                    DEFAULT: '#111827',
                    elevated: '#16213b',
                    darkest: '#040a16'
                },
                text: {
                    DEFAULT: '#e2e8f0',
                    muted: '#94a3b8',
                    inverse: '#0b1220'
                },
                success: {
                    100: '#dcfce7',
                    300: '#86efac',
                    400: '#4ade80',
                    500: '#34d399',
                    600: '#059669'
                },
                warning: {
                    100: '#fef3c7',
                    300: '#fcd34d',
                    400: '#fbbf24',
                    500: '#f59e0b',
                    600: '#d97706'
                },
                error: {
                    100: '#fee2e2',
                    300: '#fca5a5',
                    400: '#f87171',
                    500: '#ef4444',
                    600: '#dc2626'
                },
                info: {
                    100: '#dbeafe',
                    300: '#93c5fd',
                    400: '#60a5fa',
                    500: '#3b82f6',
                    600: '#2563eb'
                }
            },
            transitionTimingFunction: {
                'bounce': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
                'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
            },
            transitionDuration: {
                '2000': '2000ms',
                '3000': '3000ms',
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-in-out',
                'slide-up': 'slideUp 0.3s ease-out',
                'starfield': 'starfield 20s linear infinite',
                'float': 'float 3s ease-in-out infinite',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'bounce-gentle': 'bounce 2s infinite',
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
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-10px)' },
                }
            }
        },
    },
    plugins: [],
}
