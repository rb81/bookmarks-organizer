# Bookmarks Organizer

![Bookmarks Organizer](/header.png)

AI-powered bookmark organizer that reads your exported bookmarks (Netscape format), categorizes them into folders using any OpenAI-compatible LLM, and exports them back — ready to import into any browser.

## Features

- **Parse & export** standard Netscape Bookmark File Format (works with Chrome, Firefox, Safari, Edge, etc.)
- **AI categorization** using OpenAI, OpenRouter, or any OpenAI-compatible API
- **Protected folders** — keep specific folders untouched
- **Uncategorized mode** — only sort new/uncategorized bookmarks while preserving your existing structure
- **Batch processing** — handles large collections efficiently
- **Stop & resume** — automatically saves progress; resume after interruptions
- **Retry with backoff** — gracefully handles rate limits, timeouts, and transient API errors

## Requirements

- Python 3.10+
- An OpenAI-compatible API that supports **structured JSON output** (`response_format: { type: "json_object" }`). This is required for reliable categorization. Most major providers support this:
  - ✅ OpenAI (all GPT-4o and GPT-4o-mini models)
  - ✅ OpenRouter (most models)
  - ✅ LM Studio / Ollama (with supported models)
  - ❌ Some older or smaller models may not support JSON mode — if you get errors about `response_format`, your model/provider doesn't support it.

## Quick Start

```bash
# Clone and install
git clone https://github.com/rb81/bookmarks-organizer.git
cd bookmarks-organizer
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key

# Run
python main.py bookmarks.html
```

## Configuration

### Environment Variables (`.env`)

```bash
# Required
API_KEY=sk-your-key-here

# Optional (defaults shown)
BASE_URL=https://api.openai.com/v1
MODEL=gpt-4o-mini
```

**Using OpenRouter:**
```bash
API_KEY=sk-or-v1-your-key
BASE_URL=https://openrouter.ai/api/v1
MODEL=anthropic/claude-sonnet-4
```

**Using a local LLM (e.g., LM Studio, Ollama):**
```bash
API_KEY=not-needed
BASE_URL=http://localhost:1234/v1
MODEL=local-model
```

> **Note:** Your model must support `response_format: { type: "json_object" }`. In Ollama, this works with most recent models. In LM Studio, ensure you're using a model that supports structured output.

### Config File (`config.yaml`)

```yaml
max_categories: 20
batch_size: 10
protected_folders:
  - Favorites
  - Reading List
```

## Usage

```bash
# Organize all bookmarks
python main.py bookmarks.html

# Specify output file
python main.py bookmarks.html -o organized.html

# Only organize uncategorized bookmarks (preserves existing folders)
python main.py bookmarks.html --uncategorized-only

# Override model/provider from CLI
python main.py bookmarks.html --model gpt-4o --base-url https://openrouter.ai/api/v1

# Start fresh (ignore saved progress)
python main.py bookmarks.html --no-resume

# See all options
python main.py --help
```

### Stop & Resume

If you interrupt the process (Ctrl+C) or it crashes mid-run, progress is automatically saved to `progress.json`. Simply run the same command again and it will resume where it left off. Use `--no-resume` to discard saved progress and start fresh.

### Error Handling

The organizer handles transient API failures gracefully:

- **Rate limits** — waits and retries (up to 3 attempts with increasing delays)
- **Timeouts** — retries with backoff
- **Connection errors** — retries with backoff
- **Server errors (5xx)** — retries with backoff
- **Client errors (4xx)** — fails immediately (e.g., invalid API key, unsupported model)
- **Invalid responses** — marks affected bookmarks as "Uncategorized" rather than crashing

If all retries are exhausted for a batch, those bookmarks are placed in an "Uncategorized" folder and processing continues.

### Workflow

1. **Export** bookmarks from your browser as HTML
2. **Run** the organizer
3. **Import** the output file back into your browser
4. Keep a folder called "Uncategorized" for new bookmarks — periodically run with `--uncategorized-only` to sort them

## Netscape Bookmark File Format

This is the standard format used by all major browsers for bookmark import/export:

```html
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!--This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<Title>Bookmarks</Title>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 FOLDED ADD_DATE="1234567890">Folder Name</H3>
    <DL><p>
        <DT><A HREF="https://example.com" ADD_DATE="1234567890">Example</A>
    </DL><p>
</DL><p>
```

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_parser.py
```

## Project Structure

```
bookmarks-organizer/
├── main.py              # CLI entry point
├── src/
│   ├── models.py        # Bookmark & Folder dataclasses
│   ├── parser.py        # Netscape HTML parser
│   ├── writer.py        # Netscape HTML writer
│   ├── organizer.py     # LLM-powered categorization (with retries)
│   └── progress.py      # Stop/resume persistence
├── tests/
│   ├── test_parser.py   # Parser & extraction tests
│   ├── test_writer.py   # Writer & round-trip tests
│   ├── test_organizer.py # Organizer & categorization tests
│   └── test_progress.py # Progress persistence tests
├── config.yaml          # User settings
├── .env.example         # Environment template
├── requirements.txt
└── README.md
```

## License

MIT License — see [LICENSE](LICENSE) for details.
