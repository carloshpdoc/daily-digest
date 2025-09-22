# Contributing to Daily Digest Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to the Daily Digest Generator.

## 🚀 Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/daily-digest.git
   cd daily-digest
   ```
3. **Set up the development environment**:
   ```bash
   ./setup.sh
   source venv/bin/activate
   ```
4. **Install development dependencies**:
   ```bash
   pip install black ruff mypy bandit
   ```

## 🔧 Development Workflow

### Before Making Changes

1. Create a new branch for your feature/fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make sure all tests pass:
   ```bash
   python -c "import daily_digest; print('✅ Main module imports')"
   ```

### Code Style and Quality

We use several tools to maintain code quality:

- **Black** for code formatting
- **Ruff** for linting
- **mypy** for type checking (optional but recommended)

Run these before committing:
```bash
# Format code
black .

# Check linting
ruff check .

# Type checking (optional)
mypy daily_digest.py --ignore-missing-imports
```

### Testing

1. **Test your changes** with different configurations:
   ```bash
   # Test module imports
   python -c "from daily_digest import github_prs, jira_enhanced_status"

   # Test individual components (if you have credentials configured)
   python tests/test_calendar.py
   python tests/test_jira_enhanced.py
   ```

2. **Add tests** for new functionality in the `tests/` directory

3. **Validate test syntax**:
   ```bash
   for test in tests/test_*.py; do python -m py_compile "$test"; done
   ```

## 📝 Commit Guidelines

### Commit Message Format
```
type(scope): description

- Detailed explanation if needed
- Reference issues with #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(github): add support for draft PRs
fix(jira): handle empty status responses
docs(readme): update installation instructions
test(calendar): add timezone validation tests
```

## 🔒 Security Guidelines

### Sensitive Data
- **Never commit** actual API tokens or credentials
- **Use environment variables** for all sensitive configuration
- **Update .env.example** with placeholder values for new config
- **Test with invalid credentials** to ensure graceful error handling

### Code Security
- **Validate all user inputs**
- **Use parameterized queries** for any database operations
- **Handle API rate limits** appropriately
- **Follow principle of least privilege** for API permissions

## 🎯 Types of Contributions

### 🐛 Bug Fixes
- Check existing issues first
- Include reproduction steps in your PR description
- Add tests to prevent regression

### ✨ New Features
- **Discuss first** by opening an issue
- **Keep scope focused** - one feature per PR
- **Update documentation** as needed
- **Add tests** for new functionality

### 📚 Documentation
- Fix typos and improve clarity
- Add usage examples
- Update setup instructions
- Improve troubleshooting guides

### 🔌 New Integrations
When adding support for new services:

1. **Create a new function** following existing patterns
2. **Add environment variables** to `.env.example`
3. **Include comprehensive error handling**
4. **Add tests** in `tests/test_new_service.py`
5. **Update README** with configuration instructions
6. **Consider rate limiting** and API best practices

## 📋 Pull Request Process

1. **Update documentation** if your changes affect usage
2. **Add tests** for new functionality
3. **Ensure CI passes** (GitHub Actions will run automatically)
4. **Request review** from maintainers
5. **Address feedback** promptly

### PR Checklist
- [ ] Code follows style guidelines (Black, Ruff)
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] CI/CD passes
- [ ] Self-review completed

## 🤝 Code Review Guidelines

### For Contributors
- **Be responsive** to feedback
- **Ask questions** if feedback is unclear
- **Test suggested changes** before implementing

### For Reviewers
- **Be constructive** and specific
- **Suggest improvements** rather than just pointing out problems
- **Test the changes** locally when possible
- **Approve when ready** - don't let perfect be the enemy of good

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check README.md and tests/ for examples

## 🎉 Recognition

Contributors will be:
- **Listed in the README** (if desired)
- **Credited in release notes** for significant contributions
- **Added to GitHub contributors** automatically

Thank you for contributing to Daily Digest Generator! 🚀