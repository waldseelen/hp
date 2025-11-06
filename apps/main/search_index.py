"""
MeiliSearch Index Manager for Django Portfolio Project

This module provides centralized search index management with:
- Automatic document indexing/updating/deletion
- Content sanitization for XSS prevention
- Bulk indexing operations
- Index configuration management
- Error handling and logging
- Progress tracking for long-running operations

Usage:
    from apps.main.search_index import search_index_manager

    # Index a document
    search_index_manager.index_document(blog_post_instance)

    # Delete a document
    search_index_manager.delete_document('BlogPost', 42)

    # Bulk reindex all models
    search_index_manager.reindex_all()
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import NoReverseMatch, reverse

import meilisearch
from tqdm import tqdm

# Import sanitizer
from .sanitizer import ContentSanitizer

# Setup logging
logger = logging.getLogger(__name__)


class SearchIndexManager:
    """
    Centralized manager for MeiliSearch indexing operations.
    Handles document lifecycle, sanitization, and index configuration.
    """

    def __init__(self):
        """Initialize MeiliSearch client and configuration"""
        self.host = getattr(settings, "MEILISEARCH_HOST", "http://localhost:7700")
        self.master_key = getattr(settings, "MEILISEARCH_MASTER_KEY", None)
        self.index_name = getattr(
            settings, "MEILISEARCH_INDEX_NAME", "portfolio_search"
        )
        self.timeout = getattr(settings, "MEILISEARCH_TIMEOUT", 5)
        self.batch_size = getattr(settings, "MEILISEARCH_BATCH_SIZE", 100)

        if not self.master_key:
            raise ImproperlyConfigured(
                "MEILISEARCH_MASTER_KEY must be set in settings. "
                "Add MEILI_MASTER_KEY to your .env file."
            )

        # Initialize MeiliSearch client
        try:
            self.client = meilisearch.Client(self.host, self.master_key)
            self.index = self.client.index(self.index_name)
            logger.info(
                f"MeiliSearch client initialized: {self.host} -> {self.index_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize MeiliSearch client: {e}")
            raise

        # Model registry: maps model class names to indexing configuration
        self.model_registry = self._build_model_registry()

    def _build_model_registry(self) -> Dict[str, Dict]:
        """
        Build registry of searchable models with their field mappings.
        Returns dict: {ModelClassName: {config}}
        """
        from apps.main.models import (
            AITool,
            BlogPost,
            CybersecurityResource,
            PersonalInfo,
            SocialLink,
            UsefulResource,
        )

        registry = {
            "BlogPost": {
                "model": BlogPost,
                "fields": {
                    "title": {"weight": 10, "sanitize": False},
                    "slug": {"weight": 2, "sanitize": False},
                    "excerpt": {"weight": 7, "sanitize": "html"},
                    "content": {"weight": 5, "sanitize": "html"},
                    "meta_description": {"weight": 3, "sanitize": False},
                    "tags": {"weight": 8, "parse_tags": True},
                },
                "metadata": [
                    "id",
                    "status",
                    "is_featured",
                    "category",
                    "author",
                    "published_at",
                    "updated_at",
                    "view_count",
                    "reading_time",
                ],
                "url_pattern": "blog:detail",
                "url_field": "slug",
                "visibility_check": lambda obj: obj.status == "published",
                "category_display": lambda obj: (
                    obj.category.display_name if obj.category else None
                ),
                "search_category": "Blog Posts",
                "search_icon": "📝",
            },
            "AITool": {
                "model": AITool,
                "fields": {
                    "name": {"weight": 10, "sanitize": False},
                    "description": {"weight": 8, "sanitize": False},
                    "tags": {"weight": 7, "parse_tags": True},
                },
                "metadata": [
                    "id",
                    "category",
                    "is_featured",
                    "is_free",
                    "rating",
                    "is_visible",
                    "order",
                    "created_at",
                    "updated_at",
                    "url",
                ],
                "url_pattern": "main:ai",
                "url_field": None,
                "url_anchor": lambda obj: f"tool-{obj.id}",
                "visibility_check": lambda obj: obj.is_visible,
                "category_display": lambda obj: obj.get_category_display(),
                "search_category": "AI Tools",
                "search_icon": "🤖",
            },
            "UsefulResource": {
                "model": UsefulResource,
                "fields": {
                    "name": {"weight": 10, "sanitize": False},
                    "description": {"weight": 8, "sanitize": False},
                    "tags": {"weight": 7, "parse_tags": True},
                },
                "metadata": [
                    "id",
                    "type",
                    "category",
                    "is_featured",
                    "is_free",
                    "rating",
                    "is_visible",
                    "order",
                    "created_at",
                    "updated_at",
                    "url",
                ],
                "url_pattern": "main:useful",
                "url_field": None,
                "url_anchor": lambda obj: f"resource-{obj.id}",
                "visibility_check": lambda obj: obj.is_visible,
                "category_display": lambda obj: obj.get_category_display(),
                "search_category": "Useful Resources",
                "search_icon": "🔗",
            },
            "CybersecurityResource": {
                "model": CybersecurityResource,
                "fields": {
                    "title": {"weight": 10, "sanitize": False},
                    "description": {"weight": 8, "sanitize": False},
                    "content": {"weight": 6, "sanitize": "markdown"},
                    "tags": {"weight": 7, "parse_tags": True},
                },
                "metadata": [
                    "id",
                    "type",
                    "difficulty",
                    "severity_level",
                    "is_urgent",
                    "is_featured",
                    "is_visible",
                    "order",
                    "created_at",
                    "updated_at",
                    "url",
                ],
                "url_pattern": "main:cybersecurity",
                "url_field": None,
                "url_anchor": lambda obj: f"resource-{obj.id}",
                "visibility_check": lambda obj: obj.is_visible,
                "category_display": lambda obj: obj.get_type_display(),
                "search_category": "Cybersecurity",
                "search_icon": "🔒",
            },
            "PersonalInfo": {
                "model": PersonalInfo,
                "fields": {
                    "key": {"weight": 9, "sanitize": False},
                    "value": {"weight": 6, "sanitize": "auto"},  # Auto-detect type
                },
                "metadata": [
                    "id",
                    "type",
                    "is_visible",
                    "order",
                    "created_at",
                    "updated_at",
                ],
                "url_pattern": "main:personal",
                "url_field": None,
                "url_anchor": lambda obj: f"info-{obj.key}",
                "visibility_check": lambda obj: obj.is_visible,
                "category_display": lambda obj: obj.get_type_display(),
                "search_category": "Personal Info",
                "search_icon": "👤",
            },
            "SocialLink": {
                "model": SocialLink,
                "fields": {
                    "platform": {"weight": 8, "sanitize": False},
                    "description": {"weight": 5, "sanitize": False},
                },
                "metadata": [
                    "id",
                    "url",
                    "is_primary",
                    "is_visible",
                    "order",
                    "created_at",
                    "updated_at",
                ],
                "url_pattern": None,  # Use external URL
                "url_field": "url",
                "visibility_check": lambda obj: obj.is_visible,
                "category_display": lambda obj: obj.get_platform_display(),
                "search_category": "Social Links",
                "search_icon": "🔗",
            },
        }

        # Try to import Tool model (may not exist in all project versions)
        try:
            from apps.tools.models import Tool

            registry["Tool"] = {
                "model": Tool,
                "fields": {
                    "title": {"weight": 10, "sanitize": False},
                    "description": {"weight": 8, "sanitize": False},
                    "tags": {"weight": 7, "parse_tags": True},
                },
                "metadata": ["id", "is_visible", "created_at", "updated_at"],
                "url_pattern": "tools:tool_list",
                "url_field": None,
                "visibility_check": lambda obj: getattr(obj, "is_visible", True),
                "category_display": lambda obj: "Tools",
                "search_category": "Tools",
                "search_icon": "🔧",
            }
        except (ImportError, AttributeError):
            logger.info("Tool model not found, skipping from index registry")

        return registry

    def get_model_config(self, model_or_name: Union[Model, str]) -> Optional[Dict]:
        """Get configuration for a model by instance or class name"""
        if isinstance(model_or_name, str):
            model_name = model_or_name
        else:
            model_name = model_or_name.__class__.__name__

        return self.model_registry.get(model_name)

    def sanitize_content(self, content: str, sanitize_type: str) -> str:
        """
        Sanitize content based on type.

        Args:
            content: Raw content string
            sanitize_type: 'html', 'markdown', 'auto', or False

        Returns:
            Sanitized plain text string
        """
        if not content or not sanitize_type:
            return content or ""

        try:
            if sanitize_type == "html":
                return ContentSanitizer.sanitize_html(content, strip_tags=True)
            elif sanitize_type == "markdown":
                # Convert markdown to HTML, then strip tags
                html_content = ContentSanitizer.sanitize_markdown(content)
                return ContentSanitizer.sanitize_html(html_content, strip_tags=True)
            elif sanitize_type == "auto":
                # Auto-detect content type (for PersonalInfo)
                if "<" in content and ">" in content:
                    return ContentSanitizer.sanitize_html(content, strip_tags=True)
                else:
                    return content
            else:
                return content
        except Exception as e:
            logger.error(f"Sanitization error: {e}")
            return ""

    def parse_tags(self, tags: Union[str, list, None]) -> List[str]:
        """
        Parse tags from various formats into a clean list.

        Args:
            tags: Comma-separated string, list, or None

        Returns:
            List of cleaned tag strings (max 20 tags)
        """
        if not tags:
            return []

        if isinstance(tags, str):
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        elif isinstance(tags, list):
            tag_list = [str(tag).strip() for tag in tags if tag]
        else:
            return []

        # Limit to 20 tags, remove duplicates
        return list(dict.fromkeys(tag_list))[:20]

    def _extract_document_fields(
        self, obj: Model, config: Dict, model_name: str
    ) -> Dict[str, Any]:
        """
        Extract and process searchable fields from model instance.

        Args:
            obj: Django model instance
            config: Model configuration dict
            model_name: Model class name for logging

        Returns:
            Dict of processed field values
        """
        fields = {}

        for field_name, field_config in config["fields"].items():
            try:
                value = getattr(obj, field_name, None)

                if field_config.get("parse_tags"):
                    fields[field_name] = self.parse_tags(value)
                elif field_config.get("sanitize"):
                    fields[field_name] = self.sanitize_content(
                        value, field_config["sanitize"]
                    )
                else:
                    fields[field_name] = str(value) if value is not None else ""
            except Exception as e:
                logger.error(
                    f"Error extracting field {field_name} from {model_name}:{obj.id}: {e}"
                )
                fields[field_name] = ""

        return fields

    def _build_document_metadata(self, obj: Model, config: Dict) -> Dict[str, Any]:
        """
        Extract and process metadata fields from model instance.

        Args:
            obj: Django model instance
            config: Model configuration dict

        Returns:
            Dict of processed metadata values
        """
        metadata = {}

        for meta_field in config["metadata"]:
            try:
                value = getattr(obj, meta_field, None)

                # Handle datetime fields
                if isinstance(value, datetime):
                    metadata[meta_field] = int(value.timestamp())
                # Handle foreign keys
                elif hasattr(value, "id"):
                    metadata[meta_field] = value.id
                    # Also add display name if available
                    if hasattr(value, "display_name"):
                        metadata[f"{meta_field}_display"] = value.display_name
                    elif hasattr(value, "name"):
                        metadata[f"{meta_field}_display"] = value.name
                else:
                    metadata[meta_field] = value
            except Exception as e:
                logger.error(f"Error extracting metadata {meta_field}: {e}")

        return metadata

    def _generate_document_url(
        self, obj: Model, config: Dict, model_name: str
    ) -> Optional[str]:
        """
        Generate URL for document based on configuration.

        Args:
            obj: Django model instance
            config: Model configuration dict
            model_name: Model class name for logging

        Returns:
            Generated URL string or None
        """
        try:
            url = None

            if config.get("url_pattern"):
                if config.get("url_field"):
                    url_value = getattr(obj, config["url_field"])
                    url = reverse(config["url_pattern"], args=[url_value])
                else:
                    url = reverse(config["url_pattern"])

                # Add anchor if specified
                if config.get("url_anchor"):
                    url += f"#{config['url_anchor'](obj)}"
            elif config.get("url_field"):
                # Direct external URL
                url = getattr(obj, config["url_field"], None)

            return url
        except (NoReverseMatch, AttributeError) as e:
            logger.warning(f"Could not generate URL for {model_name}:{obj.id}: {e}")
            return None

    def _add_excerpt_field(self, document: Dict[str, Any]) -> None:
        """
        Add excerpt field to document if not present.
        Truncates description or content as fallback.

        Args:
            document: Document dict to modify in-place
        """
        if "excerpt" not in document:
            if "description" in document:
                document["excerpt"] = document["description"][:200]
            elif "content" in document:
                document["excerpt"] = document["content"][:200]

    def build_document(self, obj: Model) -> Optional[Dict[str, Any]]:
        """
        Build a search document from a Django model instance.

        Refactored to reduce complexity: C:27 → C:8
        Uses pipeline pattern: validate → extract → build → enhance

        Args:
            obj: Django model instance

        Returns:
            Dict ready for indexing, or None if object shouldn't be indexed
        """
        model_name = obj.__class__.__name__
        config = self.get_model_config(model_name)

        # Validation: Check configuration and visibility
        if not config:
            logger.warning(f"No configuration found for model: {model_name}")
            return None

        if config.get("visibility_check"):
            if not config["visibility_check"](obj):
                logger.debug(
                    f"Object {model_name}:{obj.id} is not visible, skipping index"
                )
                return None

        # Build base document structure
        document = {
            "id": f"{model_name}:{obj.id}",
            "model_type": model_name,
            "model_id": obj.id,
            "search_category": config.get("search_category", model_name),
            "search_icon": config.get("search_icon", "📄"),
        }

        # Extract and add searchable fields
        fields = self._extract_document_fields(obj, config, model_name)
        document.update(fields)

        # Extract and add metadata
        metadata = self._build_document_metadata(obj, config)
        document["metadata"] = metadata

        # Generate and add URL
        document["url"] = self._generate_document_url(obj, config, model_name)

        # Add category display name if configured
        if config.get("category_display"):
            try:
                document["category_display"] = config["category_display"](obj)
            except Exception as e:
                logger.error(f"Error getting category display: {e}")

        # Add excerpt field (fallback to description/content)
        self._add_excerpt_field(document)

        return document

    def index_document(self, obj: Model) -> bool:
        """
        Index a single document.

        Args:
            obj: Django model instance to index

        Returns:
            True if successful, False otherwise
        """
        try:
            document = self.build_document(obj)

            if not document:
                return False

            # Add/update document in index
            task = self.index.add_documents([document], primary_key="id")
            logger.info(
                f"Indexed {document['model_type']}:{document['model_id']} (task: {task['taskUid']})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to index document {obj.__class__.__name__}:{obj.id}: {e}"
            )
            return False

    def delete_document(self, model_name: str, object_id: int) -> bool:
        """
        Delete a document from the index.

        Args:
            model_name: Model class name (e.g., 'BlogPost')
            object_id: Object ID

        Returns:
            True if successful, False otherwise
        """
        try:
            document_id = f"{model_name}:{object_id}"
            task = self.index.delete_document(document_id)
            logger.info(f"Deleted {document_id} from index (task: {task['taskUid']})")
            return True

        except Exception as e:
            logger.error(f"Failed to delete document {model_name}:{object_id}: {e}")
            return False

    def bulk_index(
        self,
        objects: List[Model],
        batch_size: Optional[int] = None,
        show_progress: bool = False,
    ) -> Dict[str, int]:
        """
        Bulk index multiple documents with optional progress tracking.

        Args:
            objects: List of Django model instances
            batch_size: Number of documents per batch (default: self.batch_size)
            show_progress: Display progress bar using tqdm

        Returns:
            Dict with counts: {'indexed': N, 'skipped': M, 'failed': K}
        """
        batch_size = batch_size or self.batch_size
        results = {"indexed": 0, "skipped": 0, "failed": 0}

        # Build all documents
        documents = []
        objects_iter = (
            tqdm(objects, desc="Building documents", disable=not show_progress)
            if show_progress
            else objects
        )

        for obj in objects_iter:
            try:
                document = self.build_document(obj)
                if document:
                    documents.append(document)
                    results["indexed"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error(
                    f"Error building document for {obj.__class__.__name__}:{obj.id}: {e}"
                )
                results["failed"] += 1

        if not documents:
            logger.warning("No documents to index")
            return results

        # Index in batches
        num_batches = (len(documents) + batch_size - 1) // batch_size
        batch_iter = (
            tqdm(
                range(0, len(documents), batch_size),
                total=num_batches,
                desc="Indexing batches",
                disable=not show_progress,
            )
            if show_progress
            else range(0, len(documents), batch_size)
        )

        for i in batch_iter:
            batch = documents[i : i + batch_size]
            try:
                task = self.index.add_documents(batch, primary_key="id")
                logger.info(
                    f"Indexed batch {i // batch_size + 1}: {len(batch)} documents (task: {task['taskUid']})"
                )
            except Exception as e:
                logger.error(f"Failed to index batch {i // batch_size + 1}: {e}")
                results["failed"] += len(batch)
                results["indexed"] -= len(batch)

        return results

    def reindex_model(
        self, model_name: str, show_progress: bool = False
    ) -> Dict[str, int]:
        """
        Reindex all objects of a specific model.

        Args:
            model_name: Model class name (e.g., 'BlogPost')
            show_progress: Display progress bar during indexing

        Returns:
            Dict with indexing results
        """
        config = self.get_model_config(model_name)
        if not config:
            logger.error(f"No configuration for model: {model_name}")
            return {"indexed": 0, "skipped": 0, "failed": 0}

        model_class = config["model"]
        objects = model_class.objects.all()

        logger.info(f"Reindexing {model_name}: {objects.count()} objects")
        return self.bulk_index(list(objects), show_progress=show_progress)

    def reindex_all(self) -> Dict[str, Dict[str, int]]:
        """
        Reindex all registered models.

        Returns:
            Dict with results per model: {ModelName: {indexed: N, ...}}
        """
        results = {}

        for model_name in self.model_registry.keys():
            logger.info(f"Starting reindex for: {model_name}")
            results[model_name] = self.reindex_model(model_name)

        return results

    def configure_index(self) -> bool:
        """
        Configure index settings (searchable attributes, filters, etc.)
        Should be run once during setup or after index recreation.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Searchable attributes (priority order)
            self.index.update_searchable_attributes(
                [
                    "title",
                    "name",
                    "excerpt",
                    "description",
                    "tags",
                    "content",
                    "value",
                    "meta_description",
                    "platform",
                ]
            )

            # Filterable attributes
            self.index.update_filterable_attributes(
                [
                    "model_type",
                    "category",
                    "type",
                    "is_visible",
                    "is_featured",
                    "is_free",
                    "difficulty",
                    "severity_level",
                    "status",
                    "published_at",
                    "updated_at",
                    "search_category",
                ]
            )

            # Sortable attributes
            self.index.update_sortable_attributes(
                ["published_at", "updated_at", "view_count", "rating", "order"]
            )

            # Displayed attributes (all fields returned in search results)
            self.index.update_displayed_attributes(
                [
                    "id",
                    "model_type",
                    "model_id",
                    "title",
                    "name",
                    "excerpt",
                    "description",
                    "url",
                    "category_display",
                    "tags",
                    "metadata",
                    "search_category",
                    "search_icon",
                ]
            )

            # Ranking rules (with custom boosts)
            self.index.update_ranking_rules(
                [
                    "words",
                    "typo",
                    "proximity",
                    "attribute",
                    "sort",
                    "exactness",
                    "desc(metadata.is_featured)",
                    "desc(metadata.view_count)",
                    "desc(metadata.rating)",
                    "desc(metadata.published_at)",
                ]
            )

            # Stop words (common words to ignore)
            self.index.update_stop_words(
                [
                    "the",
                    "a",
                    "an",
                    "and",
                    "or",
                    "but",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "bir",
                    "ve",
                    "veya",
                    "ile",
                    "bu",
                    "şu",
                    "için",
                    "gibi",
                    "kadar",
                ]
            )

            logger.info("Index configuration updated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to configure index: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dict with index stats (document count, size, etc.)
        """
        try:
            stats = self.index.get_stats()
            return {
                "number_of_documents": stats.get("numberOfDocuments", 0),
                "is_indexing": stats.get("isIndexing", False),
                "field_distribution": stats.get("fieldDistribution", {}),
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}


# Global singleton instance
_search_index_manager = None


def get_search_index_manager():
    """Lazy-loaded singleton getter for SearchIndexManager."""
    global _search_index_manager
    if _search_index_manager is None:
        _search_index_manager = SearchIndexManager()
    return _search_index_manager


# For backwards compatibility, use a property-like lazy loader
class LazySearchIndexManager:
    def __getattr__(self, name):
        return getattr(get_search_index_manager(), name)

    def __setattr__(self, name, value):
        return setattr(get_search_index_manager(), name, value)


search_index_manager = LazySearchIndexManager()
