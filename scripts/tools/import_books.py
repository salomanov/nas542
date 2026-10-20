#!/opt/bin/python3
"""Import books dropped into the inbox into the Calibre library used by COPS.

Usage:
    import_books.py [--watch SECONDS] [--dry-run] [ROOT]

ROOT defaults to /i-data/45f1aca1/Apps/calibre
Inbox:  ROOT/inbox   (drop epub, fb2, pdf, mobi, azw3, djvu here)
DB:     ROOT/metadata.db  (Calibre schema, read by COPS)

Supported metadata: EPUB (full), FB2 (full), everything else (title from
the file name, author "Unknown").

No third-party modules: only the Python standard library.
"""

import base64
import os
import posixpath
import re
import shutil
import sqlite3
import struct
import sys
import time
import uuid
import zipfile
import zlib
import xml.etree.ElementTree as ET
from urllib.parse import unquote

DEFAULT_ROOT = '/i-data/45f1aca1/Apps/calibre'
FORMATS = {
    '.epub': 'EPUB',
    '.fb2': 'FB2',
    '.pdf': 'PDF',
    '.mobi': 'MOBI',
    '.azw3': 'AZW3',
    '.djvu': 'DJVU',
}

LANG3 = {
    'en': 'eng', 'ru': 'rus', 'uk': 'ukr', 'be': 'bel', 'de': 'deu',
    'fr': 'fra', 'es': 'spa', 'it': 'ita', 'pl': 'pol', 'cs': 'ces',
    'nl': 'nld', 'pt': 'por', 'sv': 'swe', 'tr': 'tur', 'ja': 'jpn',
    'zh': 'zho', 'ko': 'kor', 'ar': 'ara', 'he': 'heb', 'la': 'lat',
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS library_id (id INTEGER PRIMARY KEY, uuid TEXT NOT NULL, UNIQUE(uuid));
CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL DEFAULT 'Unknown' COLLATE NOCASE,
  sort TEXT COLLATE NOCASE, timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pubdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, series_index REAL NOT NULL DEFAULT 1.0,
  author_sort TEXT COLLATE NOCASE, isbn TEXT DEFAULT "" COLLATE NOCASE, lccn TEXT DEFAULT "" COLLATE NOCASE,
  path TEXT NOT NULL DEFAULT "", flags INTEGER NOT NULL DEFAULT 1, uuid TEXT, has_cover BOOL DEFAULT 0,
  last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE,
  sort TEXT COLLATE NOCASE, link TEXT NOT NULL DEFAULT "");
CREATE TABLE IF NOT EXISTS books_authors_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, author INTEGER NOT NULL, UNIQUE(book, author));
CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, format TEXT NOT NULL COLLATE NOCASE,
  uncompressed_size INTEGER NOT NULL, name TEXT NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS data_book_format ON data (book, format);
CREATE TABLE IF NOT EXISTS series (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE, sort TEXT COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS books_series_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, series INTEGER NOT NULL, UNIQUE(book, series));
CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE, sort TEXT COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS books_tags_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, tag INTEGER NOT NULL, UNIQUE(book, tag));
CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, text TEXT NOT NULL COLLATE NOCASE, UNIQUE(book));
CREATE TABLE IF NOT EXISTS publishers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE, sort TEXT COLLATE NOCASE);
CREATE TABLE IF NOT EXISTS books_publishers_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, publisher INTEGER NOT NULL, UNIQUE(book));
CREATE TABLE IF NOT EXISTS languages (id INTEGER PRIMARY KEY AUTOINCREMENT, lang_code TEXT NOT NULL COLLATE NOCASE, UNIQUE(lang_code));
CREATE TABLE IF NOT EXISTS books_languages_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, lang_code INTEGER NOT NULL,
  item_order INTEGER NOT NULL DEFAULT 0, link TEXT NOT NULL DEFAULT "", UNIQUE(book, lang_code));
CREATE TABLE IF NOT EXISTS identifiers (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL DEFAULT 'isbn' COLLATE NOCASE,
  value TEXT NOT NULL COLLATE NOCASE, UNIQUE(type, value));
CREATE TABLE IF NOT EXISTS books_identifiers_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, identifier INTEGER NOT NULL, UNIQUE(book, identifier));
CREATE TABLE IF NOT EXISTS ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, rating INTEGER CHECK(rating > -1 AND rating < 11), link TEXT NOT NULL DEFAULT "");
CREATE TABLE IF NOT EXISTS books_ratings_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, rating INTEGER NOT NULL, UNIQUE(book, rating));
"""


def log(msg):
    print('%s %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg), flush=True)


def local(tag):
    return tag.rsplit('}', 1)[-1].lower()


def clean_text(s):
    if not s:
        return ''
    s = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', s, flags=re.I | re.S)
    s = re.sub(r'<br\s*/?>', '\n', s, flags=re.I)
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\s+', ' ', s).strip()


def safe_name(s, maxlen=90):
    s = clean_text(s)
    s = re.sub(r'[\\/:*?"<>|\x00-\x1f]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip(' .')
    return (s[:maxlen].strip() or 'Unknown')


def author_sort(name):
    parts = name.split()
    if len(parts) >= 2:
        return '%s, %s' % (parts[-1], ' '.join(parts[:-1]))
    return name


def epub_meta(path):
    meta = {}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        container = z.read('META-INF/container.xml')
        croot = ET.fromstring(container)
        opf_path = None
        for el in croot.iter():
            if local(el.tag) == 'rootfile':
                opf_path = el.get('full-path')
                break
        if not opf_path or opf_path not in names:
            raise ValueError('no OPF in EPUB')

        root = ET.fromstring(z.read(opf_path))
        opf_dir = posixpath.dirname(opf_path)

        def texts(tag):
            out = []
            for el in root.iter():
                if local(el.tag) == tag and (el.text or '').strip():
                    out.append(el.text.strip())
            return out

        meta['title'] = (texts('title') or [''])[0]
        meta['authors'] = texts('creator') or []
        meta['language'] = (texts('language') or [''])[0]
        meta['publisher'] = (texts('publisher') or [''])[0]
        meta['date'] = (texts('date') or [''])[0]
        meta['subjects'] = texts('subject')
        meta['description'] = (texts('description') or [''])[0]
        meta['identifiers'] = texts('identifier')

        items = [el for el in root.iter() if local(el.tag) == 'item']
        cover_item = None
        cover_id = None
        series_name = ''
        series_index = None

        for el in root.iter():
            if local(el.tag) != 'meta':
                continue
            name = (el.get('name') or '').lower()
            prop = (el.get('property') or '').lower()
            content = el.get('content') or (el.text or '').strip()
            if name == 'cover':
                cover_id = content
            elif name == 'calibre:series':
                series_name = content
            elif name == 'calibre:series_index':
                series_index = content
            elif prop == 'belongs-to-collection':
                series_name = series_name or content
            elif prop == 'group-position':
                series_index = series_index or content

        for it in items:
            props = (it.get('properties') or '').lower()
            if 'cover-image' in props:
                cover_item = it
                break
        if cover_item is None and cover_id:
            for it in items:
                if it.get('id') == cover_id:
                    cover_item = it
                    break

        if cover_item is not None:
            href = unquote(cover_item.get('href') or '')
            cover_path = posixpath.normpath(posixpath.join(opf_dir, href)) if opf_dir else href
            if cover_path in names:
                meta['cover'] = z.read(cover_path)

        meta['series'] = series_name
        meta['series_index'] = series_index
    return meta


def fb2_meta(path):
    meta = {'authors': [], 'subjects': [], 'identifiers': []}
    root = ET.parse(path).getroot()

    def texts(tag):
        return [el.text.strip() for el in root.iter()
                if local(el.tag) == tag and (el.text or '').strip()]

    meta['title'] = (texts('book-title') or [''])[0]
    for el in root.iter():
        if local(el.tag) != 'author':
            continue
        parts = []
        for child in el:
            if local(child.tag) in ('first-name', 'middle-name', 'last-name', 'nickname'):
                if (child.text or '').strip():
                    parts.append(child.text.strip())
        if parts:
            meta['authors'].append(' '.join(parts))
    meta['language'] = (texts('lang') or [''])[0]
    meta['publisher'] = (texts('publisher') or [''])[0]
    meta['date'] = (texts('date') or [''])[0]
    meta['description'] = (texts('annotation') or [''])[0]
    meta['subjects'] = texts('genre')
    meta['series'] = (texts('sequence') or [''])[0]
    meta['series_index'] = None

    cover_id = None
    for el in root.iter():
        if local(el.tag) == 'coverpage':
            for img in el.iter():
                href = img.get('{http://www.w3.org/1999/xlink}href') or img.get('href') or ''
                if href.startswith('#'):
                    cover_id = href[1:]
    if cover_id:
        for el in root.iter():
            if local(el.tag) == 'binary' and el.get('id') == cover_id:
                try:
                    meta['cover'] = base64.b64decode(el.text or '')
                except Exception:
                    pass
    return meta


def inspect_file(path):
    ext = os.path.splitext(path)[1].lower()
    fmt = FORMATS.get(ext)
    if not fmt:
        return None
    meta = {}
    try:
        if ext == '.epub':
            meta = epub_meta(path)
        elif ext == '.fb2':
            meta = fb2_meta(path)
    except Exception as exc:
        log('  metadata not read (%s): %s' % (fmt, exc))

    title = clean_text(meta.get('title') or '') or os.path.splitext(os.path.basename(path))[0]
    authors = [clean_text(a) for a in meta.get('authors') or [] if clean_text(a)] or ['Unknown']
    lang = (meta.get('language') or '').strip().lower()
    lang = LANG3.get(lang[:2], lang[:3] or 'und')
    return {
        'format': fmt,
        'ext': ext,
        'title': title,
        'authors': authors,
        'language': lang,
        'publisher': clean_text(meta.get('publisher') or ''),
        'date': (meta.get('date') or '').strip(),
        'description': clean_text(meta.get('description') or ''),
        'subjects': [clean_text(s) for s in meta.get('subjects') or [] if clean_text(s)][:10],
        'identifiers': meta.get('identifiers') or [],
        'series': clean_text(meta.get('series') or ''),
        'series_index': meta.get('series_index'),
        'cover': meta.get('cover'),
    }


def norm_date(value):
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', value or '')
    if m:
        return '%s-%s-%s 00:00:00+00:00' % m.groups()
    m = re.match(r'(\d{4})', value or '')
    if m:
        return '%s-01-01 00:00:00+00:00' % m.group(1)
    return time.strftime('%Y-%m-%d %H:%M:%S+00:00', time.gmtime())


def get_or_create(cur, table, name_col, name, extra_col=None):
    if extra_col:
        cur.execute('SELECT id FROM %s WHERE %s = ?' % (table, name_col), (name,))
    else:
        cur.execute('SELECT id FROM %s WHERE %s = ?' % (table, name_col), (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    if table == 'languages':
        cur.execute('INSERT INTO languages (lang_code) VALUES (?)', (name,))
    elif table == 'publishers':
        cur.execute('INSERT INTO publishers (name, sort) VALUES (?,?)', (name, name))
    elif table == 'tags':
        cur.execute('INSERT INTO tags (name, sort) VALUES (?,?)', (name, name))
    elif table == 'series':
        cur.execute('INSERT INTO series (name, sort) VALUES (?,?)', (name, name))
    else:
        cur.execute('INSERT INTO %s (%s, sort) VALUES (?,?)' % (table, name_col), (name, name))
    return cur.lastrowid


def ensure_db(con):
    con.executescript(SCHEMA)
    cur = con.cursor()
    cur.execute('SELECT COUNT(*) FROM library_id')
    if cur.fetchone()[0] == 0:
        cur.execute('INSERT INTO library_id (id, uuid) VALUES (1, ?)', (str(uuid.uuid4()),))
    con.commit()


def import_one(con, root, src, dry_run=False):
    info = inspect_file(src)
    if info is None:
        return 'unsupported'

    title = info['title']
    author = info['authors'][0]
    cur = con.cursor()

    cur.execute("""SELECT b.id FROM books b
                   JOIN books_authors_link bal ON bal.book = b.id
                   JOIN authors a ON a.id = bal.author
                   WHERE b.title = ? AND a.name = ?""", (title, author))
    if cur.fetchone():
        return 'exists'

    if dry_run:
        log('  would import: %s - %s (%s)' % (title, author, info['format']))
        return 'dry'

    now = time.strftime('%Y-%m-%d %H:%M:%S+00:00', time.gmtime())
    cur.execute("""INSERT INTO books (title, sort, timestamp, pubdate, series_index, author_sort,
                                     isbn, lccn, path, flags, uuid, has_cover, last_modified)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (title, title, now, norm_date(info['date']), 1.0, author_sort(author),
                 '', '', '', 1, str(uuid.uuid4()), 0, now))
    bid = cur.lastrowid

    folder = '%s/%s (%d)' % (safe_name(author), safe_name(title), bid)
    full_dir = os.path.join(root, folder)
    os.makedirs(full_dir, exist_ok=True)

    base = safe_name(title)
    dst_name = base + info['ext']
    dst = os.path.join(full_dir, dst_name)
    n = 1
    while os.path.exists(dst):
        n += 1
        dst_name = '%s (%d)%s' % (base, n, info['ext'])
        dst = os.path.join(full_dir, dst_name)
    shutil.move(src, dst)
    base = os.path.splitext(dst_name)[0]

    if info['cover']:
        with open(os.path.join(full_dir, 'cover.jpg'), 'wb') as fh:
            fh.write(info['cover'])
        cur.execute('UPDATE books SET has_cover = 1 WHERE id = ?', (bid,))

    cur.execute('UPDATE books SET path = ? WHERE id = ?', (folder, bid))
    cur.execute('INSERT INTO data (book, format, uncompressed_size, name) VALUES (?,?,?,?)',
                (bid, info['format'], os.path.getsize(dst), base))

    for a in info['authors'][:5]:
        aid = get_or_create(cur, 'authors', 'name', a)
        cur.execute('INSERT OR IGNORE INTO books_authors_link (book, author) VALUES (?,?)', (bid, aid))

    if info['publisher']:
        pid = get_or_create(cur, 'publishers', 'name', info['publisher'])
        cur.execute('INSERT OR IGNORE INTO books_publishers_link (book, publisher) VALUES (?,?)', (bid, pid))

    if info['language'] and info['language'] != 'und':
        lid = get_or_create(cur, 'languages', 'lang_code', info['language'])
        cur.execute('INSERT OR IGNORE INTO books_languages_link (book, lang_code, item_order, link) VALUES (?,?,?,?)',
                    (bid, lid, 0, ''))

    for t in info['subjects']:
        tid = get_or_create(cur, 'tags', 'name', t)
        cur.execute('INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (?,?)', (bid, tid))

    if info['series']:
        sid = get_or_create(cur, 'series', 'name', info['series'])
        cur.execute('INSERT OR IGNORE INTO books_series_link (book, series) VALUES (?,?)', (bid, sid))
        try:
            idx = float(info['series_index'])
            cur.execute('UPDATE books SET series_index = ? WHERE id = ?', (idx, bid))
        except (TypeError, ValueError):
            pass

    if info['description']:
        cur.execute('INSERT OR IGNORE INTO comments (book, text) VALUES (?,?)', (bid, info['description']))

    for ident in info['identifiers']:
        digits = re.sub(r'[^0-9Xx]', '', ident)
        if len(digits) in (10, 13):
            cur.execute('INSERT OR IGNORE INTO identifiers (type, value) VALUES (?,?)', ('isbn', digits))
            cur.execute('SELECT id FROM identifiers WHERE type = ? AND value = ?', ('isbn', digits))
            row = cur.fetchone()
            if row:
                cur.execute('INSERT OR IGNORE INTO books_identifiers_link (book, identifier) VALUES (?,?)', (bid, row[0]))

    con.commit()
    log('  imported: %s - %s (%s, id %d)' % (title, author, info['format'], bid))
    return 'ok'


def scan(root, dry_run=False):
    inbox = os.path.join(root, 'inbox')
    os.makedirs(inbox, exist_ok=True)
    db_path = os.path.join(root, 'metadata.db')
    con = sqlite3.connect(db_path)
    ensure_db(con)
    counts = {}
    for name in sorted(os.listdir(inbox)):
        src = os.path.join(inbox, name)
        if not os.path.isfile(src) or name.startswith('.'):
            continue
        if os.path.splitext(name)[1].lower() not in FORMATS:
            continue
        try:
            res = import_one(con, root, src, dry_run)
        except Exception as exc:
            res = 'error'
            log('  ERROR %s: %s' % (name, exc))
        counts[res] = counts.get(res, 0) + 1
        if res in ('exists', 'unsupported', 'error') and not dry_run:
            skip_dir = os.path.join(inbox, '_skipped')
            os.makedirs(skip_dir, exist_ok=True)
            shutil.move(src, os.path.join(skip_dir, name))
    con.close()
    return counts


def main(argv):
    root = DEFAULT_ROOT
    watch = 0
    dry = False
    quiet = False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--watch':
            i += 1
            watch = int(argv[i])
        elif a == '--dry-run':
            dry = True
        elif a == '--quiet':
            quiet = True
        elif not a.startswith('-'):
            root = a
        i += 1

    if watch:
        log('watching %s/inbox every %ds' % (root, watch))
        while True:
            counts = scan(root, dry)
            if sum(counts.values()):
                log('cycle: %s' % ', '.join('%s=%d' % kv for kv in sorted(counts.items())))
            time.sleep(watch)
    else:
        counts = scan(root, dry)
        if counts:
            log('done: %s' % ', '.join('%s=%d' % kv for kv in sorted(counts.items())))
        elif not quiet:
            log('inbox is empty')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
