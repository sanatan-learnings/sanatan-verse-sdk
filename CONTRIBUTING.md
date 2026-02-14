# Contributing to Sanatan SDK

Thank you for your interest in contributing to Sanatan SDK! This project helps generate rich multimedia content for spiritual text collections, and we welcome contributions from the community.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- OpenAI API key (for testing image generation and embeddings)
- ElevenLabs API key (for testing audio generation)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/sanatan-sdk.git
   cd sanatan-sdk
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables**
   ```bash
   # In your test project directory (not in verse-sdk)
   cp /path/to/verse-sdk/.env.example .env
   # Edit .env and add your actual API keys
   ```

5. **Test your setup**
   ```bash
   verse-generate --help
   ```

## Project Structure

```
sanatan-sdk/
├── verse_sdk/
│   ├── audio/           # Audio generation with ElevenLabs
│   ├── cli/             # Command-line interface
│   ├── deployment/      # Cloudflare Worker deployment
│   ├── embeddings/      # Vector embeddings generation
│   ├── fetch/           # Text fetching from authoritative sources
│   ├── images/          # Image generation with DALL-E 3
│   └── utils/           # Shared utilities
├── docs/                # Documentation
├── examples/            # Example configurations
└── scripts/             # Development scripts
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

- Write clear, readable code
- Follow existing code style and conventions
- Add docstrings to functions and classes
- Keep changes focused and atomic

### 3. Test Your Changes

```bash
# Test specific commands
verse-generate --collection hanuman-chalisa --verse 1 --help

# Run test scripts
python scripts/test_multi_collection.py
```

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: brief description

More detailed explanation of what changed and why,
if needed for context."
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use meaningful variable and function names
- Maximum line length: 100 characters (flexible for readability)
- Use type hints where helpful

### Documentation

- Add docstrings to all public functions and classes
- Update relevant documentation in `docs/` directory
- Include usage examples for new commands or features

### Error Handling

- Provide clear, actionable error messages
- Handle edge cases gracefully
- Exit with appropriate status codes

## Submitting a Pull Request

1. **Push your changes**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**
   - Go to the [Sanatan SDK repository](https://github.com/sanatan-learnings/sanatan-sdk)
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template with:
     - Clear description of changes
     - Related issue numbers (if applicable)
     - Testing performed
     - Screenshots (if UI changes)

3. **Respond to feedback**
   - Be open to suggestions and code reviews
   - Make requested changes promptly
   - Keep the conversation respectful and constructive

## Types of Contributions

We welcome various types of contributions:

### Bug Fixes
- Report bugs via [GitHub Issues](https://github.com/sanatan-learnings/sanatan-sdk/issues)
- Include steps to reproduce
- Provide system information (OS, Python version)

### New Features
- Discuss major changes in an issue first
- Ensure features align with project goals
- Include documentation and examples

### Documentation
- Fix typos or clarify existing docs
- Add examples and use cases
- Improve command documentation

### Testing
- Add test scripts for new functionality
- Improve existing test coverage
- Report edge cases

### New Collection Support
- Add support for new verse collections
- Include text fetching sources
- Provide example configurations

## Community Guidelines

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Credit others for their contributions
- Respect the spiritual nature of the content

## Questions?

- Open an issue for general questions
- Check [Documentation](docs/README.md)
- Review [Troubleshooting Guide](docs/troubleshooting.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Sanatan SDK! 🙏
