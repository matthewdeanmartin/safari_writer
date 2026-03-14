"""ELIZA/RAG engine for Safari Chat.

Handles Markdown parsing, keyword retrieval, ELIZA-style reflection,
conversation tree management, distress scoring, and response planning.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from safari_chat.safety import (crisis_response, detect_crisis, detect_refusal,
                                refusal_response)
from safari_chat.state import (ConversationNode, DistressLevel, ResponseMode,
                               SafariChatState, TopicChunk)
from safari_chat.synonyms import apply_variation

__all__ = [
    "find_callback_candidates",
    "parse_document",
    "plan_response",
    "retrieve_chunks",
    "score_distress",
]

# ---------------------------------------------------------------------------
# Stopwords (small hardcoded set)
# ---------------------------------------------------------------------------

_STOPWORDS: set[str] = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "can",
    "need",
    "dare",
    "ought",
    "to",
    "of",
    "in",
    "for",
    "on",
    "with",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "between",
    "out",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "and",
    "but",
    "or",
    "nor",
    "not",
    "so",
    "yet",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "only",
    "own",
    "same",
    "than",
    "too",
    "very",
    "just",
    "because",
    "if",
    "when",
    "where",
    "how",
    "what",
    "which",
    "who",
    "whom",
    "this",
    "that",
    "these",
    "those",
    "i",
    "me",
    "my",
    "myself",
    "we",
    "our",
    "you",
    "your",
    "he",
    "him",
    "his",
    "she",
    "her",
    "it",
    "its",
    "they",
    "them",
    "their",
    "all",
    "any",
    "about",
    "up",
    "down",
}

# ---------------------------------------------------------------------------
# Distress keywords
# ---------------------------------------------------------------------------

_DISTRESS_KEYWORDS: set[str] = {
    "panic",
    "hopeless",
    "desperate",
    "stuck",
    "impossible",
    "hate",
    "angry",
    "furious",
    "terrible",
    "awful",
    "horrible",
    "miserable",
    "useless",
    "worthless",
    "broken",
    "ruined",
    "disaster",
    "nightmare",
    "screaming",
    "crying",
    "lost",
    "confused",
    "overwhelmed",
    "scared",
    "afraid",
    "terrified",
    "helpless",
    "trapped",
    "frustrated",
    "infuriating",
    "enraged",
    "livid",
}

# ---------------------------------------------------------------------------
# ELIZA reflection table
# ---------------------------------------------------------------------------

_REFLECTIONS: dict[str, str] = {
    "i": "you",
    "me": "you",
    "my": "your",
    "mine": "yours",
    "myself": "yourself",
    "am": "are",
    "i'm": "you are",
    "i've": "you have",
    "i'll": "you will",
    "i'd": "you would",
    "we": "you",
    "our": "your",
    "ours": "yours",
    "you": "I",
    "your": "my",
    "yours": "mine",
    "yourself": "myself",
    "you're": "I am",
    "you've": "I have",
    "you'll": "I will",
    "you'd": "I would",
}

# ---------------------------------------------------------------------------
# ELIZA patterns — help-desk flavoured
# ---------------------------------------------------------------------------

_ELIZA_PATTERNS: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(r"\bi need (.*)", re.IGNORECASE),
        [
            "What would finding {0} do for you?",
            "How long have you been looking for {0}?",
            "Let us see if the documentation covers {0}.",
        ],
    ),
    (
        re.compile(r"\bi can'?t (.*)", re.IGNORECASE),
        [
            "I am sorry that {0} feels impossible right now. Let us try another way.",
            "What happens when you try to {0}?",
            "That sounds frustrating. What step gets in the way of {0}?",
        ],
    ),
    (
        re.compile(r"\bi feel (.*)", re.IGNORECASE),
        [
            "When you feel {0}, what is the first thing you notice?",
            "I am sorry to hear you feel {0}. Let us work through it together.",
        ],
    ),
    (
        re.compile(r"\bi don'?t know (.*)", re.IGNORECASE),
        [
            "That is okay. Let us figure out {0} together.",
            "Not knowing {0} is perfectly normal. Where would you like to start?",
        ],
    ),
    (
        re.compile(r"\bi('m| am) (.*)", re.IGNORECASE),
        [
            "How long have you felt {1}?",
            "What do you think makes you feel {1}?",
        ],
    ),
    (
        re.compile(r"\bwhy (.*)", re.IGNORECASE),
        [
            "That is a fair question. Let me see if the documentation explains {0}.",
            "I understand your curiosity about {0}.",
        ],
    ),
    (
        re.compile(r"\bhow do i (.*)", re.IGNORECASE),
        [
            "Let me check if the help document covers how to {0}.",
            "Good question. Let us look for instructions on {0}.",
        ],
    ),
    (
        re.compile(r"\bwhat is (.*)", re.IGNORECASE),
        [
            "Let me search the help document for information about {0}.",
            "That is worth looking up. Let me check on {0}.",
        ],
    ),
    (
        re.compile(
            r"\b(nothing|everything)\s+(works|is broken|is wrong)", re.IGNORECASE
        ),
        [
            "I am terribly sorry. That sounds overwhelming. Can you describe what happened right before things broke?",
            "I understand that feeling. Let us start with one thing. What were you trying to do?",
            "I am sorry everything feels broken. What is the most urgent thing you need to fix?",
        ],
    ),
    (
        re.compile(
            r"\b(this|it)\s+(is|seems?)\s+(impossible|hopeless|broken|terrible|awful)",
            re.IGNORECASE,
        ),
        [
            "I am very sorry this feels {2}. You are not alone in finding this difficult. What specific part is tripping you up?",
            "I hear you. When something feels {2}, it helps to focus on just one small piece. Where would you like to start?",
        ],
    ),
    (
        re.compile(
            r"\b(hate|frustrated with|annoyed by|tired of)\s+(this|the|it)",
            re.IGNORECASE,
        ),
        [
            "I am truly sorry this is so aggravating. What is the part that frustrates you most?",
            "I understand your frustration. Can you tell me more about what is going wrong?",
            "That is completely understandable. Let us try to sort out the worst part first. What is it?",
        ],
    ),
    (
        re.compile(r"\bwhat (should|do) i do\b", re.IGNORECASE),
        [
            "That depends on where you are right now. Can you describe what you see on screen?",
            "Let us figure that out. What were you trying to accomplish?",
        ],
    ),
    (
        re.compile(r"\bi('m| am) (stuck|lost|confused)\b", re.IGNORECASE),
        [
            "I am sorry you feel {1}. What is the last thing you tried?",
            "That is okay. Being {1} is normal with software like this. What screen are you on right now?",
            "Let us get you unstuck. Can you describe where you are in the program?",
        ],
    ),
    (
        re.compile(r"\bhelp\b", re.IGNORECASE),
        [
            "I am here to help. What are you struggling with?",
            "Of course. Tell me what is giving you trouble.",
        ],
    ),
    (
        re.compile(r"\bthank(s| you)\b", re.IGNORECASE),
        [
            "You are welcome. Is there anything else I can help with?",
            "Glad I could help. Let me know if anything else comes up.",
        ],
    ),
    (
        re.compile(r"\b(hi|hello|hey)\b", re.IGNORECASE),
        [
            "Hello! How can I help you today?",
            "Hi there. What would you like to know?",
        ],
    ),
    (
        re.compile(r"\b(bye|goodbye|quit|exit)\b", re.IGNORECASE),
        [
            "Goodbye. I hope this was helpful.",
            "Take care. Come back any time you need help.",
        ],
    ),
]

# Fallback responses when no pattern matches and retrieval is weak.
_FALLBACKS: list[str] = [
    "Tell me more about that. What were you trying to do?",
    "What aspect feels most difficult? I would like to help if I can.",
    "Could you say a bit more about what you mean? I want to point you in the right direction.",
    "I want to help. Can you describe the problem differently?",
    "I am not sure I follow. Could you try asking in a different way?",
    "I did not quite catch that. What is the main thing you need help with?",
]

# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------


def parse_document(text: str) -> list[TopicChunk]:
    """Split a Markdown document on ``---`` delimiters into topic chunks."""
    raw_chunks = re.split(r"^\s*---\s*$", text, flags=re.MULTILINE)
    result: list[TopicChunk] = []
    for _idx, raw in enumerate(raw_chunks):
        body = raw.strip()
        if not body:
            continue
        heading = ""
        heading_match = re.search(r"^#{1,6}\s+(.+)$", body, re.MULTILINE)
        if heading_match:
            heading = heading_match.group(1).strip()

        # Extract keywords from headings and emphasised terms.
        kw_tokens: list[str] = []
        if heading:
            kw_tokens.extend(_tokenize(heading))
        for emph in re.findall(r"\*{1,2}([^*]+)\*{1,2}", body):
            kw_tokens.extend(_tokenize(emph))
        # Also pull words from sub-headings.
        for sub in re.findall(r"^#{1,6}\s+(.+)$", body, re.MULTILINE):
            kw_tokens.extend(_tokenize(sub))

        # Extract branches (questions that link to other sections).
        branches: list[tuple[str, str]] = []
        for match in re.finditer(
            r"^\s*[-*]\s*\[([^\]]+)\]\(#([^\)]+)\)", body, re.MULTILINE
        ):
            label, target = match.groups()
            branches.append((label.strip(), target.strip()))

        keywords = sorted(set(kw_tokens) - _STOPWORDS)
        result.append(
            TopicChunk(
                chunk_id=len(result),
                heading=heading,
                body=body,
                keywords=keywords,
                raw_markdown=raw,
                branches=branches,
            )
        )
    return result


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def retrieve_chunks(
    query: str,
    chunks: list[TopicChunk],
    *,
    top_n: int = 3,
    threshold: float = 0.1,
) -> list[tuple[TopicChunk, float]]:
    """Rank *chunks* against *query* using keyword overlap scoring."""
    if not chunks:
        return []

    query_tokens = set(_tokenize(query)) - _STOPWORDS
    if not query_tokens:
        return []

    # Compute document frequency for IDF-style weighting.
    doc_freq: Counter[str] = Counter()
    for chunk in chunks:
        body_tokens = set(_tokenize(chunk.body))
        for tok in query_tokens:
            if tok in body_tokens or tok in chunk.keywords:
                doc_freq[tok] += 1

    scored: list[tuple[TopicChunk, float]] = []
    for chunk in chunks:
        body_tokens = set(_tokenize(chunk.body))
        score = 0.0
        for tok in query_tokens:
            present_in_body = tok in body_tokens
            present_in_kw = tok in chunk.keywords
            if not (present_in_body or present_in_kw):
                continue
            idf = 1.0 / math.log(1.0 + doc_freq.get(tok, 0))
            weight = idf
            if present_in_kw:
                weight *= 2.0  # heading/emphasis bonus
            if tok in _tokenize(chunk.heading):
                weight *= 2.0  # direct heading match bonus
            score += weight
        if score >= threshold:
            scored.append((chunk, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:top_n]


# ---------------------------------------------------------------------------
# ELIZA reflection
# ---------------------------------------------------------------------------


def _reflect(text: str) -> str:
    """Apply pronoun reflection."""
    tokens = text.lower().split()
    reflected = [_REFLECTIONS.get(tok, tok) for tok in tokens]
    return " ".join(reflected)


def _eliza_respond(text: str) -> str | None:
    """Try ELIZA pattern matching and return a filled response or ``None``."""
    for pattern, responses in _ELIZA_PATTERNS:
        match = pattern.search(text)
        if match:
            groups = [_reflect(g) for g in match.groups()]
            template = responses[hash(text) % len(responses)]
            try:
                return template.format(*groups)
            except (IndexError, KeyError):
                return template
    return None


# ---------------------------------------------------------------------------
# Distress scoring
# ---------------------------------------------------------------------------

_DISTRESS_LEVELS: list[tuple[float, DistressLevel]] = [
    (0.8, DistressLevel.CRITICAL),
    (0.6, DistressLevel.HIGH),
    (0.4, DistressLevel.ELEVATED),
    (0.2, DistressLevel.GUARDED),
    (0.0, DistressLevel.LOW),
]


def score_distress(
    user_input: str, state: SafariChatState
) -> tuple[DistressLevel, float]:
    """Compute the distress level from current input and conversation state."""
    tokens = set(_tokenize(user_input))
    score = 0.0

    # Keyword component (weight 0.3).
    kw_hits = tokens & _DISTRESS_KEYWORDS
    if kw_hits:
        score += 0.3 * min(len(kw_hits) / 3.0, 1.0)

    # Punctuation / caps intensity (weight 0.1).
    excl_ratio = user_input.count("!") / max(len(user_input), 1)
    words = user_input.split()
    caps_ratio = sum(1 for w in words if w.isupper() and len(w) > 1) / max(
        len(words), 1
    )
    score += 0.1 * min(excl_ratio * 10 + caps_ratio, 1.0)

    # Repeated failed retrievals (weight 0.2).
    recent_bot = [n for n in state.conversation[-10:] if n.speaker == "bot"]
    consecutive_empty = 0
    for node in reversed(recent_bot):
        if not node.retrieved_chunk_ids:
            consecutive_empty += 1
        else:
            break
    score += 0.2 * min(consecutive_empty / 4.0, 1.0)

    # Crisis phrase bump — must dominate the score.
    if detect_crisis(user_input):
        score = max(score + 0.7, 0.85)

    # Carry forward some of the previous score (momentum).
    score = 0.8 * score + 0.2 * state.distress_score
    score = max(0.0, min(score, 1.0))

    level = DistressLevel.LOW
    for thresh, lvl in _DISTRESS_LEVELS:
        if score >= thresh:
            level = lvl
            break

    return level, score


# ---------------------------------------------------------------------------
# Callback detection
# ---------------------------------------------------------------------------


def find_callback_candidates(state: SafariChatState, current_text: str) -> list[int]:
    """Find prior user nodes worth referencing as callbacks."""
    current_tokens = set(_tokenize(current_text)) - _STOPWORDS
    if not current_tokens or len(state.conversation) < 6:
        return []

    # Skip the last 3 user turns to avoid immediate echo.
    user_nodes = [n for n in state.conversation if n.speaker == "user"]
    candidates = user_nodes[:-3] if len(user_nodes) > 3 else []

    scored: list[tuple[int, float]] = []
    for node in candidates:
        node_tokens = set(_tokenize(node.raw_text)) - _STOPWORDS
        overlap = current_tokens & node_tokens
        if overlap:
            score = len(overlap) / max(len(current_tokens), 1)
            scored.append((node.node_id, score))

    scored.sort(key=lambda p: p[1], reverse=True)
    return [nid for nid, _ in scored[:2] if _ > 0.3]


# ---------------------------------------------------------------------------
# Intent detection (simple heuristic)
# ---------------------------------------------------------------------------


def _detect_intent(text: str) -> str:
    """Classify user intent with simple keyword heuristics."""
    lower = text.lower().strip()
    words = set(re.findall(r"[a-z']+", lower))
    if lower.endswith("?") or lower.startswith(
        ("how", "what", "why", "where", "when", "who", "can")
    ):
        return "question"
    if words & {
        "frustrated",
        "frustrating",
        "angry",
        "hate",
        "annoying",
        "impossible",
        "ugh",
    }:
        return "frustration"
    if (
        words & {"hi", "hello", "hey"}
        or "good morning" in lower
        or "good evening" in lower
    ):
        return "greeting"
    if words & {"bye", "goodbye", "quit", "exit"} or "see you" in lower:
        return "farewell"
    if words & {"thanks"} or "thank you" in lower or "appreciate" in lower:
        return "gratitude"
    return "statement"


# ---------------------------------------------------------------------------
# Emotion detection (simple keyword)
# ---------------------------------------------------------------------------


def _detect_emotion(text: str) -> str:
    """Rough emotion label from keyword presence."""
    lower = text.lower()
    if any(
        w in lower for w in ("angry", "furious", "livid", "hate", "rage", "enraged")
    ):
        return "anger"
    if any(w in lower for w in ("sad", "depressed", "miserable", "hopeless", "crying")):
        return "sadness"
    if any(w in lower for w in ("scared", "afraid", "terrified", "panic", "anxious")):
        return "fear"
    if any(w in lower for w in ("confused", "lost", "bewildered", "don't understand")):
        return "confusion"
    if any(w in lower for w in ("frustrated", "annoying", "aggravating", "stuck")):
        return "frustration"
    if any(w in lower for w in ("happy", "glad", "great", "thanks", "thank")):
        return "positive"
    return "neutral"


# ---------------------------------------------------------------------------
# Response planner — the main entry point
# ---------------------------------------------------------------------------


def plan_response(
    user_input: str, state: SafariChatState
) -> tuple[ResponseMode, str, list[int]]:
    """Process *user_input* and return ``(mode, response_text, chunk_ids)``.

    Follows the spec response planning order (section 14.2):
    1. Check crisis / self-harm rules.
    2. Evaluate distress level.
    3. Check for callback opportunity.
    4. Evaluate retrieval confidence.
    5. Build response.
    6. Apply synonym variation.
    7. Enforce tone and safety constraints.
    """
    # Record user node.
    intent = _detect_intent(user_input)
    emotion = _detect_emotion(user_input)
    callbacks = find_callback_candidates(state, user_input)

    # 1. Crisis / safety check.
    if detect_refusal(user_input):
        state.add_node("user", user_input, intent="refusal", emotion=emotion)
        resp = refusal_response()
        state.add_node("bot", resp, intent="safety")
        return ResponseMode.SAFETY, resp, []

    if detect_crisis(user_input):
        state.distress_level = DistressLevel.CRITICAL
        state.distress_score = 1.0
        state.add_node("user", user_input, intent="crisis", emotion=emotion)
        resp = crisis_response()
        state.add_node("bot", resp, intent="safety")
        return ResponseMode.SAFETY, resp, []

    # 2. Distress scoring.
    level, dscore = score_distress(user_input, state)
    state.distress_level = level
    state.distress_score = dscore

    # Record user node with metadata.
    state.add_node(
        "user",
        user_input,
        intent=intent,
        emotion=emotion,
        callback_candidates=callbacks,
    )

    # 3. Exact branch match check.
    last_bot = next(
        (n for n in reversed(state.conversation[:-1]) if n.speaker == "bot"), None
    )
    if last_bot and last_bot.retrieved_chunk_ids:
        for cid in last_bot.retrieved_chunk_ids:
            chunk = next((c for c in state.chunks if c.chunk_id == cid), None)
            if chunk:
                for label, target in chunk.branches:
                    if user_input.lower().strip() == label.lower().strip():
                        target_chunk = next(
                            (
                                c
                                for c in state.chunks
                                if c.heading.lower() == target.lower()
                            ),
                            None,
                        )
                        if target_chunk:
                            resp = _build_grounded_response(
                                target_chunk, user_input, "statement"
                            )
                            resp = _maybe_vary(resp, state)
                            state.add_node(
                                "bot",
                                resp,
                                retrieved_chunk_ids=[target_chunk.chunk_id],
                                intent="branch",
                            )
                            return ResponseMode.GROUNDED, resp, [target_chunk.chunk_id]

    # 4. Callback opportunity.
    if callbacks and len(state.conversation) > 8:
        cb_node = _find_node(state, callbacks[0])
        if cb_node:
            resp = _build_callback_response(cb_node, user_input)
            resp = _maybe_vary(resp, state)
            chunk_ids: list[int] = []
            state.add_node(
                "bot", resp, retrieved_chunk_ids=chunk_ids, intent="callback"
            )
            return ResponseMode.CALLBACK, resp, chunk_ids

    # 4. Try ELIZA pattern matching first for frustration/emotional input,
    # so vague venting doesn't get a false-positive retrieval hit.
    if intent in ("frustration", "statement"):
        eliza_resp = _eliza_respond(user_input)
        if eliza_resp:
            resp = eliza_resp
            resp = _maybe_vary(resp, state)
            state.add_node("bot", resp, intent="reflective")
            return ResponseMode.REFLECTIVE, resp, []

    # 5. Retrieval.
    results = retrieve_chunks(
        user_input,
        state.chunks,
        threshold=state.retrieval_strictness,
    )
    retrieved_ids = [c.chunk_id for c, _ in results]

    # 6. Build response from retrieval.
    if results:
        best_chunk = results[0][0]
        resp = _build_grounded_response(best_chunk, user_input, intent)
        resp = _maybe_vary(resp, state)
        state.add_node(
            "bot", resp, retrieved_chunk_ids=retrieved_ids, intent="grounded"
        )
        return ResponseMode.GROUNDED, resp, retrieved_ids

    # 7. Try ELIZA pattern matching for remaining intents.
    eliza_resp = _eliza_respond(user_input)
    if eliza_resp:
        resp = eliza_resp
        resp = _maybe_vary(resp, state)
        state.add_node("bot", resp, intent="reflective")
        return ResponseMode.REFLECTIVE, resp, []

    # Fallback.
    resp = _fallback_response(user_input, state)
    resp = _maybe_vary(resp, state)
    state.add_node("bot", resp, intent="clarification")
    return ResponseMode.CLARIFICATION, resp, []


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    """Lowercase and split into word tokens, stripping punctuation."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _find_node(state: SafariChatState, node_id: int) -> ConversationNode | None:
    for node in state.conversation:
        if node.node_id == node_id:
            return node
    return None


def _build_grounded_response(chunk: TopicChunk, user_input: str, intent: str) -> str:
    """Summarise a retrieved topic chunk in a conversational way."""
    body = chunk.body
    # Strip markdown headings and branch links from the excerpt.
    lines = []
    for ln in body.splitlines():
        if ln.strip().startswith("#"):
            continue
        if re.search(r"^\s*[-*]\s*\[([^\]]+)\]\(#([^\)]+)\)", ln):
            continue
        lines.append(ln)
    excerpt = "\n".join(ln for ln in lines if ln.strip())

    prefix = ""
    if intent == "frustration":
        prefix = "I am sorry this is so frustrating. "
    elif intent == "question":
        prefix = "Good question. "

    topic_ref = f'I found help under "{chunk.heading}".\n\n' if chunk.heading else ""

    # Add branches if present.
    if chunk.branches:
        branch_lines = ["\nWould you like to know more about:"]
        for label, _ in chunk.branches:
            branch_lines.append(f"- {label}")
        excerpt += "\n" + "\n".join(branch_lines)

    followup = _pick_followup(intent)
    return f"{prefix}{topic_ref}{excerpt}\n\n{followup}"


# Follow-up questions appended to grounded responses.
_FOLLOWUPS_QUESTION: list[str] = [
    "Does that answer your question?",
    "Would you like me to explain any of that further?",
    "Is there a specific part you would like more detail on?",
    "Did that help, or shall I look for something else?",
]

_FOLLOWUPS_FRUSTRATION: list[str] = [
    "Would it help to walk through this one step at a time?",
    "What part is giving you the most trouble?",
    "Is there a specific step where things go wrong?",
    "Take a breath. Which piece would you like to tackle first?",
]

_FOLLOWUPS_GENERAL: list[str] = [
    "Is there anything else I can help with?",
    "Let me know if you need more detail on any of that.",
    "What else would you like to know?",
    "Feel free to ask if something is unclear.",
]

_FOLLOWUP_COUNTER: int = 0


def _pick_followup(intent: str) -> str:
    """Pick a rotating follow-up question based on intent."""
    global _FOLLOWUP_COUNTER  # noqa: PLW0603
    _FOLLOWUP_COUNTER += 1
    if intent == "frustration":
        pool = _FOLLOWUPS_FRUSTRATION
    elif intent == "question":
        pool = _FOLLOWUPS_QUESTION
    else:
        pool = _FOLLOWUPS_GENERAL
    return pool[_FOLLOWUP_COUNTER % len(pool)]


def _build_callback_response(cb_node: ConversationNode, current_input: str) -> str:
    """Reference an earlier user statement."""
    earlier = cb_node.raw_text
    if len(earlier) > 80:
        earlier = earlier[:77] + "..."
    return (
        f'Earlier you mentioned: "{earlier}" '
        f"Is this related to what you are experiencing now?"
    )


def _fallback_response(user_input: str, state: SafariChatState) -> str:
    """Pick a fallback response, avoiding immediate repeats."""
    # Use the conversation length to rotate through fallbacks.
    idx = len(state.conversation) % len(_FALLBACKS)
    base = _FALLBACKS[idx]
    if state.distress_level in (DistressLevel.HIGH, DistressLevel.CRITICAL):
        return (
            "I am sorry I could not find help on that in the documentation. "
            "Please tell me more so I can try to help."
        )
    if state.chunks:
        return (
            f"I could not find a clear answer in the help document. {base} "
            "I will keep trying."
        )
    return base


def _maybe_vary(text: str, state: SafariChatState) -> str:
    """Apply synonym variation if enabled."""
    if not state.synonym_enabled:
        return text
    seed = len(state.conversation)
    return apply_variation(text, seed=seed)
