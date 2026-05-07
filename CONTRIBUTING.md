# Contributing to lazyk8s

Thanks for your interest in contributing to lazyk8s! This guide will help you get started.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, kubectl version)
- Screenshots if applicable

### Suggesting Features

Feature requests are welcome! Please open an issue describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Pull Requests

1. **Fork the repository** and create your branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow existing code style
   - Add comments for complex logic

3. **Test your changes**
   - Test with different Kubernetes clusters (minikube, kind, etc.)
   - Verify all keybindings work
   - Check on your platform (Linux/macOS/Windows)

4. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of your changes"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Provide a clear description of what you changed and why
   - Reference any related issues

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/lazyk8s.git
cd lazyk8s

# Install dependencies
pip install textual

# Make the script executable (Linux/macOS)
chmod +x lazyk8s

# Run locally
./lazyk8s
```

## Code Guidelines

- Keep functions focused and single-purpose
- Use descriptive variable names
- Add docstrings for complex functions
- Maintain the existing UI style and color scheme

## Areas We'd Love Help With

- Windows compatibility improvements
- Additional resource types (ConfigMaps, Secrets, etc.)
- Performance optimizations for large clusters
- Documentation improvements
- Bug fixes

## Questions?

Feel free to open an issue for any questions about contributing!
