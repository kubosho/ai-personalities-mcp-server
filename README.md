# AI Personalities

Give personality to AI agents.

## Overview

This project helps you to give specific personality to AI agents. Can store personality data in [ChromaDB](https://github.com/chroma-core/chroma) and search it easily using vector search.

### Main Features

- **Store personality data**: Save personality information from Markdown files
- **Search with AI**: Find personality data using semantic search
- **MCP server**: Work as a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) server
- **Keep metadata**: Save creation dates, update dates, and tags

## How to Install

### What you need

- Python 3.13 or newer
- [mise](https://mise.jdx.dev/) for tool management
- [Task](https://taskfile.dev/) for task running
- [uv](https://docs.astral.sh/uv/) for Python package management

### Install the package

```bash
# Get the code
git clone https://github.com/kubosho/ai-personalities.git
cd ai-personalities

# Install mise (if not already installed)
curl https://mise.run | sh

# Install tools using mise
mise install

# Install dependencies with uv
uv sync
```

## How to Use

### 1. Load personality data

First, make sure you have personality data files in the `/personalities` directory. Then load them into ChromaDB:

```bash
# Load personality data
uv run ai-personalities-load --chunks-dir path/to/chunks

# Or use custom settings
uv run ai-personalities-load \
  --chunks-dir personalities/shinosawa_hiro \
  --db-path ./custom_db \
  --collection-name shinosawa_hiro \
  --character-name "Custom name"
```

### 2. Start MCP server

Start the server so AI tools can access your personality data:

```bash
# Start MCP server
uv run ai-personalities-mcp
```

The tools will be available:

- `get_character_dialogue_style`: Get dialogue examples and speech patterns
- `get_character_traits`: Get personality traits and characteristics
- `search_personality`: Search across all personality data

## Settings

### Environment Variables

| Variable          | What it does                     | Default       |
| ----------------- | -------------------------------- | ------------- |
| `CHUNKS_DIR`      | Where personality data files are | -             |
| `CHROMA_DB_PATH`  | Where to save ChromaDB data      | `./chroma_db` |
| `COLLECTION_NAME` | Name of collection               | `personality` |
| `CHARACTER_NAME`  | Name of character                | `unknown`     |

### Command Options

#### `uv run ai-personalities-load`

- `--chunks-dir`: Where personality data files are (required)
- `--db-path`: Where to save ChromaDB data
- `--collection-name`: Name of collection
- `--character-name`: Name of character

#### `uv run ai-personalities-mcp`

- Options for MCP server settings

## Development

### Document quality for personality files

The `/personalities` directory contains personality definition files. Markdownlint and Textlint are used to check quality of Markdown files.

```bash
# Check personality files with Markdownlint and Textlint
task lint:markdown

# Fix automatically fixable issues
task lint:markdown:fix
```

This helps maintain:

- Consistent writing style across personality definitions
- Proper Japanese language usage
- Standardized formatting for character descriptions

### Check task definitions

Run `task -l` to see available tasks. See `Taskfile.yaml` for details.

### Project structure

```text
ai-personalities/
├── src/              # Source codes
├── personalities/    # Personality data
├── docs/             # Documents
├── tests/            # Test files (will add later)
├── pyproject.toml    # Project settings
├── Taskfile.yaml     # Task definitions
├── .tool-versions    # Tool versions
├── README.md
└── LICENSE
```

## License

[MIT License](LICENSE).

## Contribute

1. Fork this repository
2. Make feature branch (`git switch -c feature/amazing-feature`)
3. Commit your changes (`git commit -m 'add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Make a Pull Request

## Useful links

- [Design Document](docs/personality_design_doc.md)
