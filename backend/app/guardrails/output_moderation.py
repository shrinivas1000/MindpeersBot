"""
Output moderation — post-generation safety check.

Scans the LLM's response for unsafe content that slipped through the
system prompt guardrails, such as:
- Diagnostic language ("you have depression", "this sounds like X disorder")
- Medication/dosage recommendations
- Harmful claims

If detected, the problematic language is softened or stripped.
"""

import re

from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Patterns that indicate diagnostic language
_DIAGNOSIS_PATTERNS = [
    re.compile(r"you (?:have|suffer from|are experiencing|might have|probably have|likely have)\s+(?:depression|anxiety disorder|bipolar|ptsd|ocd|adhd|bpd|schizophrenia|anorexia|bulimia|eating disorder|personality disorder|panic disorder|social anxiety disorder|generalized anxiety disorder|major depressive)", re.IGNORECASE),
    re.compile(r"(?:this|that|it) (?:sounds like|seems like|looks like|could be|might be|is probably|is likely)\s+(?:depression|anxiety disorder|bipolar|ptsd|ocd|adhd|bpd|schizophrenia|anorexia|bulimia|eating disorder|personality disorder|panic disorder)", re.IGNORECASE),
    re.compile(r"(?:i think|i believe) you (?:have|are|suffer)", re.IGNORECASE),
    re.compile(r"you (?:are|might be|could be)\s+(?:clinically depressed|bipolar|manic|psychotic|schizophrenic|autistic|on the spectrum)", re.IGNORECASE),
    re.compile(r"(?:diagnos(?:e|is|ed)|disorder|condition|syndrome|clinical)\b", re.IGNORECASE),
]

# Patterns that indicate medication/dosage language
_MEDICATION_PATTERNS = [
    re.compile(r"(?:take|try|start|prescribe|recommend)\s+(?:\d+\s*mg|\w+(?:ine|lam|pam|xone|done|tine|pine))\b", re.IGNORECASE),
    re.compile(r"\b(?:sertraline|fluoxetine|citalopram|escitalopram|paroxetine|venlafaxine|duloxetine|bupropion|mirtazapine|trazodone|amitriptyline|prozac|zoloft|lexapro|paxil|effexor|wellbutrin|xanax|valium|klonopin|ativan|ambien|seroquel|abilify|lithium|lamotrigine|olanzapine|risperidone|quetiapine)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*(?:mg|milligram|microgram|mcg)\b", re.IGNORECASE),
    re.compile(r"(?:dosage|dose|prescription|prescribed|medication)\b", re.IGNORECASE),
]

# Replacement phrases for softening
_DIAGNOSIS_SOFTENER = "what you're describing"
_MEDICATION_REDIRECT = "Speaking with a doctor about treatment options could be really helpful."


def moderate_output(response_text: str) -> tuple[str, bool]:
    """
    Scan and moderate the LLM's response for unsafe content.

    Args:
        response_text: The raw response text from the LLM.

    Returns:
        (moderated_text, was_modified) — the cleaned text and whether
        any modifications were made.
    """
    modified = False
    text = response_text

    # Check for diagnostic language
    for pattern in _DIAGNOSIS_PATTERNS:
        if pattern.search(text):
            logger.warning("Output moderation: diagnostic language detected")
            # Replace the specific diagnostic claim with softer language
            text = pattern.sub(_DIAGNOSIS_SOFTENER, text)
            modified = True

    # Check for medication/dosage language
    for pattern in _MEDICATION_PATTERNS:
        if pattern.search(text):
            logger.warning("Output moderation: medication/dosage language detected")
            # For medication references, replace the whole sentence
            # Find the sentence containing the match and replace it
            sentences = text.split(". ")
            cleaned_sentences = []
            med_removed = False
            for sentence in sentences:
                if pattern.search(sentence):
                    if not med_removed:
                        cleaned_sentences.append(_MEDICATION_REDIRECT)
                        med_removed = True
                    # Skip the sentence with medication content
                else:
                    cleaned_sentences.append(sentence)
            text = ". ".join(cleaned_sentences)
            modified = True

    if modified:
        logger.info("Output moderation: response was modified for safety")

    return text, modified
