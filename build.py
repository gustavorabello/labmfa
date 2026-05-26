# -*- coding: utf-8 -*-
## =================================================================== ##
#  File: build.py
#  Created: 31-Oct-2025
#  Maintained by: Gustavo Rabello dos Anjos
#  E-mail: gustavo.rabello@gmail.com
#  Description: Deploys local Pelican static site to remote server via SFTP
#  Compatible with Python 3.13+
## =================================================================== ##

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from subprocess import call
from stat import S_ISDIR
from colorama import init, Fore, Style
from student_aliases import STUDENT_AUTHOR_ALIASES

# Initialize colorama
init(autoreset=True)

BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / 'content/pages/person/gustavoRabello.rst'
PERSON_DIR = BASE_DIR / 'content/pages/person'
STUDENTS_PATH = BASE_DIR / 'content/pages/students.rst'
BIB_DIR = Path('/Users/gustavo/projects/misc/latex-personal')
JOURNALS_BIB = BIB_DIR / 'journals.bib'
CONFERENCES_BIB = BIB_DIR / 'papers_conferences.bib'
BOOKS_BIB = BIB_DIR / 'books.bib'
CHAPTERS_BIB = BIB_DIR / 'chapters.bib'
PUBLICATIONS_START = '.. AUTO-GENERATED PUBLICATIONS START: run build.py --update-publications'
PUBLICATIONS_END = '.. AUTO-GENERATED PUBLICATIONS END'
STUDENT_ARTICLES_START = '.. AUTO-GENERATED COAUTHORED ARTICLES START: run build.py --update-publications'
STUDENT_ARTICLES_END = '.. AUTO-GENERATED COAUTHORED ARTICLES END'
REMOTE_SITE_DIR = '/html'
REMOTE_MANIFEST = '.labmfa-manifest.json'
SFTP_TIMEOUT_SECONDS = 60
TEXT_SUFFIXES = {'.css', '.html', '.js', '.json', '.txt', '.xml'}

transport = None
sftp = None


def connect_sftp():
    """Open the remote connection only when deploying the generated site."""
    import paramiko
    import user

    global transport, sftp
    transport = paramiko.Transport((user.server, user.port))
    transport.connect(username=user.username, password=user.password)
    transport.set_keepalive(30)
    sftp = paramiko.SFTPClient.from_transport(transport)
    sftp.get_channel().settimeout(SFTP_TIMEOUT_SECONDS)


def _braced_value(text, start):
    """Return the content and final index of a balanced BibTeX braced value."""
    if text[start] != '{':
        raise ValueError('Expected a braced BibTeX value')

    depth = 1
    index = start + 1
    while index < len(text) and depth:
        char = text[index]
        if char == '\\':
            index += 2
            continue
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        index += 1

    if depth:
        raise ValueError('Unclosed braced value in BibTeX input')
    return text[start + 1:index - 1], index


def _parse_fields(text):
    fields = {}
    index = 0
    while index < len(text):
        separator = re.match(r'[\s,]*', text[index:])
        index += separator.end()
        match = re.match(r'([A-Za-z][A-Za-z0-9_-]*)\s*=\s*', text[index:])
        if not match:
            break

        key = match.group(1).lower()
        index += match.end()
        if text[index:index + 1] == '{':
            value, index = _braced_value(text, index)
        elif text[index:index + 1] == '"':
            end = index + 1
            while end < len(text):
                if text[end] == '"' and text[end - 1] != '\\':
                    break
                end += 1
            value = text[index + 1:end]
            index = end + 1
        else:
            end = text.find(',', index)
            end = len(text) if end == -1 else end
            value = text[index:end].strip()
            index = end
        fields[key] = value
    return fields


def parse_bibtex(path, entry_type):
    """Read selected BibTeX entries without adding a build dependency."""
    source = path.read_text(encoding='utf-8')
    entries = []
    index = 0
    entry_re = re.compile(r'@([A-Za-z]+)\s*\{', re.IGNORECASE)

    while True:
        match = entry_re.search(source, index)
        if not match:
            return entries

        body, index = _braced_value(source, match.end() - 1)
        if match.group(1).lower() != entry_type.lower():
            continue
        try:
            _, fields_text = body.split(',', 1)
        except ValueError as error:
            raise ValueError('Invalid BibTeX entry in {}'.format(path)) from error
        entries.append(_parse_fields(fields_text))


def latex_to_text(value):
    """Convert the small LaTeX subset used by the publication metadata."""
    if not value:
        return ''

    while re.search(r'\\(?:textbf|emph)\{([^{}]*)\}', value):
        value = re.sub(r'\\(?:textbf|emph)\{([^{}]*)\}', r'\1', value)

    combining = {
        "'": '\u0301',
        '"': '\u0308',
        '~': '\u0303',
        '`': '\u0300',
        '^': '\u0302',
        'c': '\u0327',
    }

    def replace_accent(match):
        mark, character = match.groups()
        return unicodedata.normalize('NFC', character + combining[mark])

    value = re.sub(r'\{?\\([\'"`~^c])\{?([A-Za-z])\}?\}?',
                   replace_accent, value)
    value = value.replace(r'\&', '&').replace(r'\%', '%').replace(r'\_', '_')
    value = value.replace('{-}', '-').replace('--', '-').replace('~', ' ')
    return ' '.join(value.replace('{', '').replace('}', '').split())


def field(entry, name):
    return latex_to_text(entry.get(name, ''))


def rst_authors(entry):
    authors = field(entry, 'author').replace(' and ', '; ')
    if re.match(r'^[A-Z]\. ', authors):
        authors = authors.replace('. ', r'\. ', 1)
    return authors if authors.endswith('.') else authors + '.'


def linked_title(entry):
    title = field(entry, 'title')
    doi = field(entry, 'doi')
    url = field(entry, 'url')
    if doi:
        return '`{} <https://doi.org/{}>`_'.format(title, doi)
    if url and not re.search(r'\.pdf(?:$|[?#])', url, flags=re.IGNORECASE):
        return '`{} <{}>`_'.format(title, url)
    return '**{}**'.format(title)


def render_journal(entry):
    volume = field(entry, 'volume')
    number = field(entry, 'number')
    pages = field(entry, 'pages') or field(entry, 'article-number')
    issue = '({})'.format(number) if number else ''
    citation = ', vol. {}{}'.format(volume, issue) if volume else ''
    citation += ', {}'.format(pages) if pages else ''
    return '#. {} {}. *{}*{} ({}).'.format(
        rst_authors(entry), linked_title(entry), field(entry, 'journal'), citation,
        field(entry, 'year'))


def render_book(entry):
    details = [field(entry, 'publisher'), field(entry, 'address')]
    pages = field(entry, 'pages')
    if pages:
        details.append('{} pp.'.format(pages))
    return '#. {} {}. *{}* ({}).'.format(
        rst_authors(entry), linked_title(entry),
        ', '.join(part for part in details if part), field(entry, 'year'))


def render_chapter(entry):
    details = []
    chapter = field(entry, 'chapter')
    pages = field(entry, 'pages')
    if chapter:
        details.append('chap. {}'.format(chapter))
    if pages:
        details.append('pp. {}'.format(pages))
    details.extend([field(entry, 'publisher'), field(entry, 'address')])
    return '#. {} {}. In *{}*, {} ({}).'.format(
        rst_authors(entry), linked_title(entry), field(entry, 'booktitle'),
        ', '.join(part for part in details if part), field(entry, 'year'))


def render_conference(entry):
    event = field(entry, 'eventtitle')
    address = field(entry, 'address')
    details = ' ({})'.format(event) if event else ''
    details += ', {}'.format(address) if address else ''
    return '#. {} **{}**. *{}*{}, {}.'.format(
        rst_authors(entry), field(entry, 'title'), field(entry, 'booktitle'),
        details, field(entry, 'year'))


def render_publications(books, chapters, journals, conferences):
    lines = [
        PUBLICATIONS_START,
        '',
        '**publications**:',
        '',
        'The publications below include work authored by Prof. Gustavo R. Anjos and',
        'research developed with supervised students. Journal articles are highlighted',
        'in color. DOI and publisher links are provided when available. Conference',
        'entries provide bibliographic event information only; no article manuscript',
        'PDF is attached.',
        '',
        'Books',
        '~~~~~',
        '',
        '.. class:: publications-list book-publications',
        '',
    ]
    lines.extend(render_book(entry) for entry in books)
    lines.extend([
        '',
        'Book Chapters',
        '~~~~~~~~~~~~~',
        '',
        '.. class:: publications-list chapter-publications',
        '',
    ])
    lines.extend(render_chapter(entry) for entry in chapters)
    lines.extend([
        '',
        'Journal Articles',
        '~~~~~~~~~~~~~~~~',
        '',
        '.. class:: publications-list journal-publications',
        '',
    ])
    lines.extend(render_journal(entry) for entry in journals)
    lines.extend([
        '',
        'Conference Papers',
        '~~~~~~~~~~~~~~~~~',
        '',
        '.. class:: publications-list conference-publications',
        '',
    ])
    lines.extend(render_conference(entry) for entry in conferences)
    lines.extend(['', PUBLICATIONS_END, ''])
    return '\n'.join(lines)


def normalize_name(value):
    value = unicodedata.normalize('NFKD', latex_to_text(value))
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', value.lower()).split())


def name_tokens(value):
    ignored = {'da', 'das', 'de', 'do', 'dos', 'prof', 'msc', 'eng'}
    return [token for token in normalize_name(value).split() if token not in ignored]


def publication_authors(entry):
    return [author.strip() for author in re.split(
        r'\s+and\s+', field(entry, 'author'), flags=re.IGNORECASE)]


def is_professor_publication(entry):
    for author in publication_authors(entry):
        tokens = set(name_tokens(author))
        if 'anjos' in tokens and ('gustavo' in tokens or 'g' in tokens):
            return True
    return False

def slug_to_name(slug):
    """Convert camelCase profile slug to words."""
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', slug)

def initials(tokens):
    return ''.join(token[0] for token in tokens if token)

def is_student_author(slug, student_name, author):
    normalized_author = normalize_name(author)

    if normalized_author in STUDENT_AUTHOR_ALIASES.get(slug, set()):
        return True

    student_tokens = name_tokens(student_name)
    author_tokens = name_tokens(author)

    if len(student_tokens) < 2 or len(author_tokens) < 2:
        return False

    student_first = student_tokens[0]
    student_family = student_tokens[-1]
    student_given_tokens = student_tokens[:-1]

    student_given_initials = initials(student_given_tokens)

    author_set = set(author_tokens)

    if student_family not in author_set:
        return False

    author_without_family = [
        token for token in author_tokens
        if token != student_family
    ]

    # Caso com nome escrito por extenso:
    # Santos, Antonio Emanuel Marques
    if student_first in author_without_family:
        return True

    # Caso abreviado:
    # Santos, A. E. M.
    author_initials = ''.join(
        token[0] for token in author_without_family
        if token
    )

    if not author_initials:
        return False

    return student_given_initials.startswith(author_initials)

def render_student_publications(articles, conferences):
    lines = [
        STUDENT_ARTICLES_START,
        '',
        '**publications with Prof. Gustavo R. Anjos**:',
    ]
    if articles:
        lines.extend([
            '',
            'Journal Articles',
            '~~~~~~~~~~~~~~~~',
            '',
            '.. class:: publications-list journal-publications',
            '',
        ])
        lines.extend(render_journal(entry) for entry in articles)
    if conferences:
        lines.extend([
            '',
            'Conference Papers',
            '~~~~~~~~~~~~~~~~~',
            '',
            '.. class:: publications-list conference-publications',
            '',
        ])
        lines.extend(render_conference(entry) for entry in conferences)
    lines.extend(['', STUDENT_ARTICLES_END, ''])
    return '\n'.join(lines)


def update_generated_section(path, start_marker, end_marker, generated,
                             legacy_start=None):
    source = path.read_text(encoding='utf-8')
    if start_marker in source and end_marker in source:
        before = source.split(start_marker, 1)[0]
        after = source.split(end_marker, 1)[1].lstrip('\n')
    elif generated:
        references = '.. Place your references here'
        if references not in source:
            print(Fore.YELLOW + 'Warning: no reference anchor in {}'.format(path))
            return False
        if legacy_start and legacy_start in source:
            before = source.split(legacy_start, 1)[0]
        else:
            before = source.split(references, 1)[0]
        references_after = source.split(references, 1)[1]
        after = references + references_after
    else:
        return False

    if generated:
        updated = before.rstrip() + '\n\n' + generated + '\n' + after
    else:
        updated = before.rstrip() + '\n\n' + after
    if updated == source:
        return False

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    updated = re.sub(r'(?m)^:modified:.*$',
                     ':modified: {}'.format(timestamp), updated, count=1)
    path.write_text(updated, encoding='utf-8')
    return True


def student_profile_slugs():
    """Return all profile slugs in content/pages/person, except Gustavo's page."""
    return {
        path.stem
        for path in sorted(PERSON_DIR.glob('*.rst'))
        if path.resolve() != PROFILE_PATH.resolve()
    }

def update_student_publications(journals, conferences):
    """Publish article and conference coauthorship on all student profile pages."""
    shared_articles = [
        entry for entry in journals
        if is_professor_publication(entry)
    ]
    shared_conferences = [
        entry for entry in conferences
        if is_professor_publication(entry)
    ]

    updated_pages = 0
    listed_pages = 0
    listed_articles = 0
    listed_conferences = 0

    print(Fore.CYAN + '\n📚 Student publication check')
    print(Fore.CYAN + '─' * 72)

    for path in sorted(PERSON_DIR.glob('*.rst')):
        if path.resolve() == PROFILE_PATH.resolve():
            continue

        source = path.read_text(encoding='utf-8')
        lines = source.splitlines()
        if not lines:
            continue

        student_name = lines[0].strip()

        articles = [
            entry for entry in shared_articles
            if any(
                is_student_author(path.stem, student_name, author)
                for author in publication_authors(entry)
            )
        ]

        student_conferences = [
            entry for entry in shared_conferences
            if any(
                is_student_author(path.stem, student_name, author)
                for author in publication_authors(entry)
            )
        ]

        if articles or student_conferences:
            print(
                Fore.GREEN
                + '  ✔ {:28s} {:22s}  {} journal, {} conference'.format(
                    path.stem,
                    student_name[:22],
                    len(articles),
                    len(student_conferences),
                )
            )

            listed_pages += 1
            listed_articles += len(articles)
            listed_conferences += len(student_conferences)

            generated = render_student_publications(
                articles,
                student_conferences,
            )
        else:
            print(
                Fore.YELLOW
                + '  - {:28s} {:22s}  no publications'.format(
                    path.stem,
                    student_name[:22],
                )
            )
            generated = ''

        if update_generated_section(
            path,
            STUDENT_ARTICLES_START,
            STUDENT_ARTICLES_END,
            generated,
        ):
            updated_pages += 1

    print(Fore.CYAN + '─' * 72)

    return listed_pages, listed_articles, listed_conferences, updated_pages

def update_publications():
    """Refresh the generated publication section on Gustavo's profile page."""
    books = parse_bibtex(BOOKS_BIB, 'book')
    chapters = parse_bibtex(CHAPTERS_BIB, 'incollection')
    journals = parse_bibtex(JOURNALS_BIB, 'article')
    conferences = parse_bibtex(CONFERENCES_BIB, 'inproceedings')
    generated = render_publications(books, chapters, journals, conferences)
    profile_changed = update_generated_section(
        PROFILE_PATH, PUBLICATIONS_START, PUBLICATIONS_END, generated,
        legacy_start='**publications**:')
    listed_pages, listed_articles, listed_conferences, student_changes = (
        update_student_publications(journals, conferences))
    result = 'Updated' if profile_changed or student_changes else 'Checked'
    print('{} publications: {} books, {} book chapters, {} journal articles and '
          '{} conference papers; coauthorship listed on {} student '
          'profiles ({} journal articles and {} conference papers).'.format(
              result, len(books), len(chapters), len(journals),
              len(conferences), listed_pages, listed_articles,
              listed_conferences))
    return profile_changed or bool(student_changes)


def isdir(path):
    try:
        return S_ISDIR(sftp.stat(path).st_mode)
    except IOError:
        return False


def rm(path):
    """Remove remote directory contents recursively."""
    try:
        files = sftp.listdir(path=path)
    except IOError:
        print(Fore.RED + "⚠️  Remote path not found: " + path)
        return

    if 'html' in files:
        files.remove('html')

    while files != 0:
        if not path.endswith("/"):
            path = "%s/" % path

        if not len(files):
            if path == '/':
                break
            if path != '/html/':
                sftp.rmdir(path)
            return

        for f in files:
            filepath = "%s/%s" % (path, f)
            if isdir(filepath):
                rm(filepath)
            else:
                sftp.remove(filepath)

        files = sftp.listdir(path=path)

    print(Fore.YELLOW + "🧹  Remote directory cleaned: " + Fore.CYAN + path)


def genSite():
    """Generate static site locally with Pelican."""
    update_publications()
    directory = BASE_DIR / 'output'
    if directory.exists():
        shutil.rmtree(directory)
        print(Fore.YELLOW + "🗑️  Removed old local directory: " + Fore.CYAN + str(directory))

    print(Fore.GREEN + "⚙️  Generating Pelican site...")
    status = call([
        sys.executable, '-m', 'pelican',
        str(BASE_DIR / 'content'),
        '-o', str(directory),
        '-s', str(BASE_DIR / 'pelicanconf.py'),
    ])
    if status:
        raise RuntimeError('Pelican site generation failed.')
    print(Fore.GREEN + "✅  Site generation complete.")


def human_size(size):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return '{:.1f} {}'.format(size, unit)
        size /= 1024


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def ensure_remote_dir(path):
    current = ''
    for component in path.strip('/').split('/'):
        current += '/' + component
        try:
            if not S_ISDIR(sftp.stat(current).st_mode):
                raise RuntimeError('Remote upload path is not a directory: ' + current)
        except IOError:
            sftp.mkdir(current)


def remote_inventory(root):
    """Return remote file stats relative to root, excluding no files."""
    inventory = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            contents = sftp.listdir_attr(directory)
        except IOError:
            continue
        for item in contents:
            remote_path = posixpath.join(directory, item.filename)
            if S_ISDIR(item.st_mode):
                pending.append(remote_path)
            else:
                relative = posixpath.relpath(remote_path, root)
                inventory[relative] = item
    return inventory


def load_remote_manifest(root):
    path = posixpath.join(root, REMOTE_MANIFEST)
    try:
        with sftp.open(path, 'rb') as manifest:
            return json.loads(manifest.read().decode('utf-8'))
    except (IOError, ValueError, AttributeError):
        return {}


def write_remote_manifest(root, manifest):
    path = posixpath.join(root, REMOTE_MANIFEST)
    payload = json.dumps(manifest, indent=2, sort_keys=True) + '\n'
    with sftp.open(path, 'wb') as output_file:
        output_file.write(payload.encode('utf-8'))


def prune_remote_files(root, previous, local_relatives):
    """Remove only deployed files tracked by the previous manifest."""
    stale = sorted(set(previous) - local_relatives)
    removed = 0
    failures = []
    for relative in stale:
        try:
            sftp.remove(posixpath.join(root, relative))
            removed += 1
        except IOError as error:
            failures.append((relative, str(error)))
    return removed, failures


def upload(localpath, remotepath, full_upload=False):
    """Synchronize the generated local site to the server over SFTP."""
    local_root = Path(localpath).resolve()
    remote_root = remotepath.rstrip('/')
    ensure_remote_dir(remote_root)

    local_files = sorted(path for path in local_root.rglob('*') if path.is_file())
    local = {
        path.relative_to(local_root).as_posix(): {
            'path': path,
            'size': path.stat().st_size,
            'sha256': file_digest(path),
        }
        for path in local_files
    }
    remote = remote_inventory(remote_root)
    previous = load_remote_manifest(remote_root)
    has_manifest = bool(previous)
    to_upload = []
    reused_by_size = 0

    for relative, metadata in local.items():
        if full_upload:
            to_upload.append(relative)
        elif relative in previous:
            if previous[relative] != metadata['sha256'] or relative not in remote:
                to_upload.append(relative)
        elif (not has_manifest and relative in remote
              and metadata['size'] == remote[relative].st_size
              and metadata['path'].suffix.lower() not in TEXT_SUFFIXES):
            # Bootstrap the manifest from a pre-existing deployment without
            # resending large unchanged document/image/font assets.
            reused_by_size += 1
        else:
            to_upload.append(relative)

    total_bytes = sum(local[relative]['size'] for relative in to_upload)
    print(Fore.BLUE + '🚀  Synchronizing {} files ({} total; {} to transfer, {}).'.format(
        len(local), human_size(sum(item['size'] for item in local.values())),
        len(to_upload), human_size(total_bytes)))
    if reused_by_size:
        print(Fore.CYAN + '    Reusing {} existing binary assets while creating the upload manifest.'.format(
            reused_by_size))

    uploaded_bytes = 0
    for number, relative in enumerate(to_upload, start=1):
        metadata = local[relative]
        remote_file = posixpath.join(remote_root, relative)
        ensure_remote_dir(posixpath.dirname(remote_file))
        prefix = '[{}/{}] {}'.format(number, len(to_upload), relative)

        def progress(transferred, total, prefix=prefix):
            overall = uploaded_bytes + transferred
            print('\r    {}: {} / {}  overall {} / {}'.format(
                prefix, human_size(transferred), human_size(total),
                human_size(overall), human_size(total_bytes)),
                end='', flush=True)

        sftp.put(str(metadata['path']), remote_file, callback=progress, confirm=True)
        uploaded_bytes += metadata['size']
        print()

    # Persist successful synchronization before optional cleanup. Unknown
    # server-managed files are intentionally left untouched.
    manifest = {relative: metadata['sha256'] for relative, metadata in local.items()}
    write_remote_manifest(remote_root, manifest)
    removed, failed_removals = prune_remote_files(remote_root, previous, set(local))
    if failed_removals:
        for relative, _ in failed_removals:
            manifest[relative] = previous[relative]
        write_remote_manifest(remote_root, manifest)
    print(Fore.BLUE + '✅  Synchronization complete: {} uploaded, {} obsolete files removed.'.format(
        human_size(uploaded_bytes), removed))
    for relative, error in failed_removals:
        print(Fore.YELLOW + '⚠️  Could not remove tracked obsolete file {}: {}'.format(
            relative, error))


def deploy(full_upload=False):
    """Generate the site, then upload it to the configured server."""
    os.chdir(BASE_DIR)
    print("")
    print(Style.BRIGHT + Fore.WHITE + "═══════════════════════════════════════════════")
    print(Style.BRIGHT + Fore.CYAN + "🌐  DEPLOY SCRIPT – LABMFA WEBSITE")
    print(Style.BRIGHT + Fore.WHITE + "═══════════════════════════════════════════════")
    start = time.time()

    print("\n" + Fore.YELLOW + "→ Step 1:" + Fore.RESET + " Generating local Pelican site...")
    genSite()

    print("\n" + Fore.YELLOW + "→ Step 2:" + Fore.RESET + " Connecting to server...")
    connect_sftp()
    try:
        print("\n" + Fore.YELLOW + "→ Step 3:" + Fore.RESET + " Synchronizing site on server...")
        upload(BASE_DIR / 'output', REMOTE_SITE_DIR, full_upload=full_upload)
    finally:
        print("\n" + Fore.YELLOW + "→ Step 4:" + Fore.RESET + " Closing SFTP connection...")
        sftp.close()
        transport.close()

    elapsed = time.time() - start
    print("\n" + Style.BRIGHT + Fore.GREEN + "✅  Deployment finished successfully!")
    print(Fore.CYAN + "⏱️  Total time: %.2f seconds" % elapsed)
    print(Style.BRIGHT + Fore.WHITE + "═══════════════════════════════════════════════\n")


def main():
    parser = argparse.ArgumentParser(description='Build and deploy the LabMFA website.')
    parser.add_argument(
        '--update-publications',
        action='store_true',
        help='update the generated profile publication list without deploying',
    )
    parser.add_argument(
        '--full-upload',
        action='store_true',
        help='upload every generated site file instead of synchronizing changed files',
    )
    args = parser.parse_args()

    if args.update_publications:
        update_publications()
    else:
        deploy(full_upload=args.full_upload)


if __name__ == "__main__":
    main()
