#!/usr/bin/env python
"""
Comprehensive script to start all Celery services with proper configuration.
"""

import os
import signal
import subprocess
import sys
import time
from multiprocessing import Process
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings.development")

# Import Django after setting environment
import django

django.setup()

from django.conf import settings


class CeleryServiceManager:
    def __init__(self):
        self.processes = []
        self.broker_url = getattr(
            settings, "CELERY_BROKER_URL", "redis://localhost:6379/0"
        )

    def start_worker(self, queue_name="default", concurrency=4):
        """Start a Celery worker for specific queue."""
        cmd = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "portfolio_site",
            "worker",
            "--loglevel=info",
            f"--concurrency={concurrency}",
            f"--queues={queue_name}",
            f"--hostname=worker-{queue_name}@%h",
        ]

        print(f"Starting Celery worker for queue '{queue_name}'...")
        print(f"Command: {' '.join(cmd)}")

        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "portfolio_site.settings.development"

        process = subprocess.Popen(cmd, env=env)
        self.processes.append(("worker", queue_name, process))
        return process

    def start_beat(self):
        """Start Celery Beat scheduler."""
        cmd = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "portfolio_site",
            "beat",
            "--loglevel=info",
            "--scheduler=django_celery_beat.schedulers:DatabaseScheduler",
        ]

        print("Starting Celery Beat scheduler...")
        print(f"Command: {' '.join(cmd)}")

        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "portfolio_site.settings.development"

        process = subprocess.Popen(cmd, env=env)
        self.processes.append(("beat", "scheduler", process))
        return process

    def start_flower(self, port=5555):
        """Start Flower monitoring."""
        cmd = [
            sys.executable,
            "-m",
            "flower",
            "--broker",
            self.broker_url,
            "--port",
            str(port),
            "--persistent",
            "True",
            "--db",
            "flower.db",
        ]

        print(f"Starting Flower monitoring on port {port}...")
        print(f"Command: {' '.join(cmd)}")
        print(f"Dashboard will be available at: http://localhost:{port}")

        env = os.environ.copy()
        env["DJANGO_SETTINGS_MODULE"] = "portfolio_site.settings.development"

        process = subprocess.Popen(cmd, env=env)
        self.processes.append(("flower", "monitoring", process))
        return process

    def start_all_services(self):
        """Start all Celery services."""
        print("=" * 60)
        print("STARTING CELERY SERVICES")
        print("=" * 60)

        # Start workers for different priority queues
        self.start_worker("high_priority", concurrency=2)
        time.sleep(2)  # Stagger startup

        self.start_worker("default", concurrency=4)
        time.sleep(2)

        self.start_worker("low_priority", concurrency=2)
        time.sleep(2)

        # Start beat scheduler
        self.start_beat()
        time.sleep(2)

        # Start flower monitoring
        self.start_flower()

        print("\n" + "=" * 60)
        print("ALL SERVICES STARTED")
        print("=" * 60)

        self.show_status()

    def show_status(self):
        """Show status of all processes."""
        print("\nSERVICE STATUS:")
        print("-" * 40)

        for service_type, name, process in self.processes:
            if process.poll() is None:
                status = "RUNNING"
                pid = process.pid
            else:
                status = "STOPPED"
                pid = "N/A"

            print(f"{service_type.upper()} ({name}): {status} (PID: {pid})")

        print("\nUSEFUL COMMANDS:")
        print("-" * 40)
        print("• Monitor tasks: http://localhost:5555")
        print("• Test tasks: python manage.py test_celery")
        print("• Check worker status: celery -A portfolio_site status")
        print("• Inspect active tasks: celery -A portfolio_site inspect active")
        print("• Stop all: Press Ctrl+C")

    def stop_all(self):
        """Stop all running processes."""
        print("\nStopping all Celery services...")

        for service_type, name, process in self.processes:
            if process.poll() is None:
                print(f"Stopping {service_type} ({name})...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {service_type} ({name})...")
                    process.kill()

        print("All services stopped.")

    def wait_for_interrupt(self):
        """Wait for keyboard interrupt and handle shutdown."""
        try:
            print("\nServices are running. Press Ctrl+C to stop all services.")

            while True:
                time.sleep(1)

                # Check if any process died unexpectedly
                for service_type, name, process in self.processes:
                    if process.poll() is not None:
                        print(f"WARNING: {service_type} ({name}) stopped unexpectedly!")

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received.")
            self.stop_all()


def test_redis_connection():
    """Test Redis connection before starting services."""
    try:
        import redis

        redis_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")

        print(f"Testing Redis connection: {redis_url}")
        r = redis.from_url(redis_url)
        r.ping()
        print("✓ Redis connection successful")
        return True

    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("Please make sure Redis server is running.")
        return False


def main():
    """Main entry point."""
    print("CELERY SERVICE MANAGER")
    print("=" * 60)

    # Test Redis connection first
    if not test_redis_connection():
        sys.exit(1)

    # Create service manager
    manager = CeleryServiceManager()

    # Set up signal handlers
    def signal_handler(signum, frame):
        print(f"\nReceived signal {signum}")
        manager.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Start all services
        manager.start_all_services()

        # Wait for interrupt
        manager.wait_for_interrupt()

    except Exception as e:
        print(f"Error: {e}")
        manager.stop_all()
        sys.exit(1)


if __name__ == "__main__":
    main()
