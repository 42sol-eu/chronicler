#!/usr/bin/env python3
"""Test script for Jira CLI functionality."""

import click
from click.testing import CliRunner
from rich.console import Console

console = Console()

def test_jira_command():
    """Test the Jira command help and structure."""
    from src.chronicler.__main__ import cli
    
    runner = CliRunner()
    
    # Test help for jira command
    result = runner.invoke(cli, ['jira', '--help'])
    console.print("[bold]Jira command help:[/bold]")
    console.print(result.output)
    
    # Test main CLI help to see if jira command is listed
    result = runner.invoke(cli, ['--help'])
    console.print("\n[bold]Main CLI help (should include jira command):[/bold]")
    console.print(result.output)

if __name__ == "__main__":
    test_jira_command()
