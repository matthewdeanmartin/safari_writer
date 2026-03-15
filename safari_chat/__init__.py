"""Public interface for Safari Chat."""

from safari_chat.app import SafariChatApp
from safari_chat.engine import parse_document, plan_response, retrieve_chunks
from safari_chat.main import build_parser, main, parse_args
from safari_chat.safety import (
    crisis_response,
    detect_crisis,
    detect_refusal,
    refusal_response,
)
from safari_chat.state import (
    ConversationNode,
    DistressLevel,
    ResponseMode,
    SafariChatState,
    TopicChunk,
)
from safari_chat.synonyms import apply_variation

__all__ = [
    "ConversationNode",
    "DistressLevel",
    "ResponseMode",
    "SafariChatApp",
    "SafariChatState",
    "TopicChunk",
    "apply_variation",
    "build_parser",
    "crisis_response",
    "detect_crisis",
    "detect_refusal",
    "main",
    "parse_args",
    "parse_document",
    "plan_response",
    "refusal_response",
    "retrieve_chunks",
]
