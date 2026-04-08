from __future__ import annotations


def patch_kombu() -> None:
    try:
        from ddtrace import patch
    except ImportError:
        return

    patch(kombu=True)
