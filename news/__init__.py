"""News domain package."""

# The news layer is isolated so article acquisition and NLP pipelines can be
# added without affecting the rest of the application boundaries.

from news.service import NewsService

__all__ = ["NewsService"]
