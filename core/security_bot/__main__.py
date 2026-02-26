"""Runner script for Security Bot."""
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from core.security_bot.bot import main

if __name__ == "__main__":
    main()
