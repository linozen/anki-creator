from enum import Enum
from typing import List, Optional
from textwrap import dedent

from openai import OpenAI
from pydantic import BaseModel


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


def generate_cards_from_markdown_content(content: str, client: OpenAI) -> Cards:
    """Use OpenAI to generate Anki cards from markdown content."""

    system_prompt = dedent(
        """You are an expert at creating high-quality flashcards for Anki.
        Follow these instructions precisely:

        CARD CREATION RULES:
        1. Create BOTH basic and cloze deletion cards
        2. Make cards clear and concise
        3. Add relevant examples whenever possible
        4. Use the EXACT SAME LANGUAGE as the input content
        5. Create multiple cards for important concepts

        BASIC CARDS MUST:
        - Have a clear, focused question
        - Provide a comprehensive but concise answer
        - Include examples when they help understanding

        CLOZE CARDS MUST:
        - Use {{c1::text}} format for deletions
        - Number multiple deletions sequentially: {{c1::}}, {{c2::}}, etc.
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
        - Create at least one example for each card when possible
        """
    )

    user_prompt = dedent(
        f"""Create a comprehensive set of Anki flashcards from this content,
        following the format requirements exactly:

        {content}

        Remember: Maintain the original language and create both basic and cloze
        cards."""
    )

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-11-20",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=Cards,
    )

    message = completion.choices[0].message

    if message.parsed:
        return message.parsed
    else:
        print(message.refusal)
        return Cards(cards=[])
