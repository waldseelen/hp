"""
Static File Minification Helpers
================================

Helper classes for CSS and JS minification using Extract Class pattern.

Complexity reduced: C:14-15 → A:2-3 (main methods)
"""

import json
import shutil
from pathlib import Path
from typing import List, Tuple


class FileFilter:
    """
    Filter files for minification

    Complexity: A:3
    """

    @staticmethod
    def filter_css_files(static_dir: Path) -> List[Path]:
        """
        Get CSS files that need minification

        Complexity: A:3
        """
        if not static_dir.exists():
            return []

        css_files = list(static_dir.rglob("*.css"))
        # Skip already minified files and backup directories
        return [
            f
            for f in css_files
            if not f.name.endswith(".min.css") and "unused-backup" not in str(f)
        ]

    @staticmethod
    def filter_js_files(static_dir: Path) -> List[Path]:
        """
        Get JS files that need minification

        Complexity: A:4
        """
        if not static_dir.exists():
            return []

        js_files = list(static_dir.rglob("*.js"))
        # Skip already minified files, service worker, and backup directories
        return [
            f
            for f in js_files
            if not f.name.endswith(".min.js")
            and f.name != "sw.js"
            and "unused-backup" not in str(f)
        ]

    @staticmethod
    def should_skip_minification(
        source_file: Path, minified_file: Path, force: bool
    ) -> bool:
        """
        Check if minification should be skipped

        Complexity: A:3
        """
        if force:
            return False

        if not minified_file.exists():
            return False

        return minified_file.stat().st_mtime > source_file.stat().st_mtime


class BackupManager:
    """
    Manage file backups

    Complexity: A:2
    """

    @staticmethod
    def create_backup(source_file: Path) -> bool:
        """
        Create backup of source file

        Complexity: A:2
        """
        backup_dir = source_file.parent / "backups"
        if not backup_dir.exists():
            backup_dir.mkdir(exist_ok=True)

        try:
            shutil.copy2(source_file, backup_dir / source_file.name)
            return True
        except Exception:
            return False


class SourceMapGenerator:
    """
    Generate source maps for minified files

    Complexity: A:1
    """

    @staticmethod
    def generate(source_file: Path, minified_file: Path) -> dict:
        """
        Generate source map data structure

        Complexity: A:1
        """
        return {
            "version": 3,
            "sources": [source_file.name],
            "names": [],
            "mappings": "",
            "file": minified_file.name,
        }

    @staticmethod
    def write_source_map(map_file: Path, source_map: dict) -> bool:
        """
        Write source map to file

        Complexity: A:1
        """
        try:
            map_file.write_text(json.dumps(source_map), encoding="utf-8")
            return True
        except Exception:
            return False


class CompressionStats:
    """
    Calculate compression statistics

    Complexity: A:2
    """

    @staticmethod
    def calculate(original_size: int, minified_size: int) -> Tuple[int, float]:
        """
        Calculate savings and compression ratio

        Returns:
            (savings, compression_ratio)

        Complexity: A:2
        """
        savings = original_size - minified_size
        compression_ratio = (savings / original_size) * 100 if original_size > 0 else 0
        return savings, compression_ratio


class FileMinifier:
    """
    Base minifier class for CSS and JS files

    Complexity: A:5
    """

    def __init__(self, minify_func, stdout_writer):
        self.minify_func = minify_func
        self.stdout = stdout_writer
        self.file_filter = FileFilter()
        self.backup_manager = BackupManager()
        self.source_map_gen = SourceMapGenerator()
        self.stats_calc = CompressionStats()

    def minify_file(self, source_file: Path, backup: bool = True) -> Tuple[bool, int]:
        """
        Minify a single file

        Returns:
            (success, savings)

        Complexity: B:7
        """
        minified_file = (
            source_file.parent / f"{source_file.stem}.min{source_file.suffix}"
        )
        source_map_file = (
            source_file.parent / f"{source_file.stem}.min{source_file.suffix}.map"
        )

        try:
            # Read and minify
            original_content = source_file.read_text(encoding="utf-8")
            original_size = len(original_content.encode("utf-8"))

            minified_content = self.minify_func(original_content)
            minified_size = len(minified_content.encode("utf-8"))

            # Create backup if requested
            if backup:
                self.backup_manager.create_backup(source_file)

            # Write minified file
            minified_file.write_text(minified_content, encoding="utf-8")

            # Create source map
            source_map = self.source_map_gen.generate(source_file, minified_file)
            self.source_map_gen.write_source_map(source_map_file, source_map)

            # Calculate and display stats
            savings, compression_ratio = self.stats_calc.calculate(
                original_size, minified_size
            )

            self.stdout.write(
                f"Minified {source_file.name}: {compression_ratio:.1f}% reduction "
                f"({original_size} → {minified_size} bytes)"
            )

            return True, savings

        except Exception as e:
            # Use ERROR style if available
            error_msg = f"Error minifying {source_file.name}: {e}"
            if hasattr(self.stdout, "style"):
                self.stdout.write(self.stdout.style.ERROR(error_msg))
            else:
                self.stdout.write(error_msg)
            return False, 0


class CSSMinifier(FileMinifier):
    """
    CSS file minifier

    Complexity: A:4
    """

    def minify_directory(
        self, static_dir: Path, force: bool = False, backup: bool = True
    ) -> int:
        """
        Minify all CSS files in directory

        Complexity: A:4
        """
        total_savings = 0
        css_files = self.file_filter.filter_css_files(static_dir)

        for css_file in css_files:
            minified_file = css_file.parent / f"{css_file.stem}.min.css"

            # Skip if not needed
            if self.file_filter.should_skip_minification(
                css_file, minified_file, force
            ):
                continue

            success, savings = self.minify_file(css_file, backup)
            if success:
                total_savings += savings

        return total_savings


class JSMinifier(FileMinifier):
    """
    JavaScript file minifier

    Complexity: A:4
    """

    def minify_directory(
        self, static_dir: Path, force: bool = False, backup: bool = True
    ) -> int:
        """
        Minify all JS files in directory

        Complexity: A:4
        """
        total_savings = 0
        js_files = self.file_filter.filter_js_files(static_dir)

        for js_file in js_files:
            minified_file = js_file.parent / f"{js_file.stem}.min.js"

            # Skip if not needed
            if self.file_filter.should_skip_minification(js_file, minified_file, force):
                continue

            success, savings = self.minify_file(js_file, backup)
            if success:
                total_savings += savings

        return total_savings
