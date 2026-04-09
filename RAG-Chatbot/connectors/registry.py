"""Connector factory -- instantiates the connector selected in .env."""

import os

from connectors.base import AssetConnector


def get_connector() -> AssetConnector:
    """Return the configured connector instance based on ASSET_CONNECTOR env var."""
    connector_type = os.getenv("ASSET_CONNECTOR", "mock").strip().lower()

    if connector_type == "mock":
        from connectors.mock import MockConnector

        return MockConnector()

    if connector_type == "nmap":
        from connectors.nmap import NmapConnector

        target = os.getenv("ASSET_CONNECTOR_NMAP_TARGET", "")
        if not target:
            raise ValueError(
                "ASSET_CONNECTOR=nmap requires ASSET_CONNECTOR_NMAP_TARGET "
                "to be set (e.g., '192.168.1.0/24')."
            )
        extra_args = os.getenv("ASSET_CONNECTOR_NMAP_ARGS", "")
        return NmapConnector(target=target, nmap_extra_args=extra_args)

    raise ValueError(
        f"Unknown ASSET_CONNECTOR='{connector_type}'. "
        "Supported values: mock, nmap"
    )
