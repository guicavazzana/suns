"""Make the package importable for tests without needing an editable install.

Note: on this machine, `pip install -e .` silently fails to make the package
importable, because pip/hatchling's editable install writes a redirect .pth
file with an absolute path, and CPython's site.py reads .pth files using the
Windows ANSI codepage (cp1252 here) rather than UTF-8 - which mangles the
accented "Dissertação" folder name in the path, so the directory no longer
resolves and site.py silently skips adding it (no error, it's just absent
from sys.path). This is a Windows/locale quirk, not a bug in this package:
a normal (non-editable) `pip install .` works fine, and so will installing
a published wheel/sdist on any machine. We insert src/ directly here so the
test suite doesn't depend on either workaround.
"""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
