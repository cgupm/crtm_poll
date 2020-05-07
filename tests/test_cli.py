#!/usr/bin/env python

"""Test cli from `crtm_poll` package."""

from click.testing import CliRunner

from crtm_poll import cli


class TestCLI:
    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'Console script for crtm_poll.' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '-h, --help                 Show this message and exit.' in \
               help_result.output

    def fail(self):
        assert 0
