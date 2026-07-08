"""Market domain package."""

# The market layer will contain scanner and technical-analysis services in the
# future; the current skeleton only defines stable boundaries.

from market.service import MarketService

__all__ = ["MarketService"]
