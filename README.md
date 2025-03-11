# Basic usage
anki-creator input.pdf output.apkg --api-key YOUR_OPENAI_API_KEY

# Set API key as environment variable
export OPENAI_API_KEY=YOUR_OPENAI_API_KEY
anki-creator input.pdf

# Create a separate deck for each section
anki-creator input.pdf --per-section

# Only format the markdown
anki-creator input.pdf --format-only

# Enable debug logging
anki-creator input.pdf --debug

# Specify log file
anki-creator input.pdf --log-file conversion.log
