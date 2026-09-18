"""AuditAI BI — Section and Question Parser.

Splits multi-document query text into canonical XBRL sections and parses
Question 1 and Question 2 inquiries deterministically.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple


# Regex pattern to match markdown headers demarcation
SECTION_HEADER_PATTERN = re.compile(r"##\s*([^\n]+)\n")

# Regex pattern for Question 1
Q1_PATTERN = re.compile(
    r"Question1:\s*What'?s the reported value of\s+([\w\-:]+)\s+in the Instance document for the period\s+([^?]+)\?",
    re.IGNORECASE,
)

# Regex pattern for Question 2
Q2_PATTERN = re.compile(
    r"Question2:\s*What'?s the actual value of\s+([\w\-:]+)\s+in the Instance document for the period\s+([^,]+),\s*calculated based on the calculation relationship\?",
    re.IGNORECASE,
)

# Date extraction patterns
DURATION_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})")
INSTANT_DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})")


def split_sections(query: str) -> Tuple[Dict[str, str], str]:
    """Splits a multi-document challenge query into component XBRL sections and question text.
    
    Args:
        query: Raw query text containing markdown headers and XML documents.
        
    Returns:
        A tuple of (sections_dict, questions_text).
    """
    normalized_query = query.replace("\r\n", "\n")
    splits = SECTION_HEADER_PATTERN.split(normalized_query)
    
    sections: Dict[str, str] = {}
    question_text = ""

    # splits[0] is text before the first '## ' (preamble, usually empty)
    for i in range(1, len(splits), 2):
        sec_title = splits[i].strip()
        sec_content = splits[i + 1]

        # Detect and detach questions from the final section
        if "Question1:" in sec_content:
            parts = sec_content.split("Question1:", 1)
            sec_content = parts[0]
            question_text = "Question1:" + parts[1]

        sections[sec_title] = sec_content.strip()

    # Fallback if Question1 was not in any split section
    if not question_text and "Question1:" in normalized_query:
        question_text = normalized_query[normalized_query.find("Question1:"):]

    return sections, question_text.strip()


def parse_questions(question_text: str) -> Dict[str, Any]:
    """Parses target concept, period specifications, and question text.
    
    Args:
        question_text: Trailing question block starting with Question1.
        
    Returns:
        Dictionary with target_concept, target_period_type, target_start_date,
        target_end_date, target_instant_date, raw_question1, raw_question2.
    """
    target_concept = ""
    period_str = ""
    raw_q1 = ""
    raw_q2 = ""

    # Match Question 1
    m1 = Q1_PATTERN.search(question_text)
    if m1:
        target_concept = m1.group(1).strip()
        period_str = m1.group(2).strip()
        raw_q1 = m1.group(0).strip()
    else:
        # Fallback extraction for irregular phrasing
        concept_m = re.search(r"Question1:.*?(?:value of\s+)([\w\-:]+)", question_text)
        if concept_m:
            target_concept = concept_m.group(1).strip()
        raw_q1 = question_text.split("\n")[0].strip() if question_text else ""

    # Match Question 2
    m2 = Q2_PATTERN.search(question_text)
    if m2:
        raw_q2 = m2.group(0).strip()
    else:
        q2_idx = question_text.find("Question2:")
        if q2_idx != -1:
            raw_q2 = question_text[q2_idx:].split("\n")[0].strip()

    # Determine period type and dates
    target_period_type = "unknown"
    start_date = None
    end_date = None
    instant_date = None

    dur_match = DURATION_DATE_PATTERN.search(period_str or question_text)
    if dur_match:
        target_period_type = "duration"
        start_date = dur_match.group(1)
        end_date = dur_match.group(2)
    else:
        inst_match = INSTANT_DATE_PATTERN.search(period_str or question_text)
        if inst_match:
            target_period_type = "instant"
            instant_date = inst_match.group(1)

    return {
        "target_concept": target_concept,
        "target_period_type": target_period_type,
        "target_start_date": start_date,
        "target_end_date": end_date,
        "target_instant_date": instant_date,
        "raw_question1": raw_q1,
        "raw_question2": raw_q2,
    }
