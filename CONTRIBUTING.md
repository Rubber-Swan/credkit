# Contributing to credkit

Thanks for your interest in contributing to credkit!

## Getting Started

```bash
git clone https://github.com/jt-hill/credkit.git
cd credkit
uv sync --dev
uv run pytest tests/ -v
```

## How to Contribute

### Reporting Issues

- Check existing issues first
- Include minimal reproducible example
- Specify Python version and environment

### Pull Requests

1. Fork the repo and create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass: `uv run pytest tests/ -v`
4. Update documentation if needed
5. Submit PR with clear description

## Code Standards

- **Type hints required** for all functions
- **Decimal for all financial math** (never float)
- **Immutable dataclasses** (use `@dataclass(frozen=True)`)
- **Comprehensive tests** covering edge cases
- Follow existing patterns in the codebase

## Testing

All PRs must include tests. We aim for 100% coverage of core logic.

```bash
uv run pytest tests/ -v
```

## Contributor License

By submitting a pull request, you hereby grant to the maintainer
and to recipients of software distributed by the maintainer a perpetual,
worldwide, non-exclusive, no-charge, royalty-free, irrevocable
copyright license to reproduce, prepare derivative works of,
publicly display, publicly perform, sublicense, and distribute
your contributions and derivative works.

You represent that you have the legal right to make this grant and that your
contribution is your original work or properly licensed from third parties.
