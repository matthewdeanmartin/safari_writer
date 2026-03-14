"""Public interface for Safari Fed."""

from safari_fed.app import SafariFedApp
from safari_fed.client import (
    FedSyncResult,
    SafariFedClient,
    load_client_from_env,
    load_clients_from_env,
)
from safari_fed.config import (
    MastodonIdentity,
    load_default_identity,
    load_mastodon_identities,
)
from safari_fed.main import build_parser, main, parse_args
from safari_fed.state import (
    FOLDER_ORDER,
    FedPost,
    SafariFedExitRequest,
    SafariFedState,
    build_demo_state,
    render_post_for_writer,
    render_thread_for_writer,
)

__all__ = [
    "FOLDER_ORDER",
    "FedSyncResult",
    "FedPost",
    "MastodonIdentity",
    "SafariFedApp",
    "SafariFedClient",
    "SafariFedExitRequest",
    "SafariFedState",
    "build_demo_state",
    "build_parser",
    "load_client_from_env",
    "load_clients_from_env",
    "load_default_identity",
    "load_mastodon_identities",
    "main",
    "parse_args",
    "render_post_for_writer",
    "render_thread_for_writer",
]
