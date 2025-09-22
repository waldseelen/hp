from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseServerError


def custom_404(request, exception):
    """
    Custom 404 error handler.
    Renders the 404 template with proper context and status code.
    """
    context = {
        'request_path': request.path,
        'site_name': 'Portfolio',
        'error_code': '404',
        'error_message': 'Sayfa Bulunamadı'
    }
    
    response = render(request, 'errors/404.html', context)
    response.status_code = 404
    return response


def custom_500(request):
    """
    Custom 500 error handler.
    Renders the 500 template with proper context and status code.
    """
    context = {
        'site_name': 'Portfolio',
        'error_code': '500',
        'error_message': 'Sunucu Hatası'
    }
    
    response = render(request, 'errors/500.html', context)
    response.status_code = 500
    return response