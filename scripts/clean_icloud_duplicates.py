#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Gustavo R. Anjos
# Email: gustavo.rabello@gmail.com
# Date: 2026-07-23
# File: clean_icloud_duplicates.py

"""Safely remove iCloud-style duplicate files (``name 2.ext``, ``name 3.ext``).

iCloud Drive resolves sync conflicts by leaving a numbered copy next to the
original: ``Makefile`` gains a ``Makefile 2`` sibling, ``report.pdf`` gains a
``report 2.pdf`` and so on. This tool finds those copies and moves them to the
Trash, with several guards so that **no genuine project file is ever removed**:

* A file is only a candidate when its name is ``<base> <N>`` (a *space* then a
  number ``N >= 2``) *and* the canonical ``<base>`` exists in the same folder.
  Series such as ``cfd_1.png``/``cfd_2.png`` (underscore) or
  ``flex-theme-2-0.md`` (hyphen) never match, because iCloud always uses a
  space before the number.
* Files tracked by git are **never** touched -- if a numbered file was
  committed on purpose, it is a real project file, not a conflict copy.
* Nothing is deleted without ``--apply``; the default is a dry run.
* Removals go to the Trash (recoverable), not an unrecoverable ``rm``.

Run ``python scripts/clean_icloud_duplicates.py`` for a preview, then
``python scripts/clean_icloud_duplicates.py --apply`` to move the copies out.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:  # Optional: nicer colours, already available in the pelican env.
    from colorama import Fore, Style, init as _colorama_init

    _colorama_init(autoreset=True)
except Exception:  # pragma: no cover - colour is a convenience only.
    class _NoColor:
        def __getattr__(self, _name):
            return ''

    Fore = Style = _NoColor()

try:  # Optional: proper "Put Back" metadata when available.
    from send2trash import send2trash as _send2trash
except Exception:  # pragma: no cover - we fall back to ~/.Trash.
    _send2trash = None

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

# ``<base> <N>`` with a space before the number and an optional extension.
# ``<N>`` must be 2 or greater, matching how iCloud names conflict copies.
DUPLICATE_RE = re.compile(r'^(?P<base>.+?) (?P<num>\d+)(?P<ext>\..*)?$')

# Build output, caches and virtual-envs are never source files; skipping them
# keeps the scan fast and focused on content a person actually edits.
DEFAULT_EXCLUDES = {
    '.git', '.hg', '.svn',
    '__pycache__', 'node_modules',
    '.venv', 'venv', 'env', 'ENV',
    '.tox', '.nox', '.mypy_cache', '.pytest_cache', '.ropeproject',
}


def supports_color() -> bool:
    """Colour only a real terminal, and honour the NO_COLOR convention."""
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('TERM') == 'dumb':
        return False
    return sys.stdout.isatty()


_COLOR = supports_color()


def paint(text: str, *styles: str) -> str:
    """Wrap ``text`` in the given styles, or return it plain when disabled."""
    if not _COLOR or not styles:
        return text
    return ''.join(styles) + text + Style.RESET_ALL


def git_tracked_files(root: Path) -> set[Path]:
    """Return absolute paths of every git-tracked file, or empty if no repo."""
    try:
        toplevel = subprocess.run(
            ['git', '-C', str(root), 'rev-parse', '--show-toplevel'],
            check=True, text=True, capture_output=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return set()

    repo_root = Path(toplevel)
    try:
        listing = subprocess.run(
            ['git', '-C', str(repo_root), 'ls-files', '-z'],
            check=True, text=True, capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return set()

    tracked = set()
    for entry in listing.split('\0'):
        if entry:
            tracked.add((repo_root / entry).resolve())
    return tracked


def iter_files(root: Path, excludes: set[str]):
    """Yield files under ``root``, pruning excluded and ``*.nosync`` folders."""
    for current, directories, files in os.walk(root):
        directories[:] = [
            name for name in directories
            if name not in excludes and not name.endswith('.nosync')
        ]
        for name in files:
            yield Path(current) / name


def canonical_for(path: Path) -> Path | None:
    """Return the original file a numbered copy shadows, if one exists.

    Only returns a path when ``path`` looks like ``<base> <N>`` with ``N >= 2``
    and the reconstructed ``<base>`` file sits beside it. Otherwise ``None``.
    """
    match = DUPLICATE_RE.match(path.name)
    if not match:
        return None
    if int(match.group('num')) < 2:
        return None

    original_name = match.group('base') + (match.group('ext') or '')
    if original_name == path.name:
        return None

    candidate = path.with_name(original_name)
    if candidate.is_file():
        return candidate
    return None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def move_to_trash(path: Path) -> str:
    """Move ``path`` to the Trash and return a short description of where."""
    if _send2trash is not None:
        _send2trash(str(path))
        return 'Trash (send2trash)'

    trash_dir = Path.home() / '.Trash'
    trash_dir.mkdir(parents=True, exist_ok=True)
    target = trash_dir / path.name
    if target.exists():
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        target = trash_dir / '{} {}{}'.format(path.stem, stamp, path.suffix)
    shutil.move(str(path), str(target))
    return '~/.Trash/{}'.format(target.name)


def human_size(size: int) -> str:
    value = float(size)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if value < 1024 or unit == 'GB':
            return '{:.1f} {}'.format(value, unit)
        value /= 1024
    return '{:.1f} GB'.format(value)


def collect_duplicates(root: Path, excludes: set[str], tracked: set[Path]):
    """Return (removable, protected) lists of duplicate descriptors."""
    removable = []
    protected = []
    for path in iter_files(root, excludes):
        canonical = canonical_for(path)
        if canonical is None:
            continue

        try:
            identical = file_sha256(path) == file_sha256(canonical)
        except OSError:
            identical = False

        descriptor = {
            'duplicate': path,
            'canonical': canonical,
            'identical': identical,
            'size': path.stat().st_size,
        }

        if path.resolve() in tracked:
            descriptor['reason'] = 'tracked by git'
            protected.append(descriptor)
        else:
            removable.append(descriptor)

    removable.sort(key=lambda item: str(item['duplicate']).lower())
    protected.sort(key=lambda item: str(item['duplicate']).lower())
    return removable, protected


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def print_header(root: Path, apply: bool, permanent: bool) -> None:
    mode = 'APPLY' if apply else 'DRY RUN'
    mode_style = (Fore.RED, Style.BRIGHT) if apply else (Fore.CYAN, Style.BRIGHT)
    action = 'delete permanently' if permanent else 'move to Trash'
    print()
    print(paint('  🧹  iCloud duplicate cleanup', Fore.CYAN, Style.BRIGHT))
    print(paint('  ' + '─' * 60, Fore.CYAN))
    print('  {}  {}'.format(paint('Scanning:', Style.BRIGHT), root))
    print('  {}      {}'.format(
        paint('Mode:', Style.BRIGHT), paint(mode, *mode_style)))
    print('  {}    {}'.format(paint('Action:', Style.BRIGHT), action))
    print(paint('  ' + '─' * 60, Fore.CYAN))


def print_entries(descriptors, root: Path) -> None:
    for item in descriptors:
        duplicate = relative(item['duplicate'], root)
        canonical = relative(item['canonical'], root)
        if item['identical']:
            tag = paint(' identical copy ', Fore.GREEN, Style.BRIGHT)
        else:
            tag = paint(' DIFFERS from original ', Fore.YELLOW, Style.BRIGHT)
        print('  {} {}   {}'.format(
            paint('✚', Fore.MAGENTA, Style.BRIGHT),
            paint(duplicate, Fore.WHITE, Style.BRIGHT),
            paint('(' + human_size(item['size']) + ')', Fore.WHITE)))
        print('      {} {}   {}'.format(
            paint('↳ original:', Fore.CYAN), canonical, tag))


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Move iCloud-style duplicate files to the Trash safely.')
    parser.add_argument(
        '--root', type=Path, default=PROJECT_DIR,
        help='directory to scan (default: the project root)')
    parser.add_argument(
        '--apply', action='store_true',
        help='actually remove the duplicates (default: dry run only)')
    parser.add_argument(
        '--permanent', action='store_true',
        help='delete permanently instead of moving to the Trash (discouraged)')
    parser.add_argument(
        '--exclude', action='append', default=[], metavar='NAME',
        help='additional folder name to skip (repeatable)')
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(paint('  ✖  Not a directory: {}'.format(root),
                    Fore.RED, Style.BRIGHT))
        return 2

    excludes = DEFAULT_EXCLUDES | set(args.exclude)
    tracked = git_tracked_files(root)

    print_header(root, args.apply, args.permanent)
    if not tracked:
        print(paint('  ⚠  No git repository detected: the "never delete '
                    'tracked files" guard is inactive here.',
                    Fore.YELLOW, Style.BRIGHT))
        print(paint('  ' + '─' * 60, Fore.CYAN))

    removable, protected = collect_duplicates(root, excludes, tracked)

    if protected:
        print(paint('\n  Protected (git-tracked, left untouched):',
                    Fore.BLUE, Style.BRIGHT))
        for item in protected:
            print('    {} {}'.format(
                paint('•', Fore.BLUE),
                paint(relative(item['duplicate'], root), Fore.BLUE)))

    if not removable:
        print(paint('\n  ✓  No removable iCloud duplicates found. All clean!',
                    Fore.GREEN, Style.BRIGHT))
        print()
        return 0

    print(paint('\n  Duplicates found ({}):'.format(len(removable)),
                Fore.MAGENTA, Style.BRIGHT))
    print_entries(removable, root)

    total = sum(item['size'] for item in removable)
    differing = sum(1 for item in removable if not item['identical'])

    print(paint('\n  ' + '─' * 60, Fore.CYAN))
    summary = '  {} duplicate file(s), {} reclaimable'.format(
        len(removable), human_size(total))
    if differing:
        summary += '  ({} differ from the original — review before applying)'.format(
            differing)
    print(paint(summary, Style.BRIGHT))

    if not args.apply:
        print(paint('\n  Dry run only — nothing was changed.',
                    Fore.CYAN, Style.BRIGHT))
        print('  Re-run with {} to move them to the Trash:'.format(
            paint('--apply', Fore.GREEN, Style.BRIGHT)))
        print(paint('      python {} --apply'.format(
            relative(Path(__file__).resolve(), root)), Fore.GREEN))
        print()
        return 0

    print()
    removed = 0
    reclaimed = 0
    for item in removable:
        path = item['duplicate']
        try:
            if args.permanent:
                path.unlink()
                where = 'deleted permanently'
            else:
                where = move_to_trash(path)
        except OSError as error:
            print('  {} {}  ({})'.format(
                paint('✖', Fore.RED, Style.BRIGHT),
                relative(path, root), error))
            continue
        removed += 1
        reclaimed += item['size']
        print('  {} {}  {}'.format(
            paint('✓', Fore.GREEN, Style.BRIGHT),
            paint(relative(path, root), Fore.WHITE),
            paint('→ ' + where, Fore.GREEN)))

    print(paint('\n  ' + '─' * 60, Fore.CYAN))
    print(paint('  ✓  Removed {} duplicate file(s), reclaimed {}.'.format(
        removed, human_size(reclaimed)), Fore.GREEN, Style.BRIGHT))
    print()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
