import logging
from pathlib import Path
from textwrap import dedent

from markitdown import MarkItDown
import mdformat
from openai import OpenAI

logger = logging.getLogger(__name__)


def parse_file_to_md(file_path: Path) -> str:
    """Pass path as string to MarkItDown and return markdown content as string."""
    md = MarkItDown()
    result = md.convert(str(file_path))
    return result.text_content


def format_markdown_mdformat(markdown_content: str) -> str:
    """Format markdown content using mdformat."""
    result = mdformat.text(markdown_content)
    return result


def format_markdown_llm(
    markdown_content: str, client: OpenAI, language: str = "German"
) -> str:
    """Format markdown content using an LLM via openai library

    Args:
        markdown_content: Raw markdown content to be preprocessed

    Returns:
        Preprocessed markdown content with proper structure and formatting
    """
    logger.debug(f"Formatting markdown content (language: {language})")

    system_prompt = dedent(
        """You are a markdown formatting specialist. Follow these instructions
        exactly:

        REQUIRED STRUCTURE:
        1. TITLE (Required)
        - Extract or create a clear title
        - Format as level 1 header: # Title

        2. SECTIONS (Required)
        - Divide content into logical sections
        - Use level 2 headers: ## Section Name
        - Ensure sections are coherent and well-organized

        3. CONTENT FORMATTING (Required)
        - Keep ALL sentences complete with proper punctuation
        - Preserve ALL technical terms exactly as written
        - Maintain ALL code blocks and formatting
        - Keep the EXACT SAME LANGUAGE as the input

        4. PRESERVATION RULES:
        - Keep ALL original information
        - Maintain ALL technical accuracy
        - Preserve ALL examples and references
        - Keep ALL language-specific terms unchanged

        OUTPUT FORMAT:
        # Main Title

        ## Section 1
        Content with complete sentences.

        ## Section 2
        More content with preserved formatting.
        """
    )

    user_prompt = dedent(
        f"""Format this content according to the requirements while strictly
        preserving the original language ({language}) and technical accuracy:

        {markdown_content}
        """
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # or gpt-3.5-turbo if preferred
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,  # Lower temperature for more consistent formatting
        )
        result = response.choices[0].message.content
        if result:
            logger.debug("Markdown content formatted successfully.")
            return result
        else:
            logger.warning("No response from the model for markdown formatting.")
            return "No response from the model."
    except Exception as e:
        logger.error(f"Error formatting markdown content: {e}")
        raise


def get_markdown_from_file(
    file_path: Path,
    client: OpenAI,
) -> tuple[str, str]:
    """Generate markdown content in the specified format."""
    logger.debug(f"Processing file: {file_path}")

    try:
        unformatted = parse_file_to_md(file_path)
        logger.debug("Successfully parsed file to markdown")

        # Format markdown content with mdformat
        formatted = format_markdown_mdformat(unformatted)
        logger.debug("Markdown content formatted with mdformat")

        llm_formatted = format_markdown_llm(formatted, client)
        logger.debug("Markdown content formatted with LLM")

        content = format_markdown_mdformat(llm_formatted)
        logger.debug("Final markdown content formatted with mdformat")

        # Get title from first line of markdown content
        title = content.split("\n")[0].strip("# ")
        logger.info(f"Title extracted: {title}")

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

    return content, title
