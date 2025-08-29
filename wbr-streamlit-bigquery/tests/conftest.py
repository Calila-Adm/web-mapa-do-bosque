# Ensure the project root (containing the 'src' directory) is on sys.path for imports like 'src.wbr...'
import os
import sys
TESTS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(TESTS_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
