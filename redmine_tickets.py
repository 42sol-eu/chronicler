#!/usr/bin/env python3
"""
Standalone script to list Redmine tickets.
Can be executed directly without installing the chronicler package.
"""

import sys
from pathlib import Path

# Add the src directory to Python path so we can import chronicler modules
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from chronicler.redmine_client import main

if __name__ == "__main__":
    main()
