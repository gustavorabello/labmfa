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
import subprocess
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
MAIN_PAGE_PATH = BASE_DIR / 'content/category/main.rst'
PERSON_DIR = BASE_DIR / 'content/pages/person'
STUDENTS_PATH = BASE_DIR / 'content/pages/students.rst'
BIB_DIR = Path('/Users/gustavo/projects/misc/latex-personal')
JOURNALS_BIB = BIB_DIR / 'journals.bib'
CONFERENCES_BIB = BIB_DIR / 'papers_conferences.bib'
BOOKS_BIB = BIB_DIR / 'books.bib'
CHAPTERS_BIB = BIB_DIR / 'chapters.bib'
THESIS_CONCLUDED_BIB = BIB_DIR / 'thesisConcluded.bib'
THESIS_NOT_CONCLUDED_BIB = BIB_DIR / 'thesisNotConcluded.bib'
IC_CONCLUDED_BIB = BIB_DIR / 'icConcluded.bib'
IC_NOT_CONCLUDED_BIB = BIB_DIR / 'icNotConcluded.bib'
POSTDOC_CONCLUDED_BIB = BIB_DIR / 'postdocConcluded.bib'
POSTDOC_NOT_CONCLUDED_BIB = BIB_DIR / 'postdocNotConcluded.bib'
UNDERGRAD_BIB = BIB_DIR / 'undergrad.bib'
PUBLICATIONS_START = '.. AUTO-GENERATED PUBLICATIONS START: run build.py --update-publications'
PUBLICATIONS_END = '.. AUTO-GENERATED PUBLICATIONS END'
STUDENT_ARTICLES_START = '.. AUTO-GENERATED COAUTHORED ARTICLES START: run build.py --update-publications'
STUDENT_ARTICLES_END = '.. AUTO-GENERATED COAUTHORED ARTICLES END'
STUDENTS_START = '.. AUTO-GENERATED STUDENTS START: run build.py --update-publications'
STUDENTS_END = '.. AUTO-GENERATED STUDENTS END'
MAIN_NUMBERS_START = '.. AUTO-GENERATED LABMFA NUMBERS START: run build.py --update-publications'
MAIN_NUMBERS_END = '.. AUTO-GENERATED LABMFA NUMBERS END'
GENERIC_PROFILE_MARKER = '.. AUTO-GENERATED GENERIC PROFILE: run build.py --update-publications'
DOCUMENTS_DIR = BASE_DIR / 'content' / 'documents'
LEGACY_DEGREE_WORK_DOCUMENTS_DIR = DOCUMENTS_DIR / 'degree-works'
PROFILE_REQUEST_FROM = 'gustavo.rabello@coppe.ufrj.br'
PROFILE_REQUEST_DRAFT_DIR = Path('/private/tmp/labmfa-profile-email-drafts')
GMAIL_PROFILE_DRAFT_SCRIPT = BASE_DIR / 'scripts/gmail_profile_draft.py'
TEAM_MOSAIC_SCRIPT = BASE_DIR / 'scripts/mosaic_images.py'
REMOTE_SITE_DIR = '/html'
REMOTE_MANIFEST = '.labmfa-manifest.json'
SFTP_TIMEOUT_SECONDS = 60
TEXT_SUFFIXES = {'.css', '.html', '.js', '.json', '.txt', '.xml'}
DEFAULT_PELICAN_BIN = Path('/Users/gustavo/miniforge3/envs/pelican/bin/pelican')
OUTPUT_DIR = BASE_DIR / 'output.nosync'
ICLOUD_CONFLICT_SUFFIX_RE = re.compile(r'^.+ \d+$')

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


def parse_bibtex_entries(path, entry_types=None):
    """Read BibTeX entries without adding a build dependency."""
    source = path.read_text(encoding='utf-8')
    entries = []
    index = 0
    selected = (
        {entry.lower() for entry in entry_types}
        if entry_types is not None else None
    )
    entry_re = re.compile(r'@([A-Za-z]+)\s*\{', re.IGNORECASE)

    while True:
        match = entry_re.search(source, index)
        if not match:
            return entries

        entry_kind = match.group(1).lower()
        body, index = _braced_value(source, match.end() - 1)
        if selected is not None and entry_kind not in selected:
            continue
        try:
            key, fields_text = body.split(',', 1)
        except ValueError as error:
            raise ValueError('Invalid BibTeX entry in {}'.format(path)) from error
        entry = _parse_fields(fields_text)
        entry['_entry_type'] = entry_kind
        entry['_entry_key'] = key.strip()
        entry['_source_path'] = str(path)
        entries.append(entry)


def parse_bibtex(path, entry_type):
    """Read selected BibTeX entries without adding a build dependency."""
    return parse_bibtex_entries(path, {entry_type})


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


def professor_author_name(author):
    tokens = set(name_tokens(author))
    return 'anjos' in tokens and (
        'gustavo' in tokens
        or 'g' in tokens
        or ('gr' in tokens)
        or ('r' in tokens and 'g' in tokens)
    )


def rst_author_name(author, highlight_professor=False,
                    highlight_author=None, highlight_role='prof-author'):
    formatted = author.strip()
    if re.match(r'^[A-Z]\. ', formatted):
        formatted = formatted.replace('. ', r'\. ', 1)
    highlight = (
        highlight_professor and professor_author_name(author)
    ) or (
        highlight_author is not None and highlight_author(author)
    )
    if highlight:
        formatted = ':{}:`{}`'.format(highlight_role, formatted)
    return formatted


def rst_authors(entry, highlight_professor=False, highlight_author=None,
                highlight_role='prof-author'):
    authors = [
        rst_author_name(
            author,
            highlight_professor=highlight_professor,
            highlight_author=highlight_author,
            highlight_role=highlight_role,
        )
        for author in re.split(r'\s+and\s+', field(entry, 'author'))
        if author.strip()
    ]
    joined = '; '.join(authors)
    return joined if joined.endswith('.') else joined + '.'


def author_highlight_block(role_name):
    return [
        '.. role:: {}'.format(role_name),
        '',
        '.. raw:: html',
        '',
        '   <style>',
        '   .{} {{'.format(role_name),
        '     background: rgba(0, 64, 133, 0.16) !important;',
        '     border-radius: 4px;',
        '     color: #004085 !important;',
        '     font-weight: 700 !important;',
        '     padding: 0 0.14rem;',
        '   }',
        '   </style>',
        '',
    ]


def linked_title(entry):
    title = field(entry, 'title')
    doi = field(entry, 'doi')
    url = field(entry, 'url')
    if doi:
        return '`{} <https://doi.org/{}>`_'.format(title, doi)
    if url and not re.search(r'\.pdf(?:$|[?#])', url, flags=re.IGNORECASE):
        return '`{} <{}>`_'.format(title, url)
    return '**{}**'.format(title)


def render_journal(entry, highlight_author=None, highlight_role='prof-author'):
    volume = field(entry, 'volume')
    number = field(entry, 'number')
    pages = field(entry, 'pages') or field(entry, 'article-number')
    issue = '({})'.format(number) if number else ''
    citation = ', vol. {}{}'.format(volume, issue) if volume else ''
    citation += ', {}'.format(pages) if pages else ''
    return '#. {} {}. *{}*{} ({}).'.format(
        rst_authors(
            entry,
            highlight_author=highlight_author,
            highlight_role=highlight_role,
        ),
        linked_title(entry), field(entry, 'journal'), citation,
        field(entry, 'year'))


def render_journal_for_profile(entry):
    return render_journal(
        entry,
        highlight_author=professor_author_name,
        highlight_role='prof-author',
    )


def render_book(entry, highlight_author=None, highlight_role='prof-author'):
    details = [field(entry, 'publisher'), field(entry, 'address')]
    pages = field(entry, 'pages')
    if pages:
        details.append('{} pp.'.format(pages))
    return '#. {} {}. *{}* ({}).'.format(
        rst_authors(
            entry,
            highlight_author=highlight_author,
            highlight_role=highlight_role,
        ), linked_title(entry),
        ', '.join(part for part in details if part), field(entry, 'year'))


def render_book_for_profile(entry):
    return render_book(
        entry,
        highlight_author=professor_author_name,
        highlight_role='prof-author',
    )


def render_chapter(entry, highlight_author=None, highlight_role='prof-author'):
    details = []
    chapter = field(entry, 'chapter')
    pages = field(entry, 'pages')
    if chapter:
        details.append('chap. {}'.format(chapter))
    if pages:
        details.append('pp. {}'.format(pages))
    details.extend([field(entry, 'publisher'), field(entry, 'address')])
    return '#. {} {}. In *{}*, {} ({}).'.format(
        rst_authors(
            entry,
            highlight_author=highlight_author,
            highlight_role=highlight_role,
        ), linked_title(entry), field(entry, 'booktitle'),
        ', '.join(part for part in details if part), field(entry, 'year'))


def render_chapter_for_profile(entry):
    return render_chapter(
        entry,
        highlight_author=professor_author_name,
        highlight_role='prof-author',
    )


def render_conference(entry, highlight_author=None, highlight_role='prof-author'):
    event = field(entry, 'eventtitle')
    address = field(entry, 'address')
    details = ' ({})'.format(event) if event else ''
    details += ', {}'.format(address) if address else ''
    return '#. {} **{}**. *{}*{}, {}.'.format(
        rst_authors(
            entry,
            highlight_author=highlight_author,
            highlight_role=highlight_role,
        ), field(entry, 'title'), field(entry, 'booktitle'),
        details, field(entry, 'year'))


def render_conference_for_profile(entry):
    return render_conference(
        entry,
        highlight_author=professor_author_name,
        highlight_role='prof-author',
    )


def render_publications(books, chapters, journals, conferences):
    lines = [
        PUBLICATIONS_START,
        '',
        '.. role:: prof-author',
        '',
        '.. raw:: html',
        '',
        '   <style>',
        '   .prof-author {',
        '     background: rgba(0, 64, 133, 0.16) !important;',
        '     border-radius: 4px;',
        '     color: #004085 !important;',
        '     font-weight: 700 !important;',
        '     padding: 0 0.14rem;',
        '   }',
        '   </style>',
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
    lines.extend(render_book_for_profile(entry) for entry in books)
    lines.extend([
        '',
        'Book Chapters',
        '~~~~~~~~~~~~~',
        '',
        '.. class:: publications-list chapter-publications',
        '',
    ])
    lines.extend(render_chapter_for_profile(entry) for entry in chapters)
    lines.extend([
        '',
        'Journal Articles',
        '~~~~~~~~~~~~~~~~',
        '',
        '.. class:: publications-list journal-publications',
        '',
    ])
    lines.extend(render_journal_for_profile(entry) for entry in journals)
    lines.extend([
        '',
        'Conference Papers',
        '~~~~~~~~~~~~~~~~~',
        '',
        '.. class:: publications-list conference-publications',
        '',
    ])
    lines.extend(render_conference_for_profile(entry) for entry in conferences)
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

def render_student_publications(articles, conferences, slug, student_name,
                                completed_works=None):
    def highlight_author(author):
        return is_student_author(slug, student_name, author)

    completed_works = completed_works or []
    lines = [
        STUDENT_ARTICLES_START,
        '',
    ]
    if articles or conferences:
        lines.extend(author_highlight_block('profile-author'))
    if completed_works:
        lines.extend(render_student_completed_works(completed_works))
    if articles or conferences:
        if completed_works:
            lines.extend([''])
        lines.extend([
            '**publications with Prof. Gustavo R. Anjos**:',
        ])
    if articles:
        lines.extend([
            '',
            'Journal Articles',
            '~~~~~~~~~~~~~~~~',
            '',
            '.. class:: publications-list journal-publications',
            '',
        ])
        lines.extend(
            render_journal(
                entry,
                highlight_author=highlight_author,
                highlight_role='profile-author',
            )
            for entry in articles
        )
    if conferences:
        lines.extend([
            '',
            'Conference Papers',
            '~~~~~~~~~~~~~~~~~',
            '',
            '.. class:: publications-list conference-publications',
            '',
        ])
        lines.extend(
            render_conference(
                entry,
                highlight_author=highlight_author,
                highlight_role='profile-author',
            )
            for entry in conferences
        )
    lines.extend(['', STUDENT_ARTICLES_END, ''])
    return '\n'.join(lines)


def completed_work_label(category):
    labels = {
        'phd': 'D.Sc. thesis',
        'msc': 'M.Sc. dissertation',
        'ic': 'Undergraduate research work (IC/TCC)',
    }
    return labels.get(category, '')


def completed_work_heading(category):
    headings = {
        'phd': 'D.Sc. thesis',
        'msc': 'M.Sc. dissertation',
        'ic': 'IC/TCC project',
    }
    return headings.get(category, '')


def completed_record_priority(record):
    priority = 0
    if record.get('document_url'):
        priority += 8
    if record.get('file_path'):
        priority += 4

    source_path = record.get('source_path', '')
    if record.get('category') == 'ic' and source_path == str(UNDERGRAD_BIB):
        priority += 3
    elif (
        record.get('category') in {'msc', 'phd'}
        and source_path == str(THESIS_CONCLUDED_BIB)
    ):
        priority += 3

    priority += len(record.get('title', '').strip()) / 1000.0
    return priority


def merge_completed_record_group(records):
    best = max(records, key=completed_record_priority).copy()

    for record in records:
        for key in ('document_url', 'file_path', 'school', 'year', 'title'):
            if not best.get(key) and record.get(key):
                best[key] = record[key]

    return best


def dedupe_completed_records(records):
    grouped = {}
    for record in records:
        key = (
            record.get('slug', ''),
            record.get('category', ''),
            record.get('year', ''),
        )
        grouped.setdefault(key, []).append(record)

    deduped = []
    for key in sorted(grouped):
        group = grouped[key]
        if len(group) == 1:
            deduped.append(group[0])
        else:
            deduped.append(merge_completed_record_group(group))

    return deduped


def prefer_undergrad_tcc_records(records):
    preferred_slugs = {
        record.get('slug', '')
        for record in records
        if (
            record.get('category') == 'ic'
            and record.get('source_path') == str(UNDERGRAD_BIB)
            and record.get('file_path')
        )
    }

    filtered = []
    for record in records:
        if (
            record.get('slug', '') in preferred_slugs
            and record.get('category') == 'ic'
            and record.get('source_path') != str(UNDERGRAD_BIB)
        ):
            continue
        filtered.append(record)
    return filtered


def collect_completed_student_works(alumni_records):
    works_by_slug = {}
    for record in dedupe_completed_records(
        prefer_undergrad_tcc_records(alumni_records)
    ):
        if record['category'] not in {'phd', 'msc', 'ic'}:
            continue
        works_by_slug.setdefault(record['slug'], []).append(record)

    for slug, records in works_by_slug.items():
        works_by_slug[slug] = sorted(records, key=record_sort_key)
    return works_by_slug


def degree_work_suffix(category):
    return {
        'phd': 'dsc',
        'msc': 'msc',
        'ic': 'tcc',
    }.get(category, '')


def publish_degree_work_documents(records, existing_document_urls=None):
    published = {}
    existing_document_urls = existing_document_urls or {}
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    for record in records:
        suffix = degree_work_suffix(record['category'])
        if not suffix:
            continue
        if existing_document_urls.get(record['slug'], {}).get(record['category']):
            continue

        source = record.get('file_path', '').strip()
        if not source:
            continue

        source_path = Path(source).expanduser()
        if not source_path.exists():
            continue

        target_name = '{}-{}.pdf'.format(record['slug'], suffix)
        target_path = DOCUMENTS_DIR / target_name
        shutil.copy2(source_path, target_path)
        published[(record['slug'], record['source_key'])] = (
            '/documents/{}'.format(target_name))

    return published


def cleanup_legacy_degree_work_documents():
    if LEGACY_DEGREE_WORK_DOCUMENTS_DIR.exists():
        shutil.rmtree(LEGACY_DEGREE_WORK_DOCUMENTS_DIR)


def document_degree_info(filename):
    match = re.match(r'(?P<slug>.+)-(?P<kind>msc|dsc)\.pdf$', filename)
    if match:
        return (
            match.group('slug'),
            {'msc': 'msc', 'dsc': 'phd'}[match.group('kind')],
        )

    match = re.match(r'(?P<slug>.+)-tcc(?:-.+)?\.pdf$', filename)
    if match:
        return match.group('slug'), 'ic'

    return '', ''


def profile_slug_for_document(document_slug, profiles):
    if document_slug in profiles:
        return document_slug
    return profile_slug_for_name(slug_to_name(document_slug), profiles)


def infer_completed_work_title_from_profile(source, category):
    compact = ' '.join(source.split())

    if category in {'msc', 'phd'}:
        patterns = [
            r'title of (?:his|her|the) thesis is\s+([^.]+)',
            r'title of (?:his|her|the) dissertation is\s+([^.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, compact, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip(' .')

    project_patterns = [
        r'Project:\s+\*([^*]+)\*',
        r'The project,\s+\*([^*]+)\*',
    ]
    for pattern in project_patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return ''


def infer_completed_work_school_from_profile(source):
    if (
        'Universidade do Estado do Rio de Janeiro' in source
        or '`UERJ`_' in source
    ):
        return 'Universidade do Estado do Rio de Janeiro'
    if (
        'Federal University of Rio de Janeiro' in source
        or '`UFRJ`_' in source
    ):
        return 'Universidade Federal do Rio de Janeiro'
    return ''


def infer_completed_work_year_from_profile(source, category):
    compact = ' '.join(source.split())
    patterns = {
        'msc': [
            r'M\.Sc\.\s*\((\d{4})\)',
            r"master'?s degree.*?(\d{4})",
        ],
        'phd': [
            r'D\.Sc\.\s*\((\d{4})\)',
            r'PhD.*?(\d{4})',
            r'doctor(?:al)? degree.*?(\d{4})',
        ],
        'ic': [],
    }
    for pattern in patterns.get(category, []):
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ''


def collect_existing_document_urls():
    profiles = existing_profile_names()
    urls = {}

    for path in sorted(DOCUMENTS_DIR.glob('*.pdf')):
        document_slug, category = document_degree_info(path.name)
        if not category:
            continue

        profile_slug = profile_slug_for_document(document_slug, profiles)
        if not profile_slug:
            continue

        urls.setdefault(profile_slug, {})
        urls[profile_slug].setdefault(
            category,
            '/documents/{}'.format(path.name),
        )

    return urls


def add_existing_document_works(completed_works_by_slug, document_urls):
    completed_works_by_slug = {
        slug: list(records)
        for slug, records in completed_works_by_slug.items()
    }

    for slug, category_urls in document_urls.items():
        existing_records = completed_works_by_slug.setdefault(slug, [])
        existing_by_category = {}
        for record in existing_records:
            existing_by_category.setdefault(record['category'], []).append(record)

        profile_path = PERSON_DIR / '{}.rst'.format(slug)
        if not profile_path.exists():
            continue

        source = profile_path.read_text(encoding='utf-8')
        student_name = next(
            (line.strip() for line in source.splitlines() if line.strip()),
            slug_to_name(slug),
        )

        for category, url in sorted(category_urls.items()):
            category_records = existing_by_category.get(category, [])
            for record in category_records:
                if not record.get('document_url'):
                    record['document_url'] = url
            if category_records:
                continue

            existing_records.append({
                'name': student_name,
                'title': infer_completed_work_title_from_profile(source, category),
                'year': infer_completed_work_year_from_profile(source, category),
                'school': infer_completed_work_school_from_profile(source),
                'address': '',
                'file_path': '',
                'note': '',
                'category': category,
                'status': 'alumni',
                'entry_type': '',
                'source_key': 'document:{}'.format(url.rsplit('/', 1)[-1]),
                'slug': slug,
                'document_url': url,
            })

        completed_works_by_slug[slug] = sorted(existing_records, key=record_sort_key)

    return completed_works_by_slug


def degree_work_title(record):
    url = record.get('document_url', '')
    title = record.get('title', '').strip()
    if url:
        if not title:
            title = {
                'phd': 'D.Sc. thesis PDF',
                'msc': 'M.Sc. dissertation PDF',
                'ic': 'IC/TCC work PDF',
            }.get(record.get('category', ''), 'Degree work PDF')
        return '`{} <{}>`_'.format(title, url)
    return '*{}*'.format(title)


def render_student_completed_works(records):
    lines = []
    last_category = None
    for record in records:
        if record['category'] != last_category:
            if lines:
                lines.append('')
            lines.extend([
                '**{}**:'.format(completed_work_heading(record['category'])),
                '',
            ])
            last_category = record['category']
        parts = [
            degree_work_title(record),
            completed_work_label(record['category']),
        ]
        if record['school']:
            parts.append(record['school'])
        if record['year']:
            parts.append(record['year'])
        lines.append(' - {}'.format(', '.join(part for part in parts if part)))
    return lines


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


def format_bibtex_person_name(value):
    """Convert the BibTeX 'Family, Given' convention to display order."""
    value = latex_to_text(value).strip()
    if ',' not in value:
        return value

    family, given = [part.strip() for part in value.split(',', 1)]
    return ' '.join(part for part in (given, family) if part)


def student_record(entry, category, status):
    """Normalize a student/advising BibTeX entry for page generation."""
    return {
        'name': format_bibtex_person_name(field(entry, 'author')),
        'title': field(entry, 'title'),
        'year': field(entry, 'year'),
        'school': field(entry, 'school') or field(entry, 'institution'),
        'address': field(entry, 'address'),
        'file_path': entry.get('file', '').strip(),
        'note': field(entry, 'note'),
        'category': category,
        'status': status,
        'entry_type': field(entry, 'type'),
        'source_key': entry.get('_entry_key', ''),
        'source_path': entry.get('_source_path', ''),
    }


def is_anjos_supervision(entry):
    """Keep only records that explicitly list Prof. Gustavo R. Anjos."""
    return 'anjos' in normalize_name(field(entry, 'note'))


def thesis_category(entry):
    thesis_type = field(entry, 'type').lower()
    if thesis_type == 'phdthesis':
        return 'phd'
    if thesis_type == 'masterthesis':
        return 'msc'
    return ''


def load_student_records():
    """Load students and alumni from the advising BibTeX files."""
    current = []
    alumni = []

    for entry in parse_bibtex_entries(THESIS_NOT_CONCLUDED_BIB, {'thesis'}):
        category = thesis_category(entry)
        if category and is_anjos_supervision(entry):
            current.append(student_record(entry, category, 'current'))

    for entry in parse_bibtex_entries(THESIS_CONCLUDED_BIB, {'thesis'}):
        category = thesis_category(entry)
        if category and is_anjos_supervision(entry):
            alumni.append(student_record(entry, category, 'alumni'))

    for entry in parse_bibtex_entries(IC_NOT_CONCLUDED_BIB, {'misc'}):
        if is_anjos_supervision(entry):
            current.append(student_record(entry, 'ic', 'current'))

    for entry in parse_bibtex_entries(IC_CONCLUDED_BIB, {'misc'}):
        if is_anjos_supervision(entry):
            alumni.append(student_record(entry, 'ic', 'alumni'))

    for entry in parse_bibtex_entries(POSTDOC_NOT_CONCLUDED_BIB, {'misc'}):
        if is_anjos_supervision(entry):
            current.append(student_record(entry, 'postdoc', 'current'))

    for entry in parse_bibtex_entries(POSTDOC_CONCLUDED_BIB, {'misc'}):
        if is_anjos_supervision(entry):
            alumni.append(student_record(entry, 'postdoc', 'alumni'))

    return current, alumni


def load_undergrad_completed_records():
    records = []
    for entry in parse_bibtex_entries(UNDERGRAD_BIB, {'thesis'}):
        if not is_anjos_supervision(entry):
            continue
        if field(entry, 'type').lower() != 'bachelorsthesis':
            continue
        records.append(student_record(entry, 'ic', 'alumni'))
    return records


def filter_ic_completed_records(records, allowed_slugs):
    return [
        record for record in records
        if record['slug'] in allowed_slugs
    ]


def existing_profile_names():
    """Return profile display names keyed by slug."""
    profiles = {}
    for path in sorted(PERSON_DIR.glob('*.rst')):
        if path.resolve() == PROFILE_PATH.resolve():
            continue
        source = path.read_text(encoding='utf-8')
        first = next((line.strip() for line in source.splitlines()
                      if line.strip()), '')
        if first:
            profiles[path.stem] = first
    return profiles


def names_compatible(candidate, existing):
    candidate_tokens = set(name_tokens(candidate))
    existing_tokens = set(name_tokens(existing))

    if candidate_tokens == existing_tokens:
        return True
    if len(candidate_tokens) >= 2 and existing_tokens.issubset(candidate_tokens):
        return True
    if len(existing_tokens) >= 2 and candidate_tokens.issubset(existing_tokens):
        return True
    return False


def profile_slug_for_name(name, profiles):
    normalized = normalize_name(name)
    for slug, existing in profiles.items():
        if normalize_name(existing) == normalized:
            return slug

    matches = [
        slug for slug, existing in profiles.items()
        if names_compatible(name, existing)
    ]
    if len(matches) == 1:
        return matches[0]
    return ''


def camel_slug(name, used):
    tokens = name_tokens(name)
    if not tokens:
        tokens = ['student']

    slug = tokens[0] + ''.join(token.capitalize() for token in tokens[1:])
    slug = re.sub(r'[^A-Za-z0-9]', '', slug)
    candidate = slug
    index = 2
    while candidate in used:
        candidate = '{}{}'.format(slug, index)
        index += 1
    used.add(candidate)
    return candidate


def assign_profile_slugs(records):
    profiles = existing_profile_names()
    used = {path.stem for path in PERSON_DIR.glob('*.rst')}

    for record in records:
        slug = profile_slug_for_name(record['name'], profiles)
        if not slug:
            slug = camel_slug(record['name'], used)
            profiles[slug] = record['name']
        record['slug'] = slug


def category_label(category, current=True):
    labels = {
        'phd': ('D.Sc. Student', 'D.Sc.'),
        'msc': ('M.Sc. Student', 'M.Sc.'),
        'ic': ('Undergraduate Scientific Research Student',
               'Undergrad Scientific Research'),
        'postdoc': ('Post-Doctoral Researcher', 'Post-Doc'),
    }
    return labels[category][0 if current else 1]


def sentence_role(category):
    labels = {
        'phd': 'D.Sc. student',
        'msc': 'M.Sc. student',
        'ic': 'undergraduate scientific research student',
        'postdoc': 'post-doctoral researcher',
    }
    return labels[category]


def role_article(category):
    return 'an' if category in {'msc', 'ic'} else 'a'


def generic_profile_affiliation(record):
    if record['category'] == 'ic':
        return {
            'sentence': '`Polytechnic School`_/`UFRJ`_',
            'academic': '`Polytechnic School`_/`Federal University of Rio de Janeiro`_',
            'reference': '.. _Polytechnic School: https://poli.ufrj.br/',
        }
    return {
        'sentence': '`UFRJ`_/`Coppe`_',
        'academic': '`Coppe`_/`Federal University of Rio de Janeiro`_',
        'reference': '.. _Coppe: http://www.coppe.ufrj.br',
    }


def infer_research_interests(title):
    normalized = normalize_name(title)
    checks = [
        ('finite element', ('finite element', 'fem', 'element')),
        ('computational fluid dynamics', ('cfd', 'fluid flow', 'aerodynamic')),
        ('two-phase and multiphase flows', ('two phase', 'multiphase',
                                            'droplet', 'biofuel')),
        ('fluid-structure interaction', ('fluid structure', 'fsi',
                                         'vibration')),
        ('heat transfer', ('heat transfer', 'thermal', 'cooling')),
        ('porous media', ('porosity', 'porous', 'filter')),
        ('aerodynamics', ('aerodynamic', 'airfoil', 'vortex', 'wind')),
        ('optimization', ('optimization', 'calibration')),
        ('numerical methods', ('numerical', 'simulation', 'modelling',
                               'modeling')),
        ('scientific computing', ('python', 'computational', 'simulator')),
    ]
    interests = [
        label for label, keywords in checks
        if any(keyword in normalized for keyword in keywords)
    ]
    if 'numerical methods' not in interests:
        interests.append('numerical methods')
    if 'scientific computing' not in interests:
        interests.append('scientific computing')
    return interests[:6]


def render_generic_profile(record):
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    title = record['name']
    underline = '_' * len(title)
    role = category_label(record['category'], record['status'] == 'current')
    role_in_sentence = sentence_role(record['category'])
    article = role_article(record['category'])
    verb = 'is' if record['status'] == 'current' else 'was'
    project = record['title']
    interests = infer_research_interests(project)
    affiliation = generic_profile_affiliation(record)

    lines = [
        title,
        underline,
        '',
        ':date: {}'.format(now),
        ':modified: {}'.format(now),
        ':slug: person/{}'.format(record['slug']),
        '',
        GENERIC_PROFILE_MARKER,
        '',
        '|',
        '',
        '.. image:: {static}/images/person/generic.jpg',
        '   :name: {}_face'.format(record['slug']),
        '   :width: 25%',
        '   :alt: {}'.format(record['slug']),
        '   :align: left',
        '',
        '{} {} {} {} at {} under the supervision of '
        '`Prof. Gustavo R. Anjos`_. The project, *{}*, is associated with '
        'LabMFA research in computational mechanics, fluid dynamics, heat '
        'transfer, and numerical methods.'.format(
            record['name'],
            verb,
            article,
            role_in_sentence,
            affiliation['sentence'],
            project,
        ),
        '',
        '|',
        '|',
        '|',
        '|',
        '|',
        '',
        '**academic info**:',
        '',
        ' - {} at {}'.format(role, affiliation['academic']),
        ' - `Department of Mechanical Engineering`_',
        ' - Project: *{}*'.format(project),
        ' - Year: {}'.format(record['year']),
        ' - Advisor: `Prof. Gustavo R. Anjos`_',
        '',
        '|',
        '',
        '**research interests**:',
        '',
    ]
    lines.extend(' - {}'.format(interest) for interest in interests)
    lines.extend([
        '',
        '.. Place your references here',
        '.. _Prof. Gustavo R. Anjos: /person/gustavoRabello',
        '.. _UFRJ: http://www.ufrj.br',
        '.. _Federal University of Rio de Janeiro: http://www.ufrj.br',
        '.. _Department of Mechanical Engineering: http://www.mecanica.ufrj.br/index.php/en/',
        affiliation['reference'],
        '',
    ])
    return '\n'.join(lines)


def ensure_missing_student_profiles(records):
    created = []
    refreshed = 0
    for record in records:
        path = PERSON_DIR / '{}.rst'.format(record['slug'])
        rendered = render_generic_profile(record)
        if path.exists():
            source = path.read_text(encoding='utf-8')
            if is_managed_generic_profile(source) and source != rendered:
                path.write_text(rendered, encoding='utf-8')
                refreshed += 1
            continue
        path.write_text(rendered, encoding='utf-8')
        created.append((record, path))
    return created, refreshed


def is_managed_generic_profile(source):
    return (
        GENERIC_PROFILE_MARKER in source
        or (
            '.. image:: {static}/images/person/generic.jpg' in source
            and 'LabMFA research in computational mechanics, fluid dynamics, '
                'heat transfer, and numerical methods.' in source
            and ' - Advisor: `Prof. Gustavo R. Anjos`_' in source
            and '.. Place your references here' in source
        )
    )


def profile_request_email_subject():
    return 'Informações para seu perfil no site do LabMFA'


def render_profile_request_email_body(record, path):
    role = category_label(record['category'], record['status'] == 'current')
    return '\n'.join([
        'Prezado(a) {},'.format(record['name']),
        '',
        'Estou atualizando sua página de perfil no site do LabMFA e criei',
        'uma versão preliminar usando o modelo genérico do laboratório.',
        '',
        'Você poderia, por favor, preencher o arquivo em anexo com as',
        'informações abaixo para que eu possa substituir o texto temporário',
        'pelo seu perfil atualizado?',
        '',
        '- Um parágrafo curto de biografia em inglês',
        '- Informações acadêmicas: programa/cargo, instituição, departamento,',
        '  orientador/coorientadores, CV Lattes, ORCID, e-mail e telefone,',
        '  caso queira publicar',
        '- Interesses de pesquisa, preferencialmente como 4 a 8 palavras-chave',
        '- Uma foto de perfil, caso queira substituir a imagem genérica em',
        'formato JPG.',
        '- Links que queira incluir, como página pessoal, GitHub, LinkedIn,',
        '  Google Scholar ou página de projeto',
        '',
        'Informações atualmente registradas no LabMFA:',
        '- Nome: {}'.format(record['name']),
        '- Vínculo: {}'.format(role),
        '- Projeto/título: {}'.format(record['title']),
        '- Ano: {}'.format(record['year']),
        '',
        'Atenciosamente,',
        'Gustavo',
    ])


def render_profile_request_email(record, path):
    return '\n'.join([
        'De: {}'.format(PROFILE_REQUEST_FROM),
        'Assunto: {}'.format(profile_request_email_subject()),
        '',
        render_profile_request_email_body(record, path),
    ])


def write_gmail_draft_payload(record, path):
    PROFILE_REQUEST_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    payload_path = PROFILE_REQUEST_DRAFT_DIR / '{}-gmail-draft.json'.format(
        record['slug'])
    payload = {
        'from': PROFILE_REQUEST_FROM,
        'subject': profile_request_email_subject(),
        'body': render_profile_request_email_body(record, path),
        'attachments': [str(path)],
    }
    payload_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )
    return payload_path


def gmail_credentials_path():
    return Path(os.environ.get(
        'LABMFA_GMAIL_CREDENTIALS',
        str(Path.home() / '.config/labmfa/gmail-credentials.json'),
    )).expanduser()


def create_gmail_profile_draft(payload_path):
    credentials = gmail_credentials_path()
    if not credentials.exists():
        return (
            False,
            'Gmail OAuth credentials not found: {}'.format(credentials),
        )

    if not GMAIL_PROFILE_DRAFT_SCRIPT.exists():
        return (
            False,
            'Gmail draft script not found: {}'.format(
                GMAIL_PROFILE_DRAFT_SCRIPT),
        )

    result = subprocess.run(
        [
            sys.executable,
            str(GMAIL_PROFILE_DRAFT_SCRIPT),
            '--payload',
            str(payload_path),
        ],
        cwd=str(BASE_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode == 0, result.stdout.strip()


def print_profile_request_emails(created_profiles):
    if not created_profiles:
        return

    print(Fore.CYAN + '\n✉️  Gmail API/profile drafts for new generic profiles, grouped by student')
    print(Fore.CYAN + '─' * 72)
    for index, (record, path) in enumerate(created_profiles, start=1):
        if index > 1:
            print(Fore.CYAN + '─' * 72)
        gmail_payload_path = write_gmail_draft_payload(record, path.resolve())
        gmail_ok, gmail_output = create_gmail_profile_draft(gmail_payload_path)
        print(Fore.RED + Style.BRIGHT + 'Student: {}'.format(record['name']))
        print(Fore.WHITE + 'Profile RST: {}'.format(path.resolve()))
        print(Fore.WHITE + 'Gmail API payload: {}'.format(
            gmail_payload_path.resolve()))
        if gmail_ok:
            print(Fore.GREEN + 'Gmail API draft: {}'.format(gmail_output))
        else:
            print(Fore.YELLOW + 'Gmail API draft skipped: {}'.format(
                gmail_output))
            print(Fore.YELLOW + 'Create credentials following Google Gmail API '
                  'Desktop OAuth setup, then save them as {}'.format(
                      gmail_credentials_path()))
    print(Fore.CYAN + '─' * 72)


def record_sort_key(record):
    year = int(record['year']) if record['year'].isdigit() else 0
    return (-year, normalize_name(record['name']))


def render_student_record(record, current=True):
    lines = [
        ' `{}`_ --'.format(record['name']),
        '  *{}*,'.format(record['title']),
        '  {},'.format(category_label(record['category'], current)),
        '  {}'.format(record['year']),
        '',
    ]
    return lines


def render_student_group(records, current=True):
    lines = []
    for record in sorted(records, key=record_sort_key):
        lines.extend(render_student_record(record, current=current))
    return lines


def render_alumni(records):
    grouped = {}
    for record in records:
        grouped.setdefault(record['slug'], []).append(record)

    groups = sorted(
        grouped.values(),
        key=lambda items: (
            -max(int(item['year']) if item['year'].isdigit() else 0
                 for item in items),
            normalize_name(items[0]['name']),
        ),
    )

    lines = []
    for items in groups:
        first = sorted(items, key=record_sort_key)[0]
        lines.append(' `{}`_ --'.format(first['name']))
        for item in sorted(items, key=record_sort_key):
            lines.extend([
                '  *{}*,'.format(item['title']),
                '  {},'.format(category_label(item['category'], current=False)),
                '  {}'.format(item['year']),
                '',
            ])
    return lines


def render_students_page(current, alumni):
    active_slugs = {record['slug'] for record in current}
    alumni = [
        record for record in alumni
        if record['slug'] not in active_slugs
    ]

    sections = [
        ('Post-Doctoral Researchers', 'postdoc'),
        ('D.Sc. Students', 'phd'),
        ('M.Sc. Students', 'msc'),
        ('Undergrad Scientific Research - IC', 'ic'),
    ]

    lines = [
        STUDENTS_START,
        '',
    ]
    for heading, category in sections:
        records = [
            record for record in current
            if record['category'] == category
        ]
        if not records:
            continue
        lines.extend([
            heading,
            '_' * len(heading),
            '',
        ])
        lines.extend(render_student_group(records, current=True))

    if alumni:
        lines.extend([
            'Alumni',
            '_' * len('Alumni'),
            '',
        ])
        lines.extend(render_alumni(alumni))

    all_records = sorted(
        {record['slug']: record for record in current + alumni}.values(),
        key=lambda record: normalize_name(record['name']),
    )
    lines.extend([
        '.. Place your references here',
    ])
    lines.extend(
        '.. _{}: /person/{}'.format(record['name'], record['slug'])
        for record in all_records
    )
    lines.extend(['', STUDENTS_END, ''])
    return '\n'.join(lines)


def update_students_page(current, alumni):
    generated = render_students_page(current, alumni)
    source = STUDENTS_PATH.read_text(encoding='utf-8')
    if STUDENTS_START in source and STUDENTS_END in source:
        before = source.split(STUDENTS_START, 1)[0]
        after = source.split(STUDENTS_END, 1)[1].lstrip('\n')
        updated = before.rstrip() + '\n\n' + generated + '\n' + after
    else:
        match = re.search(r'(?ms)^:slug:\s*students\s*\n+', source)
        if not match:
            raise RuntimeError('Could not find students page metadata block.')
        before = source[:match.end()]
        updated = before.rstrip() + '\n\n' + generated

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    updated = re.sub(r'(?m)^:modified:.*$',
                     ':modified: {}'.format(timestamp), updated, count=1)
    if updated == source:
        return False
    STUDENTS_PATH.write_text(updated, encoding='utf-8')
    return True


def update_students_from_bibs():
    current, alumni = load_student_records()
    records = current + alumni
    assign_profile_slugs(records)
    created, refreshed = ensure_missing_student_profiles(records)
    changed = update_students_page(current, alumni)
    return current, alumni, created, refreshed, changed


def student_profile_slugs():
    """Return all profile slugs in content/pages/person, except Gustavo's page."""
    return {
        path.stem
        for path in sorted(PERSON_DIR.glob('*.rst'))
        if path.resolve() != PROFILE_PATH.resolve()
    }


def publication_identity(entry):
    return (entry.get('_source_path', ''), entry.get('_entry_key', ''))


def match_student_publications(slug, student_name, articles, conferences):
    matched_articles = [
        entry for entry in articles
        if any(
            is_student_author(slug, student_name, author)
            for author in publication_authors(entry)
        )
    ]
    matched_conferences = [
        entry for entry in conferences
        if any(
            is_student_author(slug, student_name, author)
            for author in publication_authors(entry)
        )
    ]
    return matched_articles, matched_conferences


def current_and_alumni_records(current, alumni):
    current_by_slug = {}
    for record in current:
        current_by_slug.setdefault(record['slug'], record)

    alumni_by_slug = {}
    for record in alumni:
        if record['slug'] in current_by_slug:
            continue
        alumni_by_slug.setdefault(record['slug'], record)

    return current_by_slug, alumni_by_slug


def collect_student_publication_stats(current, alumni, journals, conferences):
    shared_articles = [
        entry for entry in journals
        if is_professor_publication(entry)
    ]
    shared_conferences = [
        entry for entry in conferences
        if is_professor_publication(entry)
    ]

    current_by_slug, alumni_by_slug = current_and_alumni_records(current, alumni)
    all_records = {}
    all_records.update(current_by_slug)
    all_records.update(alumni_by_slug)

    unique_journals = set()
    unique_conferences = set()
    current_with_publications = 0
    alumni_with_publications = 0
    total_profile_links = 0

    for slug, record in sorted(all_records.items()):
        matched_articles, matched_conferences = match_student_publications(
            slug,
            record['name'],
            shared_articles,
            shared_conferences,
        )
        has_publications = bool(matched_articles or matched_conferences)
        if not has_publications:
            continue

        total_profile_links += len(matched_articles) + len(matched_conferences)
        unique_journals.update(
            publication_identity(entry) for entry in matched_articles)
        unique_conferences.update(
            publication_identity(entry) for entry in matched_conferences)
        if slug in current_by_slug:
            current_with_publications += 1
        else:
            alumni_with_publications += 1

    return {
        'current_count': len(current_by_slug),
        'alumni_count': len(alumni_by_slug),
        'current_with_publications': current_with_publications,
        'alumni_with_publications': alumni_with_publications,
        'profiles_with_publications': (
            current_with_publications + alumni_with_publications),
        'unique_journal_count': len(unique_journals),
        'unique_conference_count': len(unique_conferences),
        'total_profile_links': total_profile_links,
    }


def render_main_page_numbers(stats):
    lines = [
        MAIN_NUMBERS_START,
        '',
        '* **{}** current students and postdoctoral researchers supervised in LabMFA'.format(
            stats['current_count']),
        '* **{}** alumni from LabMFA supervision already listed on the site'.format(
            stats['alumni_count']),
        '* **{}** current student and postdoctoral profiles and **{}** alumni profiles with at least one coauthored publication listed'.format(
            stats['current_with_publications'],
            stats['alumni_with_publications']),
        '* **{}** journal articles and **{}** conference papers with student or postdoctoral coauthors'.format(
            stats['unique_journal_count'],
            stats['unique_conference_count']),
        '',
        MAIN_NUMBERS_END,
        '',
    ]
    return '\n'.join(lines)


def update_main_page_numbers(stats):
    generated = render_main_page_numbers(stats)
    return update_generated_section(
        MAIN_PAGE_PATH,
        MAIN_NUMBERS_START,
        MAIN_NUMBERS_END,
        generated,
    )

def update_student_publications(journals, conferences, completed_works_by_slug=None):
    """Publish article and conference coauthorship on all student profile pages."""
    completed_works_by_slug = completed_works_by_slug or {}
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

        student_name = next((line.strip() for line in lines if line.strip()), '')
        if not student_name:
            continue

        articles, student_conferences = match_student_publications(
            path.stem,
            student_name,
            shared_articles,
            shared_conferences,
        )
        completed_works = completed_works_by_slug.get(path.stem, [])

        if articles or student_conferences or completed_works:
            print(
                Fore.GREEN
                + '  ✔ {:28s} {:22s}  {} journal, {} conference, {} works'.format(
                    path.stem,
                    student_name[:22],
                    len(articles),
                    len(student_conferences),
                    len(completed_works),
                )
            )

            if articles or student_conferences:
                listed_pages += 1
            listed_articles += len(articles)
            listed_conferences += len(student_conferences)

            generated = render_student_publications(
                articles,
                student_conferences,
                path.stem,
                student_name,
                completed_works,
            )
        else:
            print(
                Fore.YELLOW
                + '  - {:28s} {:22s}  no publications or works'.format(
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
    current_students, alumni_students, created_profiles, refreshed_profiles, students_changed = (
        update_students_from_bibs())
    student_page_slugs = {record['slug'] for record in current_students + alumni_students}
    undergrad_completed_records = load_undergrad_completed_records()
    assign_profile_slugs(undergrad_completed_records)
    undergrad_completed_records = filter_ic_completed_records(
        undergrad_completed_records,
        student_page_slugs,
    )
    cleanup_legacy_degree_work_documents()
    existing_document_urls = collect_existing_document_urls()
    for slug in list(existing_document_urls):
        category_urls = existing_document_urls[slug]
        if slug not in student_page_slugs:
            category_urls.pop('ic', None)
        if not category_urls:
            existing_document_urls.pop(slug, None)
    completed_records = alumni_students + undergrad_completed_records
    published_degree_work_documents = publish_degree_work_documents(
        completed_records,
        existing_document_urls=existing_document_urls,
    )
    for record in completed_records:
        record['document_url'] = published_degree_work_documents.get(
            (record['slug'], record['source_key']),
            existing_document_urls.get(record['slug'], {}).get(record['category'], ''),
        )
    books = parse_bibtex(BOOKS_BIB, 'book')
    chapters = parse_bibtex(CHAPTERS_BIB, 'incollection')
    journals = parse_bibtex(JOURNALS_BIB, 'article')
    conferences = parse_bibtex(CONFERENCES_BIB, 'inproceedings')
    generated = render_publications(books, chapters, journals, conferences)
    profile_changed = update_generated_section(
        PROFILE_PATH, PUBLICATIONS_START, PUBLICATIONS_END, generated,
        legacy_start='**publications**:')
    completed_works_by_slug = add_existing_document_works(
        collect_completed_student_works(completed_records),
        existing_document_urls,
    )
    main_page_numbers = collect_student_publication_stats(
        current_students,
        alumni_students,
        journals,
        conferences,
    )
    main_page_changed = update_main_page_numbers(main_page_numbers)
    listed_pages, listed_articles, listed_conferences, student_changes = (
        update_student_publications(
            journals,
            conferences,
            completed_works_by_slug=completed_works_by_slug,
        ))
    result = (
        'Updated'
        if (
            profile_changed or main_page_changed or student_changes
            or students_changed or created_profiles or refreshed_profiles
        )
        else 'Checked'
    )
    print('{} publications: {} books, {} book chapters, {} journal articles and '
          '{} conference papers; coauthorship listed on {} student '
          'profiles ({} journal articles and {} conference papers). '
          'Students page has {} current records and {} alumni records; '
          '{} generic profiles created and {} refreshed.'.format(
              result, len(books), len(chapters), len(journals),
              len(conferences), listed_pages, listed_articles,
              listed_conferences, len(current_students), len(alumni_students),
              len(created_profiles), refreshed_profiles))
    if created_profiles:
        print(Fore.CYAN + 'Created generic profiles: {}'.format(
            ', '.join(sorted(path.stem for _, path in created_profiles))))
        print_profile_request_emails(created_profiles)
    return (
        profile_changed or main_page_changed or bool(student_changes)
        or students_changed or bool(created_profiles) or bool(refreshed_profiles)
    )


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
    print(Fore.GREEN + "🧩  Updating homepage mosaic...")
    subprocess.run(
        [sys.executable, str(TEAM_MOSAIC_SCRIPT)],
        cwd=str(BASE_DIR),
        check=True,
    )
    directory = OUTPUT_DIR
    previous_snapshot = (
        collect_directory_snapshot(directory)
        if directory.exists() else None
    )
    if directory.exists():
        shutil.rmtree(directory)
        print(Fore.YELLOW + "🗑️  Removed old local directory: " + Fore.CYAN + str(directory))

    print(Fore.GREEN + "⚙️  Generating Pelican site...")
    pelican_cmd = [
        os.environ.get('LABMFA_PELICAN_BIN', str(DEFAULT_PELICAN_BIN))
    ]
    if not Path(pelican_cmd[0]).exists():
        pelican_cmd = [sys.executable, '-m', 'pelican']

    status = call(pelican_cmd + [
        str(BASE_DIR / 'content'),
        '-o', str(directory),
        '-s', str(BASE_DIR / 'pelicanconf.py'),
    ])
    if status:
        raise RuntimeError('Pelican site generation failed.')
    remove_icloud_conflicts(directory)
    print(Fore.GREEN + "✅  Site generation complete.")
    print_directory_stats(directory, previous_snapshot)


def human_size(size):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return '{:.1f} {}'.format(size, unit)
        size /= 1024


def collect_directory_stats(root):
    files = 0
    directories = 0
    total_size = 0
    suffix_counts = {}
    largest = []

    for path in root.rglob('*'):
        if path.is_dir():
            directories += 1
            continue
        if not path.is_file():
            continue

        size = path.stat().st_size
        files += 1
        total_size += size
        suffix = path.suffix.lower() or '[no ext]'
        suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
        largest.append((size, path.relative_to(root)))

    largest.sort(reverse=True)
    top_suffixes = sorted(
        suffix_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[:5]

    return {
        'files': files,
        'directories': directories,
        'total_size': total_size,
        'top_suffixes': top_suffixes,
        'largest': largest[:5],
    }


def collect_directory_snapshot(root):
    files = {}
    directories = set()

    for path in root.rglob('*'):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            directories.add(relative)
            continue
        if not path.is_file():
            continue
        files[relative] = {
            'size': path.stat().st_size,
            'sha256': file_digest(path),
        }

    return {
        'files': files,
        'directories': directories,
    }


def compare_directory_snapshots(previous, current):
    previous_files = previous['files'] if previous else {}
    previous_directories = previous['directories'] if previous else set()
    current_files = current['files']
    current_directories = current['directories']

    new_files = sorted(set(current_files) - set(previous_files))
    removed_files = sorted(set(previous_files) - set(current_files))
    modified_files = sorted(
        relative for relative in set(current_files).intersection(previous_files)
        if current_files[relative]['sha256'] != previous_files[relative]['sha256']
    )
    new_directories = sorted(current_directories - previous_directories)
    removed_directories = sorted(previous_directories - current_directories)

    return {
        'new_files': new_files,
        'modified_files': modified_files,
        'removed_files': removed_files,
        'new_directories': new_directories,
        'removed_directories': removed_directories,
    }


def print_path_list(label, paths):
    if not paths:
        return
    print('{} ({}):'.format(label, len(paths)))
    for relative in paths:
        print('  - {}'.format(relative))


def print_directory_stats(root, previous_snapshot=None):
    stats = collect_directory_stats(root)
    current_snapshot = collect_directory_snapshot(root)
    changes = compare_directory_snapshots(previous_snapshot, current_snapshot)
    print(Fore.CYAN + '\n📊 Generated site stats')
    print(Fore.CYAN + '─' * 72)
    print(
        'Output: {} directories, {} files, total size {}'.format(
            stats['directories'],
            stats['files'],
            human_size(stats['total_size']),
        )
    )
    if stats['top_suffixes']:
        print('Most common file types: {}'.format(
            ', '.join(
                '{} ({})'.format(suffix, count)
                for suffix, count in stats['top_suffixes']
            )
        ))
    if stats['largest']:
        print('Largest files:')
        for size, relative in stats['largest']:
            print('  - {} ({})'.format(relative, human_size(size)))
    if previous_snapshot is not None:
        print('Changed since previous local build:')
        print('  New files: {}, modified files: {}, removed files: {}, new directories: {}, removed directories: {}'.format(
            len(changes['new_files']),
            len(changes['modified_files']),
            len(changes['removed_files']),
            len(changes['new_directories']),
            len(changes['removed_directories']),
        ))
        print_path_list('New files', changes['new_files'])
        print_path_list('Modified files', changes['modified_files'])
        print_path_list('Removed files', changes['removed_files'])
        print_path_list('New directories', changes['new_directories'])
        print_path_list('Removed directories', changes['removed_directories'])


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def is_icloud_conflict_path(path):
    return any(
        ICLOUD_CONFLICT_SUFFIX_RE.match(component)
        for component in path.parts
    )


def remove_icloud_conflicts(root):
    root = Path(root)
    if not root.exists():
        return []

    conflicts = sorted(
        (
            path for path in root.rglob('*')
            if is_icloud_conflict_path(path.relative_to(root))
        ),
        key=lambda path: len(path.relative_to(root).parts),
        reverse=True,
    )
    removed = []
    removed_roots = set()
    for path in conflicts:
        if any(parent in removed_roots for parent in path.parents):
            continue
        if not path.exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
            removed_roots.add(path)
        else:
            path.unlink()
        removed.append(path.relative_to(root).as_posix())

    if removed:
        print(Fore.YELLOW + '🧹  Removed {} iCloud conflict paths from {}:'.format(
            len(removed), root))
        for relative in removed:
            print(Fore.YELLOW + '    - {}'.format(relative))
    return removed


def remote_file_digest(path):
    digest = hashlib.sha256()
    with sftp.open(path, 'rb') as input_file:
        for block in iter(lambda: input_file.read(1024 * 1024), b''):
            if not block:
                break
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
    source_root = Path(localpath).resolve()
    remote_root = remotepath.rstrip('/')
    ensure_remote_dir(remote_root)

    remove_icloud_conflicts(source_root)
    local_root = source_root
    print(Fore.CYAN + '📦  Upload source: {}'.format(local_root))

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
    reused_by_digest = 0

    for relative, metadata in local.items():
        if full_upload:
            to_upload.append(relative)
        elif relative in previous:
            if previous[relative] != metadata['sha256'] or relative not in remote:
                to_upload.append(relative)
        elif not has_manifest and relative in remote:
            remote_file = posixpath.join(remote_root, relative)
            if metadata['size'] != remote[relative].st_size:
                to_upload.append(relative)
            elif remote_file_digest(remote_file) != metadata['sha256']:
                to_upload.append(relative)
            else:
                reused_by_digest += 1
        else:
            to_upload.append(relative)

    total_bytes = sum(local[relative]['size'] for relative in to_upload)
    print(Fore.BLUE + '🚀  Synchronizing {} files ({} total; {} to transfer, {}).'.format(
        len(local), human_size(sum(item['size'] for item in local.values())),
        len(to_upload), human_size(total_bytes)))
    if reused_by_digest:
        print(Fore.CYAN + '    Reusing {} existing server files after checksum verification while creating the upload manifest.'.format(
            reused_by_digest))

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
        upload(OUTPUT_DIR, REMOTE_SITE_DIR, full_upload=full_upload)
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
