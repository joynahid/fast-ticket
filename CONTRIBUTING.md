# Contributing to Bangladesh Railway Ticket Booking System

Thank you for your interest in contributing to our project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- Use a clear and descriptive title
- Describe the exact steps to reproduce the problem
- Provide specific examples to demonstrate the steps
- Describe the behavior you observed after following the steps
- Explain which behavior you expected to see instead and why
- Include screenshots if applicable
- Include the Python version and OS you're using

### Suggesting Enhancements

If you have a suggestion for a new feature or enhancement, please:

- Use a clear and descriptive title
- Provide a detailed description of the proposed functionality
- Explain why this enhancement would be useful
- List any similar features in other applications

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Process

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/your-username/book-train-ticket.git
cd book-train-ticket
```

3. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

4. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Code Style

We follow PEP 8 style guide for Python code. Please ensure your code follows these guidelines:

- Use 4 spaces for indentation
- Maximum line length of 88 characters
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes

We use `black` for code formatting and `flake8` for linting. Before submitting a PR, run:

```bash
black .
flake8
```

### Testing

We use `pytest` for testing. Please write tests for new features and ensure all tests pass:

```bash
pytest
```

### Documentation

- Update the README.md if you're changing functionality
- Add docstrings to new functions and classes
- Update the API documentation if you're changing interfaces

### Git Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them:
```bash
git add .
git commit -m "feat: add your feature"
```

3. Push to your fork:
```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request

### Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

Example:
```
feat: add SMS notification service
fix: resolve authentication token refresh issue
docs: update API documentation
```

## Architecture Guidelines

When contributing, please follow these architectural principles:

1. **Clean Architecture**: Keep business logic separate from infrastructure
2. **Dependency Injection**: Use constructor injection for dependencies
3. **Interface Segregation**: Create specific interfaces for each service
4. **Single Responsibility**: Each class should have one reason to change
5. **Open/Closed**: Extend functionality through new classes, not by modifying existing ones

## Review Process

1. All PRs require at least one review
2. CI checks must pass
3. Code must be properly formatted and linted
4. Tests must pass
5. Documentation must be updated

## Getting Help

If you need help with your contribution:

1. Check the [documentation](README.md)
2. Join our [Discord community](https://discord.gg/your-discord)
3. Open an issue for discussion

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License. 