import random
from textwrap import dedent

import genanki

from .cards import Cards, ClozeCard, BasicCard

# Create models for different card types
BASIC_MODEL = genanki.Model(
    2077470994,
    "Basic with Examples (genanki)",
    fields=[
        {"name": "Question", "font": "Arial"},
        {"name": "Answer", "font": "Arial"},
        {"name": "Examples", "font": "Arial"},
    ],
    templates=[
        {
            "name": "Card 1",
            "qfmt": "{{Question}}",
            "afmt": """
                {{FrontSide}}
                <hr id="answer">
                {{Answer}}
                {{#Examples}}
                <br><br>
                <strong>Examples:</strong><br>
                {{Examples}}
                {{/Examples}}
            """,
        },
    ],
    css=dedent("""
    .card {
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }
    """),
)

CLOZE_MODEL = genanki.Model(
    1337252809,
    "Cloze with Examples (genanki)",
    fields=[
        {"name": "Text", "font": "Arial"},  # Main text with cloze deletions
        {"name": "Back Extra", "font": "Arial"},  # Optional back side info
        {"name": "Examples", "font": "Arial"},  # For additional examples
    ],
    templates=[
        {
            "name": "Cloze Card",
            "qfmt": "{{cloze:Text}}",
            "afmt": """
                {{cloze:Text}}
                {{#Back Extra}}
                <hr id="extra">
                {{Back Extra}}
                {{/Back Extra}}
                {{#Examples}}
                <br><br>
                <strong>Examples:</strong><br>
                {{Examples}}
                {{/Examples}}
            """,
        }
    ],
    css=dedent("""
    .card {
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }
    .cloze {
        font-weight: bold;
        color: blue;
    }
    .nightMode .cloze {
        color: lightblue;
    }
    """),
    model_type=genanki.Model.CLOZE,
)


def create_deck(title: str, cards: Cards) -> genanki.Deck:
    """Create an Anki deck from the cards."""
    deck_id = random.randrange(1 << 30, 1 << 31)
    deck = genanki.Deck(deck_id, title)

    for card in cards.cards:
        examples_html = (
            "<ul>"
            + "".join(f"<li>{example}</li>" for example in card.examples)
            + "</ul>"
            if card.examples
            else ""
        )
        if type(card) is ClozeCard:
            note = genanki.Note(
                model=CLOZE_MODEL,
                fields=[card.text, card.back_extra or "", examples_html],
            )
        elif type(card) is BasicCard:
            note = genanki.Note(
                model=BASIC_MODEL,
                fields=[card.question, card.answer, examples_html],
            )
        else:
            raise ValueError(f"Unknown card type: {type(card)}")
        deck.add_note(note)

    return deck
