from __future__ import annotations

from types import SimpleNamespace


def get_settings() -> SimpleNamespace:
    return SimpleNamespace(
        app_name="TerraYield Land Intelligence",
        app_host="127.0.0.1",
        app_port=8010,
        allowed_origins=["*"],
    )
