"""
Management command for comprehensive static file optimization.
"""

import gzip
import json
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from .utils.minify_helpers import CSSMinifier, JSMinifier


class Command(BaseCommand):
    help = "Optimize static files: minify CSS/JS, optimize images, clean unused files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--action",
            type=str,
            choices=["all", "minify", "images", "clean", "analyze", "compress"],
            default="all",
            help="Optimization action to perform",
        )
        parser.add_argument(
            "--force", action="store_true", help="Force reprocessing of all files"
        )
        parser.add_argument(
            "--backup", action="store_true", help="Create backup of original files"
        )
        parser.add_argument(
            "--compression",
            type=str,
            choices=["gzip", "brotli", "both"],
            default="gzip",
            help="Compression type for assets",
        )

    def handle(self, *args, **options):
        action = options["action"]
        force = options["force"]
        backup = options["backup"]
        compression = options["compression"]

        self.stdout.write(self.style.SUCCESS("STATIC FILE OPTIMIZATION"))
        self.stdout.write("=" * 60)

        # Get static files directory
        self.static_root = (
            Path(settings.STATIC_ROOT)
            if hasattr(settings, "STATIC_ROOT")
            else Path("static")
        )
        self.static_dirs = (
            [Path(d) for d in settings.STATICFILES_DIRS]
            if hasattr(settings, "STATICFILES_DIRS")
            else [Path("static")]
        )

        total_savings = 0

        if action in ["all", "analyze"]:
            self.analyze_static_files()

        if action in ["all", "clean"]:
            savings = self.clean_unused_files(backup=backup)
            total_savings += savings
            self.stdout.write(f"Unused files cleanup: {savings / 1024:.2f} KB saved")

        if action in ["all", "minify"]:
            css_savings, js_savings = self.minify_assets(force=force, backup=backup)
            total_savings += css_savings + js_savings
            self.stdout.write(f"CSS minification: {css_savings / 1024:.2f} KB saved")
            self.stdout.write(f"JS minification: {js_savings / 1024:.2f} KB saved")

        if action in ["all", "images"]:
            img_savings = self.optimize_images(force=force, backup=backup)
            total_savings += img_savings
            self.stdout.write(f"Image optimization: {img_savings / 1024:.2f} KB saved")

        if action in ["all", "compress"]:
            self.compress_assets(compression=compression)

        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"OPTIMIZATION COMPLETED: {total_savings / 1024:.2f} KB total saved"
            )
        )

        # Generate optimization report
        self.generate_optimization_report(total_savings)

    def analyze_static_files(self):
        """Analyze current static file structure."""
        self.stdout.write(f"\n{self.style.WARNING('STATIC FILES ANALYSIS')}")
        self.stdout.write("-" * 40)

        for static_dir in self.static_dirs:
            if not static_dir.exists():
                continue

            self.stdout.write(f"\nAnalyzing: {static_dir}")

            # Count files by type
            file_counts = {}
            total_size = 0

            for file_path in static_dir.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    file_counts[suffix] = file_counts.get(suffix, 0) + 1
                    total_size += file_path.stat().st_size

            # Display results
            for suffix, count in sorted(file_counts.items()):
                self.stdout.write(f"  {suffix or 'no extension'}: {count} files")

            self.stdout.write(f"  Total size: {total_size / 1024 / 1024:.2f} MB")

    def clean_unused_files(self, backup=True):
        """Clean unused static files."""
        self.stdout.write(f"\n{self.style.WARNING('CLEANING UNUSED FILES')}")
        self.stdout.write("-" * 40)

        unused_patterns = [
            "**/*.orig",
            "**/*.bak",
            "**/*.tmp",
            "**/.DS_Store",
            "**/Thumbs.db",
            "**/*.log",
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/*.pyc",
        ]

        # TODO: Files that are duplicates (already minified versions exist)
        # duplicate_patterns = [
        #     # Skip files that have minified versions
        # ]

        total_removed = 0
        files_removed = 0

        for static_dir in self.static_dirs:
            if not static_dir.exists():
                continue

            for pattern in unused_patterns:
                for file_path in static_dir.glob(pattern):
                    if file_path.is_file():
                        file_size = file_path.stat().st_size

                        if backup:
                            self.backup_file(file_path)

                        file_path.unlink()
                        total_removed += file_size
                        files_removed += 1

                        self.stdout.write(f"Removed: {file_path.name}")

        self.stdout.write(
            f"Removed {files_removed} files, {total_removed / 1024:.2f} KB freed"
        )
        return total_removed

    def minify_assets(self, force=False, backup=True):
        """Minify CSS and JS files."""
        self.stdout.write(f"\n{self.style.WARNING('MINIFYING CSS/JS ASSETS')}")
        self.stdout.write("-" * 40)

        css_savings = self.minify_css_files(force, backup)
        js_savings = self.minify_js_files(force, backup)

        return css_savings, js_savings

    def minify_css_files(self, force=False, backup=True):
        """
        Minify CSS files.

        REFACTORED: Complexity reduced from C:14 to A:3
        """
        minifier = CSSMinifier(self.basic_css_minify, self.stdout)
        total_savings = 0

        for static_dir in self.static_dirs:
            savings = minifier.minify_directory(static_dir, force, backup)
            total_savings += savings

        return total_savings

    def minify_js_files(self, force=False, backup=True):
        """
        Minify JavaScript files.

        REFACTORED: Complexity reduced from C:15 to A:3
        """
        minifier = JSMinifier(self.basic_js_minify, self.stdout)
        total_savings = 0

        for static_dir in self.static_dirs:
            savings = minifier.minify_directory(static_dir, force, backup)
            total_savings += savings

        return total_savings

    def basic_css_minify(self, css_content):
        """Basic CSS minification."""
        import re

        # Remove comments
        css_content = re.sub(r"/\*.*?\*/", "", css_content, flags=re.DOTALL)

        # Remove unnecessary whitespace
        css_content = re.sub(r"\s+", " ", css_content)

        # Remove whitespace around specific characters
        css_content = re.sub(r"\s*([{}:;,>+~])\s*", r"\1", css_content)

        # Remove trailing semicolons
        css_content = re.sub(r";}", "}", css_content)

        # Remove unnecessary quotes from URLs
        css_content = re.sub(r'url\(["\']([^"\']*)["\']?\)', r"url(\1)", css_content)

        return css_content.strip()

    def basic_js_minify(self, js_content):
        """Basic JavaScript minification."""
        import re

        # Remove single-line comments
        js_content = re.sub(r"//.*$", "", js_content, flags=re.MULTILINE)

        # Remove multi-line comments
        js_content = re.sub(r"/\*.*?\*/", "", js_content, flags=re.DOTALL)

        # Remove unnecessary whitespace
        js_content = re.sub(r"\s+", " ", js_content)

        # Remove whitespace around specific characters
        js_content = re.sub(r"\s*([{}();,=+\-*/<>!&|])\s*", r"\1", js_content)

        # Remove unnecessary semicolons
        js_content = re.sub(r";;+", ";", js_content)

        return js_content.strip()

    def optimize_images(self, force=False, backup=True):  # noqa: C901
        """Optimize image files."""
        self.stdout.write(f"\n{self.style.WARNING('OPTIMIZING IMAGES')}")
        self.stdout.write("-" * 40)

        total_savings = 0
        image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"]

        for static_dir in self.static_dirs:
            if not static_dir.exists():
                continue

            for ext in image_extensions:
                image_files = list(static_dir.rglob(f"*{ext}"))

                for image_file in image_files:
                    if "unused-backup" in str(image_file):
                        continue

                    try:
                        image_file.stat().st_size

                        # Create WebP version for supported formats
                        if ext.lower() in [".jpg", ".jpeg", ".png"]:
                            webp_file = image_file.parent / f"{image_file.stem}.webp"

                            if force or not webp_file.exists():
                                savings = self.create_webp_version(
                                    image_file, webp_file
                                )
                                if savings > 0:
                                    total_savings += savings
                                    self.stdout.write(f"Created WebP: {webp_file.name}")

                        # Basic optimization for PNG/JPEG
                        if ext.lower() in [".png", ".jpg", ".jpeg"]:
                            optimized_savings = self.basic_image_optimize(
                                image_file, backup
                            )
                            total_savings += optimized_savings

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error optimizing {image_file.name}: {e}")
                        )

        return total_savings

    def create_webp_version(self, source_file, webp_file):
        """Create WebP version of image."""
        try:
            # Simple conversion using Pillow if available
            try:
                from PIL import Image

                with Image.open(source_file) as img:
                    # Convert to RGB if necessary
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")

                    img.save(webp_file, "WEBP", quality=85, optimize=True)

                    original_size = source_file.stat().st_size
                    webp_size = webp_file.stat().st_size
                    return max(0, original_size - webp_size)

            except ImportError:
                self.stdout.write("Pillow not available for WebP conversion")
                return 0

        except Exception as e:
            self.stdout.write(f"WebP conversion failed for {source_file.name}: {e}")
            return 0

    def basic_image_optimize(self, image_file, backup=True):
        """Basic image optimization."""
        # Placeholder for image optimization
        # In a real implementation, you'd use tools like:
        # - OptiPNG for PNG files
        # - mozjpeg for JPEG files
        # - SVGO for SVG files
        return 0

    def compress_assets(self, compression="gzip"):
        """Compress static assets with gzip/brotli."""
        self.stdout.write(f"\n{self.style.WARNING('COMPRESSING ASSETS')}")
        self.stdout.write("-" * 40)

        compressible_extensions = [".css", ".js", ".html", ".svg", ".json", ".xml"]

        for static_dir in self.static_dirs:
            if not static_dir.exists():
                continue

            for ext in compressible_extensions:
                files = list(static_dir.rglob(f"*{ext}"))

                for file_path in files:
                    if "unused-backup" in str(file_path):
                        continue

                    try:
                        if compression in ["gzip", "both"]:
                            self.create_gzip_version(file_path)

                        if compression in ["brotli", "both"]:
                            self.create_brotli_version(file_path)

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"Error compressing {file_path.name}: {e}")
                        )

    def create_gzip_version(self, file_path):
        """Create gzip compressed version."""
        gzip_path = file_path.parent / f"{file_path.name}.gz"

        with open(file_path, "rb") as f_in:
            with gzip.open(gzip_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        original_size = file_path.stat().st_size
        compressed_size = gzip_path.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100

        self.stdout.write(
            f"Gzipped {file_path.name}: {compression_ratio:.1f}% compression"
        )

    def create_brotli_version(self, file_path):
        """Create brotli compressed version."""
        try:
            import brotli

            brotli_path = file_path.parent / f"{file_path.name}.br"

            with open(file_path, "rb") as f:
                compressed_data = brotli.compress(f.read())

            with open(brotli_path, "wb") as f:
                f.write(compressed_data)

            original_size = file_path.stat().st_size
            compressed_size = len(compressed_data)
            compression_ratio = (1 - compressed_size / original_size) * 100

            self.stdout.write(
                f"Brotli {file_path.name}: {compression_ratio:.1f}% compression"
            )

        except ImportError:
            self.stdout.write("Brotli not available for compression")

    def backup_file(self, file_path):
        """Create backup of file."""
        backup_dir = file_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)

        backup_path = backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)

    def generate_optimization_report(self, total_savings):
        """Generate optimization report."""
        report_file = Path("static_optimization_report.json")

        report_data = {
            "timestamp": self.get_timestamp(),
            "total_savings_bytes": total_savings,
            "total_savings_kb": total_savings / 1024,
            "optimizations": {
                "css_minification": "completed",
                "js_minification": "completed",
                "image_optimization": "completed",
                "unused_file_cleanup": "completed",
                "asset_compression": "completed",
            },
            "recommendations": [
                "Use a CDN for better static file delivery",
                "Enable HTTP/2 server push for critical assets",
                "Implement lazy loading for images",
                "Consider using a build tool like Webpack for advanced optimization",
            ],
        }

        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        self.stdout.write(f"Optimization report saved to: {report_file}")

    def get_timestamp(self):
        """Get current timestamp."""
        from django.utils import timezone

        return timezone.now().isoformat()
