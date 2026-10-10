# Contributing to Contribution Farm

Thank you for your interest in contributing to Contribution Farm.

## Development Workflow

1. Fork the repository on GitHub.
2. Clone your forked repository locally.
3. Create a descriptive branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Make your modifications.
5. Execute the test suite to ensure all unit tests pass:
   ```bash
   python -m unittest discover tests
   ```
6. Commit your changes following conventional commit syntax:
   ```bash
   git commit -m "feat: description of changes"
   ```
7. Push your branch to GitHub:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Open a Pull Request against the main branch.

## Code Standards

- Maintain zero comment lines across scripts and code.
- Ensure all tests pass cleanly.
- Keep dependencies minimal using the Python Standard Library.
