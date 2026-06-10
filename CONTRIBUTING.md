# Contributing to TruShell

Thank you for your interest in contributing! This project follows an open and collaborative workflow.

## How to contribute

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-change`.
3. Run tests locally: `python -m pytest`
4. Submit a pull request and describe the changes clearly.

## Coding standards

- Follow the existing style and keep the code readable.
- Use `black` for formatting and `ruff` for linting.
- Keep logic simple and beginner-friendly.

## Development Environment Setup

To start contributing safely, you need to set up your local development environment. We strongly recommend isolating your workspace before installing dependencies.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/TruFoundation/TruShell.git
   cd TruShell
   ```

2. **Create and activate a virtual environment:**
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install TruShell in editable mode:**

   ```
   pip install -e .
   ```
4. **Run the test suite:**
   ```
   python -m pytest
    ```
## Issues
If you find a bug or want to request a feature, please open an issue with a clear description and reproduction steps.
