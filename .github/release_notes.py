"""Release title and notes from CHANGELOG.md for one platform.

Usage: python .github/release_notes.py <version> <Windows|macOS>
Writes release-notes.md and appends `name=...` to $GITHUB_OUTPUT.
Keeps changelog bullets marked **Both:** or **<platform>:** from the `## [version]` section.
"""
import os
import re
import sys

version, platform = sys.argv[1], sys.argv[2]
text = open('CHANGELOG.md', encoding='utf-8').read()
match = re.search(r'^## \[' + re.escape(version) + r'\][^\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
lines = []
if match:
    for line in match.group(1).splitlines():
        if line.startswith('- ') and ('**Both:**' in line or f'**{platform}:**' in line):
            lines.append(re.sub(r'\*\*(Both|' + platform + r'):\*\* ?', '', line))
notes = '\n'.join(lines) or 'See CHANGELOG.md.'
open('release-notes.md', 'w', encoding='utf-8').write(notes + '\n')
with open(os.environ.get('GITHUB_OUTPUT', os.devnull), 'a', encoding='utf-8') as out:
    out.write(f'name=Haste2 Battery {version} ({platform})\n')
