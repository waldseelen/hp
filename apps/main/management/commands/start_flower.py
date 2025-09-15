"""
Management command to start Flower monitoring for Celery tasks.
"""

import os
import subprocess
import sys
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Start Flower monitoring for Celery tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--port',
            type=int,
            default=5555,
            help='Port to run Flower on (default: 5555)'
        )
        parser.add_argument(
            '--address',
            type=str,
            default='0.0.0.0',
            help='Address to bind Flower to (default: 0.0.0.0)'
        )
        parser.add_argument(
            '--broker',
            type=str,
            default=None,
            help='Celery broker URL (uses CELERY_BROKER_URL from settings if not provided)'
        )

    def handle(self, *args, **options):
        port = options['port']
        address = options['address']
        broker_url = options['broker'] or getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')

        self.stdout.write(
            self.style.SUCCESS(f'Starting Flower monitoring on {address}:{port}')
        )
        self.stdout.write(f'Broker URL: {broker_url}')
        self.stdout.write('Access the monitoring dashboard at: http://{}:{}'.format(
            'localhost' if address == '0.0.0.0' else address, port
        ))

        try:
            # Start Flower with the specified configuration
            cmd = [
                sys.executable, '-m', 'flower',
                '--broker', broker_url,
                '--address', address,
                '--port', str(port),
                '--persistent', 'True',  # Enable persistent mode
                '--db', 'flower.db',     # Database file for persistence
            ]

            # Set environment variables
            env = os.environ.copy()
            env['DJANGO_SETTINGS_MODULE'] = os.environ.get(
                'DJANGO_SETTINGS_MODULE',
                'portfolio_site.settings.development'
            )

            self.stdout.write('Starting Flower with command: ' + ' '.join(cmd))

            # Run Flower
            subprocess.run(cmd, env=env)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nFlower monitoring stopped.'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting Flower: {e}')
            )
            raise