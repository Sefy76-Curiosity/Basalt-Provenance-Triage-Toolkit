# Contributing to Scientific Toolkit

Thank you for your interest in contributing! This project thrives on community involvement. Whether you're fixing bugs, adding features, improving documentation, or testing with your data, your contributions are valued.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How Can I Contribute?](#how-can-i-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Pull Request Process](#pull-request-process)
6. [Plugin Development](#plugin-development)
7. [Documentation](#documentation)
8. [Testing](#testing)
9. [Community](#community)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for everyone, regardless of:
- Experience level
- Gender identity
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion
- Nationality

### Expected Behavior

- Be respectful and constructive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards others
- Accept constructive criticism gracefully

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information
- Inappropriate conduct or language

**Enforcement**: Violations may result in temporary or permanent ban. Report issues to sefy76@gmail.com.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Found a bug? Help us fix it!

1. **Check existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, toolkit version)
   - Screenshots if applicable
   - Error messages (full traceback)

**Example**:
```
Title: Classification engine crashes with negative Zr values

Environment:
- OS: Windows 11
- Python: 3.10.5
- Toolkit: v2.0

Steps to reproduce:
1. Load dataset with Zr = -5.2
2. Select "TAS Diagram" classification
3. Click "Run"

Expected: Error message about invalid values
Actual: Program crashes with AttributeError

Error message:
[paste full traceback here]
```

### ✨ Suggesting Features

Have an idea? We'd love to hear it!

1. **Check existing feature requests** first
2. **Open a new issue** with tag `enhancement`
3. **Describe**:
   - What problem does it solve?
   - Who would benefit?
   - How should it work?
   - Any alternative approaches?

### 📝 Improving Documentation

Documentation is crucial! You can help by:

- Fixing typos or clarifying confusing sections
- Adding examples
- Writing tutorials
- Translating to other languages
- Creating video tutorials
- Improving code comments

**Small fixes**: Edit directly on GitHub and submit PR  
**Large changes**: Open an issue to discuss first

### 🧪 Testing

Help us ensure quality:

- Test with your own data
- Test on different operating systems
- Test with different instruments
- Report what works and what doesn't
- Share your use cases

### 💬 Answering Questions

Help others in:
- GitHub Discussions
- Issue comments
- Email support

---

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Text editor or IDE (VS Code, PyCharm recommended)
- Basic Python knowledge

### Setup Process

1. **Fork the repository**
   - Click "Fork" button on GitHub
   - This creates your own copy

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/scientific-toolkit.git
   cd scientific-toolkit
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/sefy-levy/scientific-toolkit.git
   ```

4. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

5. **Install in development mode**
   ```bash
   pip install -r requirements.txt
   pip install -e .  # Editable install
   ```

6. **Install development tools** (optional but recommended)
   ```bash
   pip install pytest black flake8 mypy
   ```

### Keeping Your Fork Updated

```bash
# Fetch latest changes from original repo
git fetch upstream

# Merge into your local main branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

---

## Coding Standards

### Python Style

We follow **PEP 8** with some flexibility:

- **Line length**: 100 characters (not strict 79)
- **Indentation**: 4 spaces
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`

### Code Formatting

Use `black` for consistent formatting:

```bash
black Scientific-Toolkit.py plugins/ engines/
```

### Linting

Check code quality with `flake8`:

```bash
flake8 . --max-line-length=100 --ignore=E203,W503
```

### Type Hints

Use type hints for new code (not required for old code):

```python
def process_data(df: pd.DataFrame, element: str) -> pd.DataFrame:
    """Process geochemical data."""
    return df[df[element] > 0]
```

### Documentation Strings

Use docstrings for all public functions/classes:

```python
def calculate_ratio(numerator: float, denominator: float) -> float:
    """
    Calculate ratio of two elements.
    
    Args:
        numerator: Value for numerator
        denominator: Value for denominator
        
    Returns:
        Ratio value, or np.nan if denominator is zero
        
    Example:
        >>> calculate_ratio(10.0, 2.0)
        5.0
    """
    if denominator == 0:
        return np.nan
    return numerator / denominator
```

### Comments

- Write clear, concise comments
- Explain *why*, not *what*
- Keep comments up-to-date with code changes
- Aim for 15-25% comment ratio

**Good comment**:
```python
# Apply drift correction because long run times (>4 hours) 
# show systematic Zr depletion in standards
corrected_zr = apply_drift_correction(raw_zr)
```

**Bad comment**:
```python
# Calculate corrected Zr
corrected_zr = apply_drift_correction(raw_zr)  # obvious from function name
```

---

## Pull Request Process

### Before Creating PR

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow coding standards
   - Test your changes

3. **Commit with clear messages**
   ```bash
   git add .
   git commit -m "Add XRF drift correction for Niton analyzers"
   ```

   Good commit messages:
   - Start with verb (Add, Fix, Update, Remove)
   - Be specific
   - Explain why if not obvious

4. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

### Creating the PR

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Fill out the template:

   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   How was this tested?
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Comments added/updated
   - [ ] Documentation updated
   - [ ] No new warnings
   - [ ] Tested on my system
   
   ## Screenshots (if applicable)
   ```

### Review Process

1. **Automated checks** will run (if configured)
2. **Maintainer review** - may take a few days
3. **Respond to feedback** - make requested changes
4. **Approval & merge** - celebrate! 🎉

### After Merge

- Delete your feature branch
- Update your fork's main branch
- Close related issues

---

## Plugin Development

### Plugin Structure

Plugins follow a standard structure:

```python
class MyInstrumentPlugin:
    """
    Brief description of instrument.
    
    Attributes:
        name: Display name
        version: Plugin version
        instrument_type: Category
    """
    
    def __init__(self, root):
        self.root = root
        self.name = "My Instrument"
        self.version = "1.0.0"
        self.instrument_type = "hardware"
        
    def connect(self):
        """Establish connection to instrument."""
        pass
        
    def acquire(self):
        """Acquire data from instrument."""
        pass
        
    def process(self, data):
        """Process raw data."""
        return data
```

### Plugin Guidelines

- **Single responsibility**: One plugin = one instrument/feature
- **Error handling**: Catch and report errors gracefully
- **Dependencies**: Document any special requirements
- **Configuration**: Use JSON files for settings
- **Testing**: Test with real instruments if possible

### Classification Plugin

To add a new classification system, create JSON file in `engines/classification/`:

```json
{
  "name": "My Classification",
  "version": "1.0",
  "description": "Classify samples based on X vs Y",
  "required_columns": ["X_ppm", "Y_ppm"],
  "algorithm": "boundaries",
  "regions": [
    {
      "name": "Type A",
      "x_min": 0, "x_max": 100,
      "y_min": 0, "y_max": 50
    }
  ]
}
```

See [docs/PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for complete guide.

---

## Documentation

### Where to Document

1. **Code comments**: Inline for complex logic
2. **Docstrings**: All public functions/classes
3. **README.md**: Project overview
4. **docs/ folder**: Detailed guides
5. **Examples**: Sample code in docs/examples/
6. **Tutorials**: Step-by-step in docs/tutorials/

### Documentation Style

- Clear, concise language
- Practical examples
- Screenshots where helpful
- Keep up-to-date
- Test examples actually work

### Building Documentation

If using Sphinx (future):

```bash
cd docs/
make html
```

---

## Testing

Currently, the project has minimal automated tests. We welcome contributions!

### Manual Testing

Before submitting PR:

1. Test your changes work as expected
2. Test on your OS
3. Test with real data if possible
4. Check no existing features broke

### Writing Tests (Future)

We plan to use `pytest`. Example:

```python
# tests/test_ratio_calculation.py
import pytest
from engines.calculations import calculate_ratio

def test_normal_ratio():
    assert calculate_ratio(10, 2) == 5

def test_zero_denominator():
    assert np.isnan(calculate_ratio(10, 0))

def test_negative_values():
    assert calculate_ratio(-10, -2) == 5
```

Run tests:
```bash
pytest tests/
```

---

## Community

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: Questions, ideas, show-and-tell
- **Email**: sefy76@gmail.com (for sensitive matters)

### Getting Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in academic citations (for major contributions)

### Becoming a Maintainer

Active, quality contributors may be invited to become maintainers with commit access.

---

## Questions?

- 📚 Read [USER_GUIDE.md](USER_GUIDE.md)
- 🐛 Check [existing issues](https://github.com/sefy-levy/scientific-toolkit/issues)
- 💬 Ask in [Discussions](https://github.com/sefy-levy/scientific-toolkit/discussions)
- 📧 Email: sefy76@gmail.com

---

## License

By contributing, you agree that your contributions will be licensed under the same CC BY-NC-SA 4.0 license that covers this project.

---

## Thank You! 🙏

Your contributions make this project better for everyone. Every PR, issue report, documentation improvement, and test case helps the scientific community.

**Happy Contributing!** 🎉

---

*Last updated: 2026*
