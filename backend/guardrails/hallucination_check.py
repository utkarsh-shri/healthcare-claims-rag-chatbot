"""
guardrails/hallucination_check.py

Source-grounding validator that verifies the LLM's answer is grounded
in the retrieved context documents, reducing hallucination risk in
healthcare claims responses.
"""

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GroundingResult:
    """Result of a hallucination / grounding check."""
    is_grounded: bool
    confidence: float  # 0.0 to 1.0
    grounded_sentences: list[str] = field(default_factory=list)
    ungrounded_sentences: list[str] = field(default_factory=list)
    warning_message: str = ""


def _tokenize_to_words(text: str) -> set[str]:
    """
    Simple word tokenizer that lowercases and strips punctuation.
    Used for overlap-based grounding check.
    """
    words = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    # Filter out common stop words to focus on meaningful terms
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "of", "to", "in", "for",
        "on", "with", "at", "by", "from", "up", "about", "into", "through",
        "and", "or", "but", "if", "then", "that", "this", "these", "those",
        "it", "its", "he", "she", "they", "we", "you", "i", "my", "your",
        "his", "her", "their", "our", "not", "no", "so", "as", "also",
        "which", "who", "what", "when", "where", "how", "all", "any",
    }
    return {w for w in words if w not in stop_words and len(w) > 2}


def _sentence_overlap_score(sentence: str, context: str) -> float:
    """
    Calculate what fraction of meaningful words in `sentence` appear in `context`.

    Args:
        sentence: A sentence from the LLM answer.
        context:  The full concatenated retrieved context.

    Returns:
        Float between 0.0 and 1.0 — higher means better grounding.
    """
    sentence_words = _tokenize_to_words(sentence)
    context_words = _tokenize_to_words(context)

    if not sentence_words:
        return 1.0  # Empty sentences are trivially grounded

    overlap = sentence_words & context_words
    return len(overlap) / len(sentence_words)


# Threshold: a sentence with >40% keyword overlap is considered grounded
SENTENCE_GROUNDING_THRESHOLD = 0.40

# Minimum fraction of sentences that must be grounded for the answer to pass
ANSWER_GROUNDING_THRESHOLD = 0.70

# Phrases that always indicate the model is appropriately declining
SAFE_DECLINE_PHRASES = [
    "i don't have that information",
    "i do not have that information",
    "not in my knowledge base",
    "please consult your pbm administrator",
    "i cannot find",
    "i could not find",
    "not available in the context",
]


def check_grounding(answer: str, context_chunks: list[str]) -> GroundingResult:
    """
    Verify that the LLM answer is grounded in the retrieved context.

    Strategy:
    1. Split the answer into sentences.
    2. For each sentence, compute keyword overlap with the combined context.
    3. Flag sentences with low overlap as potentially ungrounded.
    4. If >30% of sentences are ungrounded, mark the overall answer as suspect.

    This is a lightweight heuristic check — not a semantic similarity check.
    It is intentionally conservative for healthcare compliance reasons.

    Args:
        answer:        The LLM-generated answer string.
        context_chunks: List of retrieved document chunk texts.

    Returns:
        GroundingResult with grounding assessment and any warnings.
    """
    if not context_chunks:
        return GroundingResult(
            is_grounded=False,
            confidence=0.0,
            warning_message="No context chunks retrieved — answer cannot be grounded."
        )

    # Check for appropriate decline responses
    answer_lower = answer.lower()
    for phrase in SAFE_DECLINE_PHRASES:
        if phrase in answer_lower:
            logger.debug("Answer contains safe decline phrase — marking as grounded.")
            return GroundingResult(
                is_grounded=True,
                confidence=1.0,
                warning_message=""
            )

    # Combine all context into one string for overlap comparison
    full_context = " ".join(context_chunks)

    # Split answer into sentences
    sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return GroundingResult(
            is_grounded=True,
            confidence=1.0,
            warning_message=""
        )

    grounded = []
    ungrounded = []

    for sentence in sentences:
        score = _sentence_overlap_score(sentence, full_context)
        if score >= SENTENCE_GROUNDING_THRESHOLD:
            grounded.append(sentence)
        else:
            ungrounded.append(sentence)
            logger.debug(
                "Potentially ungrounded sentence (overlap=%.2f): %.80s...",
                score, sentence
            )

    grounded_fraction = len(grounded) / len(sentences)
    is_grounded = grounded_fraction >= ANSWER_GROUNDING_THRESHOLD

    warning = ""
    if not is_grounded:
        warning = (
            f"Answer grounding check failed: only {grounded_fraction:.0%} of sentences "
            f"are supported by retrieved context. Review answer for potential hallucinations."
        )
        logger.warning(warning)

    return GroundingResult(
        is_grounded=is_grounded,
        confidence=round(grounded_fraction, 3),
        grounded_sentences=grounded,
        ungrounded_sentences=ungrounded,
        warning_message=warning
    )
