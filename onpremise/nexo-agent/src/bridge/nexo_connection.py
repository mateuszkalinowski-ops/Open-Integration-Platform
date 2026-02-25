"""InsERT Nexo SDK connection manager via pythonnet.

Wraps the .NET MenedzerPolaczen / DanePolaczenia / Uchwyt lifecycle
into a Python-friendly interface with health monitoring and reconnection.
"""

import logging
import os
import threading
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Generator

logger = logging.getLogger(__name__)

_clr_initialized = False
_init_lock = threading.Lock()


class NexoProduct(str, Enum):
    SUBIEKT = "Subiekt"
    RACHMISTRZ = "Rachmistrz"
    REWIZOR = "Rewizor"
    GRATYFIKANT = "Gratyfikant"


class ConnectionStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


def _init_clr(sdk_bin_path: str) -> None:
    """Initialize the .NET CLR runtime and load InsERT Nexo assemblies."""
    global _clr_initialized
    if _clr_initialized:
        return

    with _init_lock:
        if _clr_initialized:
            return

        from pythonnet import load  # type: ignore[import-untyped]

        load("coreclr")

        import clr  # type: ignore[import-untyped]

        sdk_path = Path(sdk_bin_path)
        if not sdk_path.exists():
            raise FileNotFoundError(f"Nexo SDK Bin directory not found: {sdk_bin_path}")

        os.environ["PATH"] = str(sdk_path) + os.pathsep + os.environ.get("PATH", "")

        required_dlls = [
            "InsERT.Moria.API",
            "InsERT.Moria.ModelDanych",
            "InsERT.Moria.Sfera",
            "InsERT.Mox.Core",
        ]

        for dll_name in required_dlls:
            dll_path = sdk_path / f"{dll_name}.dll"
            if not dll_path.exists():
                raise FileNotFoundError(f"Required SDK assembly not found: {dll_path}")
            clr.AddReference(str(dll_path))
            logger.info("Loaded assembly: %s", dll_name)

        _clr_initialized = True
        logger.info("CLR runtime initialized with InsERT Nexo SDK from %s", sdk_bin_path)


class NexoConnection:
    """Manages a single connection to the InsERT Nexo database via the SDK."""

    def __init__(
        self,
        sql_server: str,
        sql_database: str,
        operator_login: str,
        operator_password: str,
        product: NexoProduct = NexoProduct.SUBIEKT,
        sdk_bin_path: str = r"C:\nexoSDK\Bin",
        windows_auth: bool = True,
        sql_username: str = "",
        sql_password: str = "",
        default_warehouse: str = "MAG",
        default_branch: str = "CENTRALA",
    ):
        self._sql_server = sql_server
        self._sql_database = sql_database
        self._operator_login = operator_login
        self._operator_password = operator_password
        self._product = product
        self._sdk_bin_path = sdk_bin_path
        self._windows_auth = windows_auth
        self._sql_username = sql_username
        self._sql_password = sql_password
        self._default_warehouse = default_warehouse
        self._default_branch = default_branch

        self._sfera: Any = None
        self._status = ConnectionStatus.DISCONNECTED
        self._last_ping: float = 0
        self._consecutive_failures: int = 0
        self._lock = threading.Lock()

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == ConnectionStatus.CONNECTED

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    @property
    def sfera(self) -> Any:
        if not self._sfera or not self.is_connected:
            raise ConnectionError("Not connected to InsERT Nexo. Call connect() first.")
        return self._sfera

    def connect(self) -> None:
        """Establish connection to InsERT Nexo via the SDK."""
        with self._lock:
            if self.is_connected:
                return

            self._status = ConnectionStatus.CONNECTING
            logger.info(
                "Connecting to InsERT Nexo: server=%s, db=%s, product=%s",
                self._sql_server,
                self._sql_database,
                self._product.value,
            )

            try:
                _init_clr(self._sdk_bin_path)

                from InsERT.Moria.Sfera import MenedzerPolaczen, DanePolaczenia  # type: ignore[import-not-found]
                from InsERT.Moria.API import ProductId  # type: ignore[import-not-found]

                if self._windows_auth:
                    dane_polaczenia = DanePolaczenia.Jawne(
                        self._sql_server,
                        self._sql_database,
                        True,
                    )
                else:
                    dane_polaczenia = DanePolaczenia.Jawne(
                        self._sql_server,
                        self._sql_database,
                        self._sql_username,
                        self._sql_password,
                    )

                product_id = getattr(ProductId, self._product.value)

                mp = MenedzerPolaczen()
                self._sfera = mp.Polacz(dane_polaczenia, product_id)
                self._sfera.ZalogujOperatora(self._operator_login, self._operator_password)

                self._setup_context()

                self._status = ConnectionStatus.CONNECTED
                self._consecutive_failures = 0
                self._last_ping = time.monotonic()
                logger.info("Connected to InsERT Nexo successfully")

            except Exception:
                self._status = ConnectionStatus.ERROR
                self._consecutive_failures += 1
                logger.exception("Failed to connect to InsERT Nexo")
                raise

    def _setup_context(self) -> None:
        """Set default warehouse and branch context."""
        if not self._sfera:
            return
        try:
            kontekst = self._sfera.Kontekst()
            if self._default_warehouse:
                kontekst.UstawMagazynWedlugSymbolu(self._default_warehouse)
            if self._default_branch:
                kontekst.UstawOddzialWedlugSymbolu(self._default_branch)
            logger.info(
                "Context set: warehouse=%s, branch=%s",
                self._default_warehouse,
                self._default_branch,
            )
        except Exception:
            logger.warning("Failed to set context (warehouse/branch may not exist)")

    def disconnect(self) -> None:
        """Disconnect from InsERT Nexo."""
        with self._lock:
            if self._sfera:
                try:
                    self._sfera.Dispose()
                except Exception:
                    logger.warning("Error during Nexo disconnect", exc_info=True)
                finally:
                    self._sfera = None
            self._status = ConnectionStatus.DISCONNECTED
            logger.info("Disconnected from InsERT Nexo")

    def ping(self) -> dict[str, Any]:
        """Verify the connection is alive by querying a lightweight entity."""
        start = time.monotonic()
        try:
            from InsERT.Moria.ModelDanych import IPodmioty  # type: ignore[import-not-found]

            podmioty = self.sfera.PodajObiektTypu[IPodmioty]()
            _ = podmioty.Dane.Wszystkie().Count
            latency_ms = round((time.monotonic() - start) * 1000, 1)
            self._last_ping = time.monotonic()
            self._consecutive_failures = 0

            return {
                "status": "ok",
                "latency_ms": latency_ms,
                "last_ping": self._last_ping,
            }
        except Exception as exc:
            latency_ms = round((time.monotonic() - start) * 1000, 1)
            self._consecutive_failures += 1
            return {
                "status": "error",
                "latency_ms": latency_ms,
                "error": str(exc),
                "consecutive_failures": self._consecutive_failures,
            }

    def reconnect(self) -> None:
        """Force reconnection."""
        logger.info("Reconnecting to InsERT Nexo...")
        self.disconnect()
        self.connect()

    def get_typed_object(self, interface_type: type) -> Any:
        """Get a typed service object from the Sfera handle (wrapper for PodajObiektTypu<T>)."""
        return self.sfera.PodajObiektTypu[interface_type]()

    @contextmanager
    def entity_scope(self, entity: Any) -> Generator[Any, None, None]:
        """Context manager that wraps a Nexo entity for safe disposal."""
        try:
            yield entity
        finally:
            try:
                if hasattr(entity, "Dispose"):
                    entity.Dispose()
            except Exception:
                logger.warning("Failed to dispose Nexo entity", exc_info=True)


class NexoConnectionPool:
    """Simple pool managing one primary connection with auto-reconnect."""

    def __init__(self, **connection_kwargs: Any):
        self._kwargs = connection_kwargs
        self._connection = NexoConnection(**connection_kwargs)

    @property
    def connection(self) -> NexoConnection:
        if not self._connection.is_connected:
            self._connection.connect()
        return self._connection

    def ensure_connected(self) -> NexoConnection:
        """Get the connection, reconnecting if necessary."""
        conn = self._connection
        if not conn.is_connected:
            try:
                conn.connect()
            except Exception:
                logger.error("Failed to establish Nexo connection")
                raise
        return conn

    def shutdown(self) -> None:
        self._connection.disconnect()
