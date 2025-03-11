import logging

from enum import Enum
from typing import List, Optional, Tuple
from textwrap import dedent
import re

from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CardType(str, Enum):
    BASIC = "basic"
    CLOZE = "cloze"


class BasicCard(BaseModel):
    question: str
    answer: str
    examples: Optional[List[str]]
    type: CardType = CardType.BASIC


class ClozeCard(BaseModel):
    text: str
    back_extra: Optional[str]
    examples: Optional[List[str]]
    type: CardType = CardType.CLOZE


class Cards(BaseModel):
    cards: List[BasicCard | ClozeCard]


def split_markdown_into_sections(content: str) -> List[Tuple[str, str]]:
    """Split markdown content into sections based on ## headers.

    Returns:
        List of tuples (section_title, section_content)
    """
    content_lines = content.split("\n")
    if content_lines and content_lines[0].startswith("# "):
        content = "\n".join(content_lines[1:])

    # Split by ## headers
    sections = re.split(r"\n(?=## )", content.strip())

    # Process each section to extract title and content
    processed_sections = []
    for section in sections:
        if section.strip():
            lines = section.split("\n")
            if lines[0].startswith("## "):
                title = lines[0].strip("## ").strip()
                content = "\n".join(lines[1:]).strip()
                if content:  # Only include sections with content
                    processed_sections.append((title, content))
    return processed_sections


def generate_cards_for_section(
    section_title: str,
    section_content: str,
    client: OpenAI,
    language: str = "German",
) -> Cards:
    """Generate cards for a single section."""
    logger.debug(f"Generating cards for section: {section_title}")

    system_prompt = dedent("""You are an expert at creating high-quality flashcards for Anki.
    Follow these instructions precisely:

    CONTEXT:
    You are processing a section of a larger document. Focus on creating cards
    that capture the key concepts of this specific section.

    CARD CREATION RULES:
    1. Create BOTH basic and cloze deletion cards
    2. Make cards clear and concise
    3. Add relevant examples whenever possible
    4. Use the EXACT SAME LANGUAGE as the input content
    5. Create multiple cards for important concepts

    BASIC CARDS MUST:
    - Have a clear, focused question
    - Provide a comprehensive but concise answer
    - Include examples if and only if they help understanding
    - When using numbered or bulleted lists, use HTML tags (<ol>, <ul>, <li>)

    CLOZE CARDS MUST:
    - Use {{c1::text}} format for deletions
    - Number multiple deletions sequentially: {{c1::}}, {{c2::}}, etc.
    - Only include examples when they are directly relevant
    - Only include back_extra when additional context is needed

    JSON FORMAT REQUIREMENTS:
    1. Basic cards:
    {
        "question": "Clear, specific question",
        "answer": "Precise, complete answer",
        "examples": ["Concrete example 1", "Concrete example 2"],
        "type": "basic"
    }

    2. Cloze cards:
    {
        "text": "Complete sentence with {{c1::cloze deletions}}",
        "back_extra": "Additional context if needed",
        "examples": ["Relevant example 1", "Relevant example 2"],
        "type": "cloze"
    }

    IMPORTANT:
    - Keep ALL content in the original language
    - Ensure ALL fields match the specified format exactly
    - Create at least one example for each card when possible""")

    user_prompt = dedent(f"""Create Anki flashcards for this section titled "{section_title}":

    {section_content}

    Remember: Maintain the original language (i.e. {language}) and create both
    basic and cloze cards.""")

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=Cards,
        )

        message = completion.choices[0].message
        if message.parsed:
            cards = message.parsed
            logger.debug(
                f"Generated {len(cards.cards)} cards for section '{section_title}'"
            )
            return cards
        else:
            logger.warning(
                f"No cards generated for section '{section_title}': {message.refusal}"
            )
            return Cards(cards=[])
    except Exception as e:
        logger.error(f"Error generating cards for section '{section_title}': {e}")
        return Cards(cards=[])


def generate_cards_from_markdown_content(content: str, client: OpenAI) -> Cards:
    """Use OpenAI to generate Anki cards from markdown content."""
    sections = split_markdown_into_sections(content)
    logger.debug(f"Split markdown into {len(sections)} sections")

    all_cards = []
    for section_title, section_content in sections:
        try:
            section_cards = generate_cards_for_section(
                section_title, section_content, client
            )
            all_cards.extend(section_cards.cards)
        except Exception as e:
            logger.error(f"Error generating cards for section '{section_title}': {e}")

    return Cards(cards=all_cards)
