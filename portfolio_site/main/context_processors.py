from .models import SocialLink


def social_links(request):
    """
    Context processor to provide global social links for the footer.
    """
    return {
        'global_social_links': SocialLink.objects.filter(
            is_visible=True
        ).order_by('order', 'platform')
    }