"""
Django management command to reindex search engine.

Usage:
    python manage.py reindex_search --all
    python manage.py reindex_search --model BlogPost
    python manage.py reindex_search --model BlogPost --model AITool
    python manage.py reindex_search --configure-only
"""

import time

from django.core.management.base import BaseCommand, CommandError

from apps.main.search_index import search_index_manager


class Command(BaseCommand):
    help = "Reindex all searchable models or specific models for MeiliSearch"

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Reindex all registered models",
        )
        parser.add_argument(
            "--model",
            action="append",
            help="Reindex specific model(s). Can be used multiple times.",
        )
        parser.add_argument(
            "--configure-only",
            action="store_true",
            help="Only configure index settings without indexing documents",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Number of documents per batch (default: 100)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed progress information",
        )

    def handle(self, *args, **options):  # noqa: C901
        """
        NOTE: High complexity (26) - scheduled for refactoring in Phase 19.
        See docs/development/technical-debt-complexity.md
        """
        start_time = time.time()

        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING("MeiliSearch Reindex Command"))
        self.stdout.write(self.style.WARNING("=" * 70))

        # Step 1: Configure index
        if options["configure_only"] or options["all"]:
            self.stdout.write("\n📐 Configuring search index...")

            try:
                success = search_index_manager.configure_index()
                if success:
                    self.stdout.write(
                        self.style.SUCCESS("✓ Index configuration updated")
                    )
                else:
                    self.stdout.write(self.style.ERROR("✗ Index configuration failed"))

                # Show index stats
                stats = search_index_manager.get_index_stats()
                self.stdout.write(
                    f"   Documents: {stats.get('number_of_documents', 0)}"
                )
                self.stdout.write(f"   Indexing: {stats.get('is_indexing', False)}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Configuration error: {e}"))
                raise CommandError(f"Failed to configure index: {e}")

        # If configure-only, stop here
        if options["configure_only"]:
            self.stdout.write(self.style.SUCCESS("\n✓ Configuration complete"))
            return

        # Step 2: Determine which models to reindex
        models_to_index = []

        if options["all"]:
            models_to_index = list(search_index_manager.model_registry.keys())
            self.stdout.write(
                f"\n🔄 Reindexing ALL models ({len(models_to_index)} models)..."
            )
        elif options["model"]:
            # Validate model names
            invalid_models = []
            for model_name in options["model"]:
                if model_name not in search_index_manager.model_registry:
                    invalid_models.append(model_name)
                else:
                    models_to_index.append(model_name)

            if invalid_models:
                available = ", ".join(search_index_manager.model_registry.keys())
                raise CommandError(
                    f"Invalid model(s): {', '.join(invalid_models)}.\n"
                    f"Available models: {available}"
                )

            self.stdout.write(f"\n🔄 Reindexing {len(models_to_index)} model(s)...")
        else:
            raise CommandError(
                "Please specify --all or --model <ModelName>.\n"
                "Available models: "
                + ", ".join(search_index_manager.model_registry.keys())
            )

        # Step 3: Reindex each model
        total_results = {
            "indexed": 0,
            "skipped": 0,
            "failed": 0,
        }

        for model_name in models_to_index:
            self.stdout.write(f"\n📦 Processing {model_name}...")

            try:
                model_config = search_index_manager.get_model_config(model_name)
                model_class = model_config["model"]

                # Get total count
                total_count = model_class.objects.count()
                self.stdout.write(f"   Total objects: {total_count}")

                if total_count == 0:
                    self.stdout.write(
                        self.style.WARNING("   ⚠ No objects found, skipping")
                    )
                    continue

                # Reindex
                model_start = time.time()
                results = search_index_manager.reindex_model(model_name)
                model_duration = time.time() - model_start

                # Update totals
                total_results["indexed"] += results["indexed"]
                total_results["skipped"] += results["skipped"]
                total_results["failed"] += results["failed"]

                # Show results
                if results["indexed"] > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✓ Indexed: {results["indexed"]}')
                    )
                if results["skipped"] > 0:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠ Skipped: {results["skipped"]}')
                    )
                if results["failed"] > 0:
                    self.stdout.write(
                        self.style.ERROR(f'   ✗ Failed: {results["failed"]}')
                    )

                # Performance info
                if options["verbose"] and results["indexed"] > 0:
                    docs_per_sec = results["indexed"] / model_duration
                    self.stdout.write(
                        f"   ⏱ Duration: {model_duration:.2f}s ({docs_per_sec:.1f} docs/sec)"
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ✗ Error: {e}"))
                if options["verbose"]:
                    import traceback

                    self.stdout.write(traceback.format_exc())

        # Step 4: Summary
        total_duration = time.time() - start_time

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.WARNING("Reindexing Summary"))
        self.stdout.write("=" * 70)

        self.stdout.write(
            self.style.SUCCESS(f'✓ Indexed:  {total_results["indexed"]:,}')
        )
        if total_results["skipped"] > 0:
            self.stdout.write(
                self.style.WARNING(f'⚠ Skipped:  {total_results["skipped"]:,}')
            )
        if total_results["failed"] > 0:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed:   {total_results["failed"]:,}')
            )

        self.stdout.write(f"\n⏱ Total duration: {total_duration:.2f}s")

        if total_results["indexed"] > 0:
            docs_per_sec = total_results["indexed"] / total_duration
            self.stdout.write(f"📊 Throughput: {docs_per_sec:.1f} docs/sec")

        # Check index stats again
        try:
            stats = search_index_manager.get_index_stats()
            self.stdout.write("\n📈 Final index stats:")
            self.stdout.write(
                f'   Documents in index: {stats.get("number_of_documents", 0):,}'
            )
            self.stdout.write(
                f'   Indexing in progress: {stats.get("is_indexing", False)}'
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"\n⚠ Could not fetch index stats: {e}")
            )

        self.stdout.write("\n" + "=" * 70)

        if total_results["failed"] > 0:
            self.stdout.write(self.style.ERROR("✗ Reindexing completed with errors"))
        else:
            self.stdout.write(
                self.style.SUCCESS("✓ Reindexing completed successfully!")
            )

        self.stdout.write("=" * 70 + "\n")
