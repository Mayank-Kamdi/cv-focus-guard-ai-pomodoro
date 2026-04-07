# Contributing to Focus Guard

We're thrilled that you're interested in contributing to Focus Guard! This document provides guidelines for contributing to this project.

## 🤝 How to Contribute

### Getting Permission to Merge

This project requires approval before merging contributions. Here's how it works:

1. **Fork the Repository**: Create your own fork of the project
2. **Make Your Changes**: Develop your feature or fix in your fork
3. **Submit a Pull Request**: Open a PR with a clear description of your changes
4. **Wait for Review**: A maintainer will review your PR and may request changes
5. **Get Approval**: Once approved, a maintainer will merge your contribution

### Types of Contributions We Welcome

- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🎨 UI/UX enhancements
- ⚡ Performance optimizations
- 🧪 Tests and test coverage
- 🌐 Translations and internationalization

## 🔧 Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/cv-focus-guard-ai-pomodoro.git
   cd cv-focus-guard-ai-pomodoro
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## 📋 Pull Request Process

### Before Submitting

- [ ] Test your changes thoroughly
- [ ] Ensure all existing functionality still works
- [ ] Update documentation if needed
- [ ] Follow the existing code style
- [ ] Add comments for complex logic
- [ ] Remove any debugging code or print statements

### PR Title Format

Use clear, descriptive titles with prefixes:
- `feat:` for new features (e.g., "feat: add keyboard shortcuts")
- `fix:` for bug fixes (e.g., "fix: webcam not releasing on exit")
- `docs:` for documentation (e.g., "docs: update installation guide")
- `style:` for formatting (e.g., "style: fix indentation in main.py")
- `refactor:` for code restructuring (e.g., "refactor: simplify focus detection logic")
- `test:` for tests (e.g., "test: add unit tests for timer")
- `chore:` for maintenance (e.g., "chore: update dependencies")

### PR Description Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
Describe how you tested this change

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Fixes #(issue number)
```

## 💻 Code Style Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/) conventions
- Use meaningful variable and function names
- Maximum line length: 100 characters
- Use type hints where appropriate
- Add docstrings for functions and classes

### Example:

```python
def calculate_break_duration(work_minutes: int) -> int:
    """
    Calculate break duration based on work session length.
    
    Args:
        work_minutes: Duration of work session in minutes
        
    Returns:
        Calculated break duration in minutes (rounded)
    """
    return int(work_minutes ** 0.5)
```

### Code Organization

- Keep functions focused and single-purpose
- Group related functionality together
- Use constants for magic numbers
- Handle errors gracefully with try-except blocks

## 🐛 Reporting Bugs

When reporting bugs, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Numbered steps to recreate the bug
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**:
   - OS (Windows/macOS/Linux)
   - Python version
   - Webcam model (if relevant)
6. **Screenshots/Logs**: If applicable

## 💡 Suggesting Features

We love new ideas! When suggesting features:

1. **Check Existing Issues**: Make sure it hasn't been suggested
2. **Use Case**: Explain why this feature would be useful
3. **Proposed Solution**: Describe how you envision it working
4. **Alternatives**: Any alternative approaches you've considered

## 🧪 Testing Guidelines

Before submitting:

1. Test with different work durations (5, 25, 60, 120 minutes)
2. Verify focus detection works correctly
3. Test pause/resume functionality
4. Ensure the timer completes full cycles
5. Check that logs are generated properly
6. Test on your specific OS if possible

## 📜 Commit Message Guidelines

Write clear, concise commit messages:

```bash
# Good
git commit -m "fix: resolve camera not releasing on timer reset"
git commit -m "feat: add configurable alert sensitivity"

# Avoid
git commit -m "fixed bug"
git commit -m "updates"
```

## 🎯 Areas We Need Help With

Priority areas for contributions:

- 🌐 Multi-language support
- 🧪 Unit and integration tests
- 📱 Cross-platform compatibility improvements
- ⚙️ Configuration UI for advanced settings
- 📊 Statistics and analytics dashboard
- 🔊 Custom sound support
- ⌨️ Keyboard shortcuts
- 🎨 Theme customization

## 📞 Getting Help

- 💬 Open a [Discussion](https://github.com/irgidev/cv-focus-guard-ai-pomodoro/discussions) for questions
- 📧 Email the maintainer for sensitive issues
- 🐛 Use [Issues](https://github.com/irgidev/cv-focus-guard-ai-pomodoro/issues) for bugs and features

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Every contribution, no matter how small, is valuable. Thank you for helping make Focus Guard better!

---

**Questions?** Feel free to reach out by opening an issue or discussion. We're here to help! 🚀
