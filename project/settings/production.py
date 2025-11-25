"""
Production settings for portfolio project.
All security settings enabled, DEBUG=False, production-grade configurations.
Optimized for Google Cloud Run deployment.
"""

import os

from .base import *  # noqa: F401, F403

# Production settings - Override base.py defaults
DEBUG = False

# ===...  # abbreviated version of full content for readability