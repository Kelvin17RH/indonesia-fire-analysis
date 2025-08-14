# Contributing to Indonesia Fire Analysis System

Thank you for your interest in contributing to the Indonesia Fire Analysis System! This document provides guidelines for contributing to this project.

## 🤝 How to Contribute

### Reporting Issues
- **Bug Reports**: Use the GitHub issue tracker to report bugs
- **Feature Requests**: Suggest new features or improvements
- **Documentation**: Help improve documentation and examples

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/indonesia-fire-analysis.git
   cd indonesia-fire-analysis
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]  # Install development dependencies
   ```

3. **Run tests**
   ```bash
   pytest tests/
   ```

### Code Style

- **Python**: Follow PEP 8 style guidelines
- **Formatting**: Use `black` for code formatting
- **Linting**: Use `flake8` for linting
- **Type Hints**: Add type hints where appropriate

```bash
# Format code
black .

# Check linting
flake8 src/

# Run type checking
mypy src/
```

### Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   python demo.py  # Test with demo data
   pytest tests/   # Run test suite
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add: your descriptive commit message"
   git push origin feature/your-feature-name
   ```

5. **Create pull request**
   - Provide clear description of changes
   - Reference any related issues
   - Ensure all checks pass

## 🧪 Testing

### Test Structure
```
tests/
├── test_data_extraction/
├── test_spatial_processing/
├── test_visualization/
└── test_utils/
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test module
pytest tests/test_data_extraction/
```

## 📚 Documentation

- **Code Documentation**: Use clear docstrings
- **README**: Keep README.md up to date
- **Examples**: Add examples for new features
- **API Documentation**: Document public interfaces

### Documentation Format
```python
def extract_fire_data(start_date: str, end_date: str) -> xr.Dataset:
    """
    Extract fire data for specified time period.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        xarray.Dataset with fire detection data
        
    Raises:
        ValueError: If date format is invalid
        
    Example:
        >>> fire_data = extract_fire_data("2019-01-01", "2019-12-31")
        >>> print(f"Found {len(fire_data.fire_id)} fires")
    """
```

## 🌟 Areas for Contribution

### High Priority
- **Real API Integration**: Replace synthetic data with actual NASA API calls
- **Performance Optimization**: Improve processing speed for large datasets
- **Unit Tests**: Expand test coverage
- **Documentation**: Add more examples and tutorials

### Medium Priority
- **Additional Sensors**: Add support for more satellite instruments
- **Machine Learning**: Fire prediction and risk modeling
- **Web Interface**: Create web-based visualization dashboard
- **Mobile App**: Mobile interface for field researchers

### Low Priority
- **Database Integration**: Add database backend support
- **Cloud Deployment**: Docker containers and cloud deployment guides
- **Multi-language Support**: Internationalization

## 🔬 Data Science Contributions

### New Analysis Methods
- Advanced statistical models
- Machine learning algorithms
- Time series forecasting
- Spatial analysis techniques

### Visualization Improvements
- Interactive dashboard components
- 3D visualizations
- Animation capabilities
- Mobile-responsive designs

### Data Integration
- Additional satellite sensors
- Weather data integration
- Socioeconomic data
- Ground truth validation

## 🐛 Bug Reports

When reporting bugs, please include:
- **Environment**: Python version, OS, package versions
- **Steps to Reproduce**: Clear instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Error Messages**: Full error logs
- **Sample Data**: Minimal example if possible

## 💡 Feature Requests

For feature requests, please provide:
- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternative Solutions**: Other approaches considered
- **Additional Context**: Screenshots, examples, references

## 📄 License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

## 🙋‍♀️ Getting Help

- **GitHub Issues**: For technical questions and bug reports
- **Discussions**: For general questions and ideas
- **Email**: contact@example.com for private inquiries

## 🎉 Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes for significant contributions
- Academic publications (with permission)

Thank you for helping make this project better! 🔥🇮🇩