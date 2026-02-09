import sys
from pathlib import Path

# Add project root to sys.path so 'shared' can be imported
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
