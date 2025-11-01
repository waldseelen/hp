import subprocess
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import psutil


class Command(BaseCommand):
    help = "Manage Django development server with auto-restart and process monitoring"

    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            type=int,
            default=8000,
            help="Port to run the server on (default: 8000)",
        )
        parser.add_argument(
            "--auto-restart",
            action="store_true",
            help="Enable auto-restart on crash",
        )
        parser.add_argument(
            "--max-restarts",
            type=int,
            default=3,
            help="Maximum restart attempts (default: 3)",
        )
        parser.add_argument(
            "--restart-delay",
            type=int,
            default=2,
            help="Delay between restart attempts in seconds (default: 2)",
        )
        parser.add_argument(
            "--kill-orphans",
            action="store_true",
            help="Kill orphaned Django processes before starting",
        )
        parser.add_argument(
            "--check-port",
            action="store_true",
            help="Check if port is available before starting",
        )
        parser.add_argument(
            "--status",
            action="store_true",
            help="Show server status information",
        )
        parser.add_argument(
            "--stop",
            action="store_true",
            help="Stop running Django servers",
        )
        parser.add_argument(
            "--preview-port",
            type=int,
            default=8001,
            help="Port for preview server (default: 8001)",
        )

    def handle(self, *args, **options):
        if options["status"]:
            self.show_status()
            return

        if options["stop"]:
            self.stop_servers()
            return

        if options["kill_orphans"]:
            self.kill_orphan_processes()

        if options["check_port"]:
            available_port = self.find_available_port(options["port"])
            if available_port != options["port"]:
                self.stdout.write(
                    self.style.WARNING(
                        f'Port {options["port"]} not available, using {available_port}'
                    )
                )
                options["port"] = available_port

        if options["auto_restart"]:
            self.run_with_auto_restart(options)
        else:
            self.run_server(options["port"])

    def show_status(self):
        """Show current server status"""
        self.stdout.write(self.style.SUCCESS("Django Server Status:"))
        self.stdout.write("=" * 50)

        django_processes = self.find_django_processes()
        if django_processes:
            for proc in django_processes:
                try:
                    self.stdout.write(f"PID: {proc.pid}")
                    self.stdout.write(f'Command: {" ".join(proc.cmdline())}')
                    self.stdout.write(f"Status: {proc.status()}")
                    self.stdout.write(f"CPU: {proc.cpu_percent():.1f}%")
                    self.stdout.write(
                        f"Memory: {proc.memory_info().rss / 1024 / 1024:.1f} MB"
                    )

                    # Check listening ports
                    try:
                        connections = proc.connections()
                        listening_ports = [
                            conn.laddr.port
                            for conn in connections
                            if conn.status == "LISTEN"
                        ]
                        if listening_ports:
                            self.stdout.write(
                                f'Listening on ports: {", ".join(map(str, listening_ports))}'
                            )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                    self.stdout.write("-" * 30)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
            self.stdout.write("No Django server processes found")

    def stop_servers(self):
        """Stop all running Django servers"""
        django_processes = self.find_django_processes()
        if not django_processes:
            self.stdout.write("No Django servers running")
            return

        self.stdout.write(f"Found {len(django_processes)} Django server(s) to stop")

        for proc in django_processes:
            try:
                self.stdout.write(f"Stopping process {proc.pid}...")
                proc.terminate()

                # Wait for graceful termination
                try:
                    proc.wait(timeout=5)
                    self.stdout.write(
                        self.style.SUCCESS(f"Process {proc.pid} stopped gracefully")
                    )
                except psutil.TimeoutExpired:
                    # Force kill if needed
                    self.stdout.write(f"Force killing process {proc.pid}...")
                    proc.kill()
                    self.stdout.write(
                        self.style.WARNING(f"Process {proc.pid} force killed")
                    )

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.stdout.write(
                    self.style.ERROR(f"Error stopping process {proc.pid}: {e}")
                )

    def find_django_processes(self):
        """Find running Django server processes"""
        django_processes = []
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if (
                    cmdline
                    and "manage.py" in " ".join(cmdline)
                    and "runserver" in " ".join(cmdline)
                ):
                    django_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return django_processes

    def kill_orphan_processes(self):
        """Kill orphaned Django processes"""
        django_processes = self.find_django_processes()
        if django_processes:
            self.stdout.write(
                f"Found {len(django_processes)} orphaned Django process(es)"
            )
            for proc in django_processes:
                try:
                    self.stdout.write(f"Killing orphaned process {proc.pid}")
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        else:
            self.stdout.write("No orphaned processes found")

    def find_available_port(self, start_port, max_port=9000):
        """Find an available port starting from start_port"""
        import socket

        for port in range(start_port, max_port + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", port))
                    return port
            except OSError:
                continue

        raise CommandError(
            f"No available ports found between {start_port} and {max_port}"
        )

    def run_with_auto_restart(self, options):
        """Run server with auto-restart capability"""
        port = options["port"]
        max_restarts = options["max_restarts"]
        restart_delay = options["restart_delay"]
        restart_count = 0

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting Django server with auto-restart on port {port}"
            )
        )
        self.stdout.write(
            f"Max restarts: {max_restarts}, Restart delay: {restart_delay}s"
        )

        while restart_count <= max_restarts:
            try:
                # Run the server
                process = self.start_server_process(port)

                # Monitor the process
                process.wait()

                # If we get here, the process has exited
                if restart_count < max_restarts:
                    restart_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Server crashed. Restarting in {restart_delay}s... (Attempt {restart_count}/{max_restarts})"
                        )
                    )
                    time.sleep(restart_delay)
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Max restart attempts ({max_restarts}) reached. Giving up."
                        )
                    )
                    break

            except KeyboardInterrupt:
                self.stdout.write("\nShutting down server...")
                if "process" in locals():
                    process.terminate()
                break
            except Exception as e:
                if restart_count < max_restarts:
                    restart_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"Server error: {e}. Restarting in {restart_delay}s... (Attempt {restart_count}/{max_restarts})"
                        )
                    )
                    time.sleep(restart_delay)
                else:
                    raise CommandError(
                        f"Server failed after {max_restarts} restart attempts: {e}"
                    )

    def start_server_process(self, port):
        """Start Django server process"""
        import sys

        cmd = [
            sys.executable,
            "manage.py",
            "runserver",
            f"localhost:{port}",
            "--noreload",  # We handle reloading through our auto-restart
        ]

        self.stdout.write(f'Starting server: {" ".join(cmd)}')

        return subprocess.Popen(
            cmd,
            cwd=settings.BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

    def run_server(self, port):
        """Run server normally without auto-restart"""
        from django.core.management import execute_from_command_line

        self.stdout.write(self.style.SUCCESS(f"Starting Django server on port {port}"))
        execute_from_command_line(["manage.py", "runserver", f"localhost:{port}"])
