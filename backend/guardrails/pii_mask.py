"""
guardrails/pii_mask.py

Regex-based PII detection and masking for healthcare claims queries.
Masks Member IDs (MBR-XXXXXXX format) and Social Security Numbers before
sending queries to the LLM to ensure member privacy compliance.
"""

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Regex Patterns
# ──────────────────────────────────────────────────────────────────────────────

# Member ID: MBR- followed by 7 alphanumeric characters (e.g., MBR-1234567, MBR-AB12345)
MEMBER_ID_PATTERN = re.compile(
    r'\bMBR-[A-Z0-9]{7}\b',
    re.IGNORECASE
)

# SSN patterns:
#   - Formatted: 123-45-6789
#   - Unformatted (9 consecutive digits that look like SSN context): 123456789
SSN_FORMATTED_PATTERN = re.compile(
    r'\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b'
)

SSN_UNFORMATTED_PATTERN = re.compile(
    r'\b(?!000|666|9\d{2})\d{3}(?!00)\d{2}(?!0000)\d{4}\b'
)

# National Provider Identifier (NPI): 10-digit number
NPI_PATTERN = re.compile(
    r'\bNPI[:\s#-]*([0-9]{10})\b',
    re.IGNORECASE
)

# Date of Birth patterns
DOB_PATTERN = re.compile(
    r'\b(?:DOB|Date\s+of\s+Birth|Birth\s+Date)[:\s]*'
    r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
    re.IGNORECASE
)

# ──────────────────────────────────────────────────────────────────────────────
# Replacement Tokens
# ──────────────────────────────────────────────────────────────────────────────

MEMBER_ID_REPLACEMENT = "[MEMBER_ID_REDACTED]"
SSN_REPLACEMENT = "[SSN_REDACTED]"
NPI_REPLACEMENT = "NPI: [NPI_REDACTED]"
DOB_REPLACEMENT = "Date of Birth: [DOB_REDACTED]"


# ──────────────────────────────────────────────────────────────────────────────
# Result Dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class MaskResult:
    """Result of a PII masking operation."""
    masked_text: str
    pii_detected: bool
    detections: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.pii_detected = bool(self.detections)


# ──────────────────────────────────────────────────────────────────────────────
# Core Masking Functions
# ──────────────────────────────────────────────────────────────────────────────

def mask_member_ids(text: str) -> tuple[str, list[str]]:
    """
    Detect and replace Member IDs in the format MBR-XXXXXXX.

    Args:
        text: Input string potentially containing member IDs.

    Returns:
        Tuple of (masked_text, list_of_detected_values).
    """
    detections = []
    matches = MEMBER_ID_PATTERN.findall(text)
    if matches:
        detections.extend([f"MEMBER_ID: {m}" for m in matches])
        text = MEMBER_ID_PATTERN.sub(MEMBER_ID_REPLACEMENT, text)
    return text, detections


def mask_ssns(text: str) -> tuple[str, list[str]]:
    """
    Detect and replace Social Security Numbers (formatted and unformatted).

    Args:
        text: Input string potentially containing SSNs.

    Returns:
        Tuple of (masked_text, list_of_detected_values).
    """
    detections = []

    # Mask formatted SSN first (e.g., 123-45-6789)
    formatted_matches = SSN_FORMATTED_PATTERN.findall(text)
    if formatted_matches:
        detections.extend([f"SSN_FORMATTED: {m}" for m in formatted_matches])
        text = SSN_FORMATTED_PATTERN.sub(SSN_REPLACEMENT, text)

    # Mask unformatted SSN (e.g., 123456789) — be conservative to avoid false positives
    # Only mask if surrounded by non-digit chars to avoid matching within longer numbers
    unformatted_matches = SSN_UNFORMATTED_PATTERN.findall(text)
    if unformatted_matches:
        detections.extend([f"SSN_UNFORMATTED: {m}" for m in unformatted_matches])
        text = SSN_UNFORMATTED_PATTERN.sub(SSN_REPLACEMENT, text)

    return text, detections


def mask_npis(text: str) -> tuple[str, list[str]]:
    """
    Detect and replace National Provider Identifiers (NPIs).

    Args:
        text: Input string potentially containing NPI numbers.

    Returns:
        Tuple of (masked_text, list_of_detected_values).
    """
    detections = []
    matches = NPI_PATTERN.findall(text)
    if matches:
        detections.extend([f"NPI: {m}" for m in matches])
        text = NPI_PATTERN.sub(NPI_REPLACEMENT, text)
    return text, detections


def mask_dob(text: str) -> tuple[str, list[str]]:
    """
    Detect and replace Date of Birth references.

    Args:
        text: Input string potentially containing DOB.

    Returns:
        Tuple of (masked_text, list_of_detected_values).
    """
    detections = []
    matches = DOB_PATTERN.findall(text)
    if matches:
        detections.extend([f"DOB: {m}" for m in matches])
        text = DOB_PATTERN.sub(DOB_REPLACEMENT, text)
    return text, detections


# ──────────────────────────────────────────────────────────────────────────────
# Primary Public Interface
# ──────────────────────────────────────────────────────────────────────────────

def mask_pii(text: str) -> MaskResult:
    """
    Apply all PII masking rules to the input text in sequence.

    This is the primary function to call before sending any user query
    to the LLM. It masks:
    - Member IDs (MBR-XXXXXXX)
    - Social Security Numbers (formatted and unformatted)
    - National Provider Identifiers (NPI: XXXXXXXXXX)
    - Dates of Birth (DOB: MM/DD/YYYY)

    Args:
        text: Raw user query text.

    Returns:
        MaskResult with the sanitized text and detection metadata.
    """
    all_detections: list[str] = []

    text, member_id_detections = mask_member_ids(text)
    all_detections.extend(member_id_detections)

    text, ssn_detections = mask_ssns(text)
    all_detections.extend(ssn_detections)

    text, npi_detections = mask_npis(text)
    all_detections.extend(npi_detections)

    text, dob_detections = mask_dob(text)
    all_detections.extend(dob_detections)

    if all_detections:
        logger.warning(
            "PII detected and masked in query. Types: %s",
            ", ".join(set(d.split(":")[0] for d in all_detections))
        )

    return MaskResult(
        masked_text=text,
        pii_detected=bool(all_detections),
        detections=all_detections
    )


def detect_pii_only(text: str) -> list[str]:
    """
    Detect PII types present in the text without masking.

    Useful for logging/auditing purposes.

    Args:
        text: Input text to scan.

    Returns:
        List of PII type identifiers found (e.g., ['MEMBER_ID', 'SSN_FORMATTED']).
    """
    detected_types = []

    if MEMBER_ID_PATTERN.search(text):
        detected_types.append("MEMBER_ID")
    if SSN_FORMATTED_PATTERN.search(text):
        detected_types.append("SSN_FORMATTED")
    if SSN_UNFORMATTED_PATTERN.search(text):
        detected_types.append("SSN_UNFORMATTED")
    if NPI_PATTERN.search(text):
        detected_types.append("NPI")
    if DOB_PATTERN.search(text):
        detected_types.append("DOB")

    return detected_types
