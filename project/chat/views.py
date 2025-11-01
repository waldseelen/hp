import logging

from django.shortcuts import render

logger = logging.getLogger(__name__)


def chat_view(request):
    """
    Chat page view with chat interface.
    """
    try:
        context = {
            "page_title": "Sohbet",
            "meta_description": "Canlı sohbet ve mesajlaşma",
        }

        return render(request, "chat/chat.html", context)

    except Exception as e:
        logger.error(f"Error in chat view: {str(e)}")
        context = {
            "page_title": "Sohbet",
            "meta_description": "Sohbet",
        }
        return render(request, "chat/chat.html", context)
