"""Pinquark Common — shared library for all Python-based integrators.

Provides:
- schemas.wms        — Pinquark WMS REST API DTOs (Article, Document, Contractor, …)
- schemas.ecommerce  — Normalized e-commerce DTOs (Order, Product, StockItem, …)
- schemas.courier    — Normalized courier DTOs (CreateShipmentCommand, ShipmentResponse, …)
- schemas.common     — Platform-wide DTOs (Health, Error, Sync, Pagination)
- mapping            — Per-client configurable field mapping framework
"""

__version__ = "0.2.0"
