from pathlib import Path

import click
import genanki
from openai import OpenAI

from .markdown import get_markdown_from_file
from .cards import generate_cards_from_markdown_content
from .anki import create_deck


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option("--api-key", envvar="OPENAI_API_KEY", required=True)
def main(input_file: Path, output_file: Path, api_key: str):
    """Convert a markdown file into an Anki deck."""
    # Ensure output file has .apkg extension
    if not output_file.suffix == ".apkg":
        output_file = output_file.with_suffix(".apkg")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)

    # Extract markdown content from file
    click.echo(f"Extracting markdown content from {input_file}...")
    content, title = get_markdown_from_file(input_file, client)
    # Write formatted markdown to file for reference
    print(content)
    formatted_path = input_file.with_suffix(".formatted.md")
    print(formatted_path)
    formatted_path.write_text(content, encoding="utf-8")

    # Generate cards
    click.echo(f"Generating cards for '{title}'...")
    cards = generate_cards_from_markdown_content(content, client)
    click.echo(f"Generated {len(cards.cards)} cards")

    # Create and save the deck
    click.echo("Creating deck...")
    deck = create_deck(title, cards)
    genanki.Package(deck).write_to_file(str(output_file))
    click.echo(f"Deck saved to {output_file}")


if __name__ == "__main__":
    main()
