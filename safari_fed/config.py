"""Configuration loading for Safari Fed Mastodon identities."""

from __future__ import annotations

from dataclasses import dataclass
import os
from os import PathLike
from pathlib import Path
from typing import Mapping

from dotenv import load_dotenv

__all__ = [
    "MastodonIdentity",
    "load_default_identity",
    "load_mastodon_identities",
]

_FIELDS = ("BASE_URL", "CLIENT_ID", "CLIENT_SECRET", "ACCESS_TOKEN")


@dataclass(frozen=True)
class MastodonIdentity:
    """Resolved credentials for one Mastodon identity."""

    name: str
    base_url: str
    access_token: str
    client_id: str | None = None
    client_secret: str | None = None

    @property
    def label(self) -> str:
        """Human-readable identity label for UI status lines."""

        host = self.base_url.removeprefix("https://").removeprefix("http://")
        return f"{self.name}@{host}"


def load_mastodon_identities(
    environ: Mapping[str, str] | None = None,
    dotenv_path: str | PathLike[str] | None = None,
) -> dict[str, MastodonIdentity]:
    """Load Mastodon identities from env vars and optional dotenv files."""

    if dotenv_path is None:
        load_dotenv()
    else:
        load_dotenv(dotenv_path=Path(dotenv_path), override=False)
    source = dict(os.environ if environ is None else environ)

    identities: dict[str, dict[str, str]] = {}
    for key, value in source.items():
        if not key.startswith("MASTODON_ID_"):
            continue
        remainder = key.removeprefix("MASTODON_ID_")
        for field in _FIELDS:
            suffix = f"_{field}"
            if remainder.endswith(suffix):
                name = remainder[: -len(suffix)]
                if name:
                    identities.setdefault(name, {})[field] = value
                break

    resolved: dict[str, MastodonIdentity] = {}
    for name, fields in identities.items():
        base_url = fields.get("BASE_URL", "").strip()
        access_token = fields.get("ACCESS_TOKEN", "").strip()
        if not base_url or not access_token:
            continue
        resolved[name] = MastodonIdentity(
            name=name,
            base_url=base_url,
            access_token=access_token,
            client_id=fields.get("CLIENT_ID"),
            client_secret=fields.get("CLIENT_SECRET"),
        )

    if resolved:
        return resolved

    legacy_base_url = source.get("MASTODON_BASE_URL", "").strip()
    legacy_access_token = source.get("MASTODON_ACCESS_TOKEN", "").strip()
    if not legacy_base_url or not legacy_access_token:
        return {}
    return {
        "LEGACY": MastodonIdentity(
            name="LEGACY",
            base_url=legacy_base_url,
            access_token=legacy_access_token,
            client_id=source.get("MASTODON_CLIENT_ID"),
            client_secret=source.get("MASTODON_CLIENT_SECRET"),
        )
    }


def load_default_identity(
    environ: Mapping[str, str] | None = None,
    dotenv_path: str | PathLike[str] | None = None,
) -> MastodonIdentity | None:
    """Choose the default Mastodon identity from the loaded config."""

    source = dict(os.environ if environ is None else environ)
    identities = load_mastodon_identities(source, dotenv_path=dotenv_path)
    if not identities:
        return None
    preferred = source.get("MASTODON_DEFAULT_ID", "").strip()
    if preferred and preferred in identities:
        return identities[preferred]
    if "MAIN" in identities:
        return identities["MAIN"]
    return identities[sorted(identities)[0]]
