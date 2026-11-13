"""Package the three static marketing pages and their public assets."""
import argparse
import tarfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
with tarfile.open(args.output, 'w:gz') as archive:
    for path in sorted((root / 'marketing-preview').rglob('*')):
        if not path.is_file() or path.name.endswith('-source.js'):
            continue
        if path.suffix not in ('.html', '.css', '.js', '.png', '.svg', '.webp'):
            continue
        archive.add(path, arcname=str(path.relative_to(root / 'marketing-preview')))
    for path in sorted((root / 'cloud-preview/assets').rglob('*')):
        if path.is_file():
            archive.add(path, arcname=str(path.relative_to(root)))
print('Static marketing package created.')
