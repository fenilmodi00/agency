"""Tests for --phase CLI argument in main.py."""

from __future__ import annotations

import argparse
import pytest

from main import parse_args


class TestPhaseArgument:
    """Verify --phase argument wiring in parse_args()."""

    def test_phase_arg_exists(self) -> None:
        """--phase is accepted and stored on the namespace."""
        args = parse_args(["test brief", "--phase", "scout"])
        assert args.phase == "scout"

    def test_phase_default_is_all(self) -> None:
        """Default value for --phase is 'all'."""
        args = parse_args(["test brief"])
        assert args.phase == "all"

    def test_phase_valid_choices(self) -> None:
        """All STAR phases plus 'all' are accepted."""
        for phase in ("scout", "target", "activate", "report", "all"):
            args = parse_args(["test brief", "--phase", phase])
            assert args.phase == phase

    def test_phase_rejects_invalid_value(self) -> None:
        """An unrecognised phase value is rejected."""
        with pytest.raises(SystemExit):
            parse_args(["test brief", "--phase", "invalid"])

    def test_phase_coexists_with_other_args(self) -> None:
        """--phase works alongside --send, --approve-each, --max-creators."""
        args = parse_args([
            "test brief",
            "--phase", "target",
            "--send",
            "--approve-each",
            "--max-creators", "5",
        ])
        assert args.phase == "target"
        assert args.send is True
        assert args.approve_each is True
        assert args.max_creators == 5