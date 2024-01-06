import sys
from pathlib import Path

# Set the path to the project root (where the modules are)
project_root = Path(__file__).parent.parent

# Add the project root to sys.path
sys.path.insert(0, str(project_root))
