import logging
from pathlib import Path

import click
import genanki
from openai import OpenAI

from .markdown import get_markdown_from_file
from .cards import generate_cards_for_section, generate_cards_from_markdown_content, Cards, split_markdown_into_sections
from .anki import create_deck
from .logging import setup_logging

logger = logging.getLogger(__name__)


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path), required=False)
@click.option("--api-key", envvar="OPENAI_API_KEY", required=True)
@click.option("--log-file", type=click.Path(path_type=Path), help="Path to log file")
@click.option(
    "--debug",
    is_flag=True,
    default=False,
    help="Enable debug logging",
)
@click.option(
    "--force-format",
    is_flag=True,
    default=False,
    help="Force reformatting of markdown",
)
@click.option(
    "--format-only",
    is_flag=True,
    default=False,
    help="Only format the markdown file without creating an Anki deck",
)
@click.option(
    "--anki-conversion-only",
    is_flag=True,
    default=False,
    help="Only create an Anki deck without formatting the markdown file",
)
@click.option(
    "--per-section",
    is_flag=True,
    default=False,
    help="Create a separate Anki deck for each section in the document",
)
def main(
    input_file: Path,
    output_file: Path | None,
    api_key: str,
    log_file: Path,
    debug: bool,
    force_format: bool,
    format_only: bool,
    anki_conversion_only: bool,
    per_section: bool,
):
    """Convert a markdown file into an Anki deck."""
    # Setup logging
    setup_logging(log_file, debug)
    logger.info("Starting Anki deck creation...")

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        logger.debug("OpenAI client initialized")

        # Check for existing formatted markdown
        formatted_path = input_file.with_suffix(".formatted.md")
        if formatted_path.exists() and not force_format:
            logger.info(f"Using existing formatted markdown from {formatted_path}")
            content = formatted_path.read_text(encoding="utf-8")
            title = content.split("\n")[0].strip("# ")
        if anki_conversion_only:
            logger.info(
                "Anki card/deck creation only, skipping markdown conversion/formatting"
            )
            # Ensure input file is a markdown file
            if not input_file.suffix == ".md":
                raise click.ClickException("Input file must be a markdown file")
            content = input_file.read_text(encoding="utf-8")
            title = content.split("\n")[0].strip("# ")
        else:
            # Extract and format markdown content from file
            logger.info(f"Extracting and formatting markdown content from {input_file}")
            content, title = get_markdown_from_file(input_file, client)
            # Write formatted markdown to file for reference
            formatted_path.write_text(content, encoding="utf-8")
            logger.debug(f"Formatted markdown saved to {formatted_path}")

        if format_only:
            logger.info("Formatting only, skipping Anki deck creation")
            return

        # Split markdown content into sections
        sections = split_markdown_into_sections(content)

        if per_section:
            for section_title, section_content in sections:
                logger.info(f"Creating deck for section '{section_title}'")
                section_cards = generate_cards_for_section(section_title, section_content, client)
                section_deck = create_deck(section_title, section_cards)

                if output_file is None:
                    section_output_file = input_file.with_name(f"{section_title}.apkg")
                else:
                    section_output_file = output_file.with_name(f"{section_title}.apkg")

                genanki.Package(section_deck).write_to_file(str(section_output_file))
                click.echo(f"Deck for section '{section_title}' saved to {section_output_file}")

        else:
            # Create a single deck for the entire document
            cards = generate_cards_from_markdown_content(content, client)
            deck = create_deck(title, cards)
            if output_file is None:
                output_file = input_file.with_suffix(".apkg")
            genanki.Package(deck).write_to_file(str(output_file))
            click.echo(f"Deck saved to {output_file}")

    except Exception as e:
        logger.exception("An error occurred during conversion")
        raise click.ClickException(str(e))

if __name__ == "__main__":
    main()
