#!/usr/bin/env python3
"""Runner that imports and runs all test modules for vernacular-creator-agents.

Usage:
    python test_agents.py
    python -m pytest test_agents.py -v
"""

import pytest
import sys


def main():
    """Run all test modules in the tests/ directory."""
    exit_code = pytest.main([
        "tests/",
        "-v",
        "--tb=short",
        "--no-header",
    ])
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
