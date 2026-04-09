"""Base class for all asset connectors."""

from abc import ABC, abstractmethod


class AssetConnector(ABC):
    """Interface that every asset connector must implement.

    Each connector returns a list of dicts matching the CSV template columns:
        name, type, vendor_product, network_zone, ip_or_subnet,
        role, managed_by, criticality, notes
    """

    @abstractmethod
    def fetch_assets(self) -> list[dict]:
        """Discover or generate asset records."""
        ...
