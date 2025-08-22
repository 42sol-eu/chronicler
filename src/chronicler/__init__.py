"""Chronicler - A CLI application."""
from pathlib import Path

chronicler_path = Path(__file__).parent

with open(chronicler_path /"__VERSION__", "r") as version_file:
    __version__ = version_file.read().strip()
