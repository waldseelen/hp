"""
Management command to publish scheduled blog posts
"""

import logging

from django.core.management.base import BaseCommand

from apps.blog.models import Post

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Publish scheduled blog posts that are ready"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be published without actually publishing",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]

        # Find posts ready to be published
        ready_posts = Post.objects.ready_to_publish()

        if not ready_posts.exists():
            if verbose:
                self.stdout.write(
                    self.style.SUCCESS("No scheduled posts ready for publishing.")
                )
            return

        published_count = 0

        for post in ready_posts:
            try:
                if dry_run:
                    self.stdout.write(
                        f"Would publish: '{post.title}' (scheduled for {post.published_at})"
                    )
                else:
                    # Update status to published
                    post.status = "published"
                    post.save(update_fields=["status"])

                    published_count += 1

                    if verbose:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Published: '{post.title}' (was scheduled for {post.published_at})"
                            )
                        )

                    logger.info(f"Auto-published post: {post.title} (ID: {post.pk})")

            except Exception as e:
                error_msg = f"Error publishing post '{post.title}': {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                logger.error(error_msg)

        if dry_run:
            self.stdout.write(
                f"Dry run complete. {ready_posts.count()} posts would be published."
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully published {published_count} posts.")
            )

            if published_count != ready_posts.count():
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: {ready_posts.count() - published_count} posts failed to publish."
                    )
                )
