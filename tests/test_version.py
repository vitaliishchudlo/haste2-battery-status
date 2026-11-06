import re
from pathlib import Path

from haste2_battery import __version__

ROOT = Path(__file__).resolve().parents[1]


def test_version_info_matches_package():
    text = (ROOT / 'installers' / 'windows' / 'version_info.txt').read_text(encoding='utf-8')
    commas = ', '.join(__version__.split('.') + ['0']).replace(', ', ',')
    assert f'filevers=({commas})' in text
    assert text.count(f"'{__version__}'") == 2


def test_changelog_mentions_current_version():
    assert re.search(rf'^## \[{re.escape(__version__)}\]', (ROOT / 'CHANGELOG.md').read_text(encoding='utf-8'), re.M)
