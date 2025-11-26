# Contributing to Homey MCP Server

Thank you for your interest in contributing to the Homey MCP Server! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/mcp-homey.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests: `make test`
6. Commit your changes: `git commit -m "Add your feature"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## 🛠️ Development Setup

```bash
# Install dependencies
make install

# Run tests
make test

# Run linting
make lint

# Format code
make format
```

## 📋 Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and concise

## 🧪 Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Include both unit tests and integration tests where appropriate
- Test in both normal mode and demo mode

## 📝 Commit Messages

- Use clear and descriptive commit messages
- Start with a verb in imperative mood (Add, Fix, Update, etc.)
- Keep the first line under 72 characters
- Add detailed description if needed

Example:
```
Add support for window blinds control

- Implement blind position control
- Add tilt angle adjustment
- Update documentation with new features
```

## 🔍 Pull Request Guidelines

- Provide a clear description of the changes
- Link to any related issues
- Include screenshots or examples if relevant
- Ensure CI checks pass
- Be responsive to feedback and review comments

## 🐛 Reporting Bugs

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Homey version)
- Relevant logs or error messages

## 💡 Feature Requests

We welcome feature requests! Please:

- Check if the feature has already been requested
- Provide clear use cases
- Explain why the feature would be useful
- Consider implementation complexity

## 📚 Documentation

- Update documentation for any changes
- Add examples for new features
- Keep CLAUDE.md in sync with tool changes
- Update README.md if necessary

## 🤝 Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Maintain a welcoming environment

## ❓ Questions?

Feel free to open an issue for questions or discussions about contributing.

Thank you for contributing to Homey MCP Server! 🎉
