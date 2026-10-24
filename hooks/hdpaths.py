"""The server-side paths the hooks share with hd (hd.fork_clone); HD_SERVER_HOME / INTEGRATION_CLONE override."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the harness repo
from hd import fork_clone  # noqa: E402,F401
