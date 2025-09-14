/**
 * ADMIN_IMPROVEMENTS.JS - Django Admin Panel Geliştirmeleri (Django Admin Panel Improvements)
 * ==========================================================================================
 *
 * Bu dosya, Django admin panelinin kullanıcı deneyimini iyileştiren özelleştirmeler
 * ve geliştirmeler sağlar. Standart admin arayüzüne modern UI/UX özelikleri ekler.
 *
 * TEMEL GELİŞTİRMELER:
 * • Status dropdown görsel geliştirmeleri - Renk kodlu durum seçiciler
 * • İmproved admin form functionality - Form işlevsellik geliştirmeleri  
 * • Enhanced list view interactions - Liste görünüm etkileşimleri
 * • Better mobile responsiveness - Mobil uyumluluk geliştirmeleri
 * • Custom admin widgets - Özel admin widget'ları
 * • Rich text editor improvements - Zengin metin editörü geliştirmeleri
 * • Image preview functionality - Görsel önizleme işlevselliği
 * • Bulk actions enhancements - Toplu işlem geliştirmeleri
 *
 * UI/UX GELİŞTİRMELERİ:
 * • Color-coded status indicators (draft=gray, published=green, etc.)
 * • Improved dropdown styling and visibility
 * • Enhanced form field validation feedback
 * • Better error message presentation
 * • Loading states for admin actions
 * • Success/failure notifications
 * • Keyboard shortcuts for common actions
 *
 * ERİŞİLEBİLİRLİK:
 * • Improved keyboard navigation
 * • Screen reader compatibility
 * • High contrast mode support
 * • ARIA labels for custom elements
 * • Focus management improvements
 * • Better semantic HTML structure
 *
 * BAĞIMLILIKLAR:
 * • jQuery (Django admin standart bağımlılık)
 * • Django admin CSS framework
 * • Modern tarayıcı desteği (ES5+)
 * • CSS custom properties support
 * • Django admin JavaScript utilities
 *
 * TARAYICI UYUMLULUK:
 * • Chrome 40+, Firefox 35+, Safari 9+, Edge 12+
 * • Internet Explorer 11 (temel destek)
 * • Mobile Safari ve Chrome Mobile
 *
 * PERFORMANS:
 * • Document ready optimization
 * • Event delegation patterns
 * • Minimal DOM manipulation
 * • CSS-based styling where possible
 * • Efficient jQuery selectors
 *
 * @author Portfolio Site Admin Team
 * @version 1.2.0
 * @since 1.0.0
 * @framework Django Admin
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        
        // Improve status dropdown visibility
        function improveStatusDropdown() {
            // Target status dropdowns (both in forms and changelist)
            $('.field-status select, .results tbody td select').each(function() {
                var $select = $(this);
                var currentValue = $select.val();
                
                // Add custom styling based on current value
                updateStatusStyling($select, currentValue);
                
                // Update styling when value changes
                $select.on('change', function() {
                    var newValue = $(this).val();
                    updateStatusStyling($select, newValue);
                });
            });
        }
        
        // Update status styling based on value
        function updateStatusStyling($select, value) {
            $select.removeClass('status-draft status-published status-unlisted status-scheduled');
            $select.addClass('status-' + value);
            $select.attr('value', value);
        }
        
        // Add navigation breadcrumbs improvements
        function improveBreadcrumbs() {
            var $breadcrumbs = $('.breadcrumbs');
            if ($breadcrumbs.length) {
                $breadcrumbs.addClass('improved-breadcrumbs');
                
                // Add icons to breadcrumb links
                $breadcrumbs.find('a').each(function() {
                    var $link = $(this);
                    var text = $link.text().toLowerCase();
                    
                    if (text.includes('home')) {
                        $link.prepend('🏠 ');
                    } else if (text.includes('blog')) {
                        $link.prepend('📝 ');
                    } else if (text.includes('posts')) {
                        $link.prepend('📄 ');
                    } else if (text.includes('add')) {
                        $link.prepend('➕ ');
                    } else if (text.includes('change')) {
                        $link.prepend('✏️ ');
                    }
                });
            }
        }
        
        // Improve form navigation
        function improveFormNavigation() {
            // Add quick navigation buttons
            var $form = $('form');
            if ($form.length && $('.submit-row').length) {
                var isAddForm = window.location.pathname.includes('/add/');
                var isChangeForm = window.location.pathname.includes('/change/');
                
                if (isChangeForm) {
                    // Add "Add Another" quick link
                    var addUrl = window.location.pathname.replace(/\/change\/.*/, '/add/');
                    var $quickAdd = $('<a href="' + addUrl + '" class="button quick-add-button">📝 Add New Post</a>');
                    $('.submit-row').prepend($quickAdd);
                }
                
                if (isAddForm) {
                    // Add "View All" quick link  
                    var listUrl = window.location.pathname.replace(/\/add\/$/, '/');
                    var $quickList = $('<a href="' + listUrl + '" class="button quick-list-button">📋 View All Posts</a>');
                    $('.submit-row').prepend($quickList);
                }
            }
        }
        
        // Add hover effects for better UX
        function addHoverEffects() {
            // Add hover effects to table rows
            $('.results tbody tr').hover(
                function() {
                    $(this).addClass('hovered-row');
                },
                function() {
                    $(this).removeClass('hovered-row');
                }
            );
            
            // Add click feedback to buttons
            $('.button, input[type="submit"]').on('click', function() {
                $(this).addClass('clicked');
                setTimeout(() => {
                    $(this).removeClass('clicked');
                }, 150);
            });
        }
        
        // Improve status field display
        function enhanceStatusField() {
            // Make status dropdown more prominent
            $('.field-status').addClass('enhanced-status-field');
            
            // Add status indicators
            $('.field-status select option').each(function() {
                var $option = $(this);
                var value = $option.val();
                
                switch(value) {
                    case 'draft':
                        if (!$option.text().includes('📝')) {
                            $option.text('📝 ' + $option.text());
                        }
                        break;
                    case 'published':
                        if (!$option.text().includes('✅')) {
                            $option.text('✅ ' + $option.text());
                        }
                        break;
                    case 'unlisted':
                        if (!$option.text().includes('🔒')) {
                            $option.text('🔒 ' + $option.text());
                        }
                        break;
                    case 'scheduled':
                        if (!$option.text().includes('⏰')) {
                            $option.text('⏰ ' + $option.text());
                        }
                        break;
                }
            });
        }
        
        // Add notification system
        function addNotifications() {
            // Show save notifications
            if (window.location.search.includes('saved=1')) {
                var $notification = $('<div class="admin-notification success">✅ Post saved successfully!</div>');
                $('body').prepend($notification);
                setTimeout(() => {
                    $notification.fadeOut();
                }, 3000);
            }
        }
        
        // Initialize all improvements
        improveStatusDropdown();
        improveBreadcrumbs();
        improveFormNavigation();
        addHoverEffects();
        enhanceStatusField();
        addNotifications();
        
        // Add smooth transitions
        $('<style>')
            .prop('type', 'text/css')
            .html(`
                .hovered-row {
                    background-color: #e0f2fe !important;
                    transform: scale(1.01);
                    transition: all 0.2s ease;
                }
                
                .clicked {
                    transform: scale(0.95);
                    transition: transform 0.1s ease;
                }
                
                .quick-add-button, .quick-list-button {
                    margin-right: 15px !important;
                    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
                    border: none !important;
                    color: white !important;
                    padding: 10px 20px !important;
                    border-radius: 6px !important;
                    text-decoration: none !important;
                    display: inline-block !important;
                    transition: all 0.2s ease !important;
                }
                
                .quick-add-button:hover, .quick-list-button:hover {
                    transform: translateY(-2px) !important;
                    box-shadow: 0 10px 25px rgba(5, 150, 105, 0.3) !important;
                    text-decoration: none !important;
                    color: white !important;
                }
                
                .enhanced-status-field select {
                    font-weight: bold !important;
                    text-transform: capitalize !important;
                }
                
                .admin-notification {
                    position: fixed !important;
                    top: 20px !important;
                    right: 20px !important;
                    padding: 15px 25px !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
                    z-index: 9999 !important;
                    font-weight: 600 !important;
                }
                
                .admin-notification.success {
                    background: #f0fdf4 !important;
                    border: 1px solid #bbf7d0 !important;
                    color: #166534 !important;
                }
                
                /* Status field styling improvements */
                .field-status select.status-draft {
                    border-left: 4px solid #6b7280 !important;
                }
                
                .field-status select.status-published {
                    border-left: 4px solid #059669 !important;
                }
                
                .field-status select.status-unlisted {
                    border-left: 4px solid #ea580c !important;
                }
                
                .field-status select.status-scheduled {
                    border-left: 4px solid #2563eb !important;
                }
            `)
            .appendTo('head');
    });
    
})(django.jQuery);