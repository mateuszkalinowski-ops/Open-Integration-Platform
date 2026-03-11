from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INTEGRATORS_ROOT = ROOT / "integrators"


def _entrypoints() -> list[Path]:
    app_files = sorted(INTEGRATORS_ROOT.glob("**/src/app.py"))
    main_files = sorted(INTEGRATORS_ROOT.glob("**/src/main.py"))
    return app_files + main_files


def test_all_connector_entrypoints_use_sdk_bridge() -> None:
    entrypoints = _entrypoints()
    assert entrypoints, "No connector entrypoints discovered"

    missing: list[str] = []
    for entrypoint in entrypoints:
        source = entrypoint.read_text(encoding="utf-8")
        if "augment_legacy_fastapi_app" not in source or "manifest_path=" not in source:
            missing.append(str(entrypoint.relative_to(ROOT)))

    assert not missing, f"Entrypoints missing SDK bridge wiring: {missing}"


def test_every_bridged_entrypoint_has_neighbor_manifest() -> None:
    missing: list[str] = []
    for entrypoint in _entrypoints():
        manifest = entrypoint.parent.parent / "connector.yaml"
        if not manifest.exists():
            missing.append(str(entrypoint.relative_to(ROOT)))

    assert not missing, f"Entrypoints missing connector.yaml next to version root: {missing}"
