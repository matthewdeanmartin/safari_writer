"""State models for Safari Chat."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

__all__ = [
    "ConversationNode",
    "DistressLevel",
    "ResponseMode",
    "SafariChatState",
    "TopicChunk",
]


class DistressLevel(str, Enum):
    """Distress meter levels per spec section 8.4."""

    LOW = "LOW"
    GUARDED = "GUARDED"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ResponseMode(str, Enum):
    """Response modes per spec section 5.2."""

    GROUNDED = "grounded"
    REFLECTIVE = "reflective"
    CALLBACK = "callback"
    SAFETY = "safety"
    CLARIFICATION = "clarification"


@dataclass
class TopicChunk:
    """A single topic parsed from the Markdown help document."""

    chunk_id: int
    heading: str
    body: str
    keywords: list[str]
    raw_markdown: str


@dataclass
class ConversationNode:
    """A single turn in the conversation tree."""

    node_id: int
    parent_id: int | None
    speaker: str  # "user" or "bot"
    raw_text: str
    normalized_text: str
    emotion: str
    distress_level: DistressLevel
    retrieved_chunk_ids: list[int]
    intent: str
    callback_candidates: list[int]
    timestamp: float
    branch_depth: int


@dataclass
class SafariChatState:
    """Mutable state shared across Safari Chat screens."""

    document_path: Path | None = None
    chunks: list[TopicChunk] = field(default_factory=list)
    conversation: list[ConversationNode] = field(default_factory=list)
    current_branch_id: int | None = None
    distress_level: DistressLevel = DistressLevel.LOW
    distress_score: float = 0.0
    synonym_enabled: bool = True
    typing_speed: int = 0
    retrieval_strictness: float = 0.1
    next_node_id: int = 0

    def add_node(
        self,
        speaker: str,
        raw_text: str,
        *,
        retrieved_chunk_ids: list[int] | None = None,
        intent: str = "",
        emotion: str = "",
        callback_candidates: list[int] | None = None,
    ) -> ConversationNode:
        """Create and append a conversation node, returning it."""
        parent_id: int | None = None
        branch_depth = 0
        if self.conversation:
            parent_id = self.conversation[-1].node_id
            branch_depth = self.conversation[-1].branch_depth
            if speaker == "user" and self.conversation[-1].speaker == "bot":
                pass  # same branch depth
        node = ConversationNode(
            node_id=self.next_node_id,
            parent_id=parent_id,
            speaker=speaker,
            raw_text=raw_text,
            normalized_text=raw_text.lower().strip(),
            emotion=emotion,
            distress_level=self.distress_level,
            retrieved_chunk_ids=retrieved_chunk_ids or [],
            intent=intent,
            callback_candidates=callback_candidates or [],
            timestamp=time.time(),
            branch_depth=branch_depth,
        )
        self.conversation.append(node)
        self.next_node_id += 1
        return node
