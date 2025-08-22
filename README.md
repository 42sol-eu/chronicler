# Chronicler

A powerful CLI application for managing multiple types of text and office files. Chronicler helps you organize, track, and manage your documents efficiently from the command line.

## Features

- **Document Management**: Organize and manage text and office files
- **Chronicle Creation**: Create new chronicles to categorize your documents
- **Flexible Listing**: View your chronicles in different formats (table, JSON)
- **Rich CLI Interface**: Built with Click for an intuitive command-line experience
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Installation

### Requirements

- Python 3.11 or higher
- Poetry (recommended) or pip

### Install with Poetry

```bash
# Clone the repository
git clone <repository-url>
cd chronicler

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Install with pip

```bash
# Clone the repository
git clone <repository-url>
cd chronicler

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### Basic Commands

#### Show Help
```bash
python -m src.chronicler --help
```

#### Check Version
```bash
python -m src.chronicler --version
```

### Managing Chronicles

#### Create a New Chronicle
```bash
# Basic creation
python -m src.chronicler create "My Documents"

# With description
python -m src.chronicler create "Project Files" --description "Files for the new project"
```

#### List All Chronicles
```bash
# Default table format
python -m src.chronicler list

# JSON format
python -m src.chronicler list --format json
```

#### Show Chronicle Details
```bash
python -m src.chronicler show "My Documents"
```

### Global Options

- `--verbose, -v`: Enable verbose output for detailed information
- `--version`: Show the application version
- `--help`: Show help information

### Examples

```bash
# Create a chronicle for work documents with verbose output
python -m src.chronicler -v create "Work Documents" --description "All work-related files"

# List chronicles in JSON format with verbose output
python -m src.chronicler --verbose list --format json

# Show details of a specific chronicle
python -m src.chronicler show "Work Documents"
```

## Development

### Project Structure

```
chronicler/
├── src/
│   └── chronicler/
│       ├── __init__.py          # Package initialization
│       └── __main__.py          # CLI entry point
├── tests/
│   ├── __init__.py
│   └── test_cli.py              # Test cases
├── pyproject.toml               # Project configuration
├── poetry.lock                  # Dependency lock file
└── README.md                    # This file
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test class
poetry run pytest tests/test_cli.py::TestVersion -v

# Run tests with coverage
poetry run pytest --cov=src
```

### Development Dependencies

The project includes test dependencies that can be installed with:

```bash
# Install with test dependencies
poetry install --with test

# Or with pip
pip install -e ".[test]"
```

### Code Quality

The project uses:
- **pytest**: For testing
- **click**: For CLI framework
- **rich**: For enhanced terminal output

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`poetry run pytest`)
6. Commit your changes (`git commit -am 'Add new feature'`)
7. Push to the branch (`git push origin feature/new-feature`)
8. Create a Pull Request

## Configuration

Chronicler can be configured through various means:

### Environment Variables

- `CHRONICLER_VERBOSE`: Set to `true` to enable verbose output by default
- `CHRONICLER_FORMAT`: Default format for list commands (`table` or `json`)

### Configuration File

(Feature planned for future releases)

## Supported File Types

Chronicler is designed to work with various text and office file formats:

- **Text Files**: `.txt`, `.md`, `.rst`
- **Office Documents**: `.docx`, `.xlsx`, `.pptx`
- **PDF Files**: `.pdf`
- **Source Code**: `.py`, `.js`, `.html`, `.css`, etc.
- **Configuration Files**: `.json`, `.yaml`, `.toml`, `.ini`

## Roadmap

- [ ] File indexing and search functionality
- [ ] Document metadata extraction
- [ ] Integration with cloud storage services
- [ ] Web interface for document management
- [ ] Document versioning and history
- [ ] Advanced filtering and sorting options
- [ ] Export/import functionality
- [ ] Plugin system for custom file handlers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the [documentation](#usage)
2. Search existing [issues](issues)
3. Create a [new issue](issues/new) if needed

## Changelog

### Version 2025.0.1
- Initial release with basic chronicle management
- CLI interface with create, list, and show commands
- Support for verbose output and multiple formats
- Comprehensive test suite

---

**Chronicler** - Manage your documents with ease from the command line.
