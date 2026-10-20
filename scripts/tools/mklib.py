import os, sqlite3, shutil, time

root = '/i-data/45f1aca1/Apps/calibre'
db_path = os.path.join(root, 'metadata.db')
if os.path.exists(db_path):
    os.remove(db_path)

books = [
    # id, title, author, epub source, isbn, publisher, language, tags, comment
    (1, 'Pride and Prejudice', 'Jane Austen', '/tmp/b1.epub', '9780141439518', 'Penguin Classics', 'eng', ['classic', 'romance'],
     'A classic novel of manners, originally published in 1813.'),
    (2, 'Alice in Wonderland', 'Lewis Carroll', '/tmp/b2.epub', '9780141439761', 'Penguin Classics', 'eng', ['fantasy', 'classic'],
     'The story of a girl who falls down a rabbit hole into a fantasy world.'),
    (3, 'The Adventures of Sherlock Holmes', 'Arthur Conan Doyle', '/tmp/b3.epub', '9780140439076', 'Penguin Classics', 'eng', ['detective', 'classic'],
     'Twelve detective stories featuring Sherlock Holmes.'),
]

schema = """
CREATE TABLE library_id (id INTEGER PRIMARY KEY, uuid TEXT NOT NULL, UNIQUE(uuid));
CREATE TABLE books (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL DEFAULT 'Unknown' COLLATE NOCASE,
  sort TEXT COLLATE NOCASE, timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  pubdate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, series_index REAL NOT NULL DEFAULT 1.0,
  author_sort TEXT COLLATE NOCASE, isbn TEXT DEFAULT "" COLLATE NOCASE, lccn TEXT DEFAULT "" COLLATE NOCASE,
  path TEXT NOT NULL DEFAULT "", flags INTEGER NOT NULL DEFAULT 1, uuid TEXT, has_cover BOOL DEFAULT 0,
  last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE authors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE,
  sort TEXT COLLATE NOCASE, link TEXT NOT NULL DEFAULT "");
CREATE TABLE books_authors_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, author INTEGER NOT NULL, UNIQUE(book, author));
CREATE TABLE data (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, format TEXT NOT NULL COLLATE NOCASE,
  uncompressed_size INTEGER NOT NULL, name TEXT NOT NULL);
CREATE UNIQUE INDEX data_book_format ON data (book, format);
CREATE TABLE series (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE, sort TEXT COLLATE NOCASE);
CREATE TABLE books_series_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, series INTEGER NOT NULL, UNIQUE(book, series));
CREATE TABLE tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE, sort TEXT COLLATE NOCASE);
CREATE TABLE books_tags_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, tag INTEGER NOT NULL, UNIQUE(book, tag));
CREATE TABLE comments (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, text TEXT NOT NULL COLLATE NOCASE, UNIQUE(book));
CREATE TABLE publishers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL COLLATE NOCASE, sort TEXT COLLATE NOCASE);
CREATE TABLE books_publishers_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, publisher INTEGER NOT NULL, UNIQUE(book));
CREATE TABLE languages (id INTEGER PRIMARY KEY AUTOINCREMENT, lang_code TEXT NOT NULL COLLATE NOCASE, UNIQUE(lang_code));
CREATE TABLE books_languages_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, lang_code INTEGER NOT NULL,
  item_order INTEGER NOT NULL DEFAULT 0, link TEXT NOT NULL DEFAULT "", UNIQUE(book, lang_code));
CREATE TABLE identifiers (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL DEFAULT 'isbn' COLLATE NOCASE,
  value TEXT NOT NULL COLLATE NOCASE, UNIQUE(type, value));
CREATE TABLE books_identifiers_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, identifier INTEGER NOT NULL, UNIQUE(book, identifier));
CREATE TABLE ratings (id INTEGER PRIMARY KEY AUTOINCREMENT, rating INTEGER CHECK(rating > -1 AND rating < 11), link TEXT NOT NULL DEFAULT "");
CREATE TABLE books_ratings_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, rating INTEGER NOT NULL, UNIQUE(book, rating));
"""

con = sqlite3.connect(db_path)
cur = con.cursor()
cur.executescript(schema)
cur.execute("INSERT INTO library_id (id, uuid) VALUES (1, '6c1f3a2e-0000-4000-8000-000000000001')")

authors = {}
publishers = {}
languages = {}
tags = {}
now = time.strftime('%Y-%m-%d %H:%M:%S+00:00', time.gmtime())

for bid, title, author, src, isbn, publisher, lang, btags, comment in books:
    folder = '%s/%s (%d)' % (author, title, bid)
    full = os.path.join(root, folder)
    if not os.path.isdir(full):
        os.makedirs(full)
    fname = '%s - %s.epub' % (title, author)
    dst = os.path.join(full, fname)
    if os.path.exists(src):
        shutil.copyfile(src, dst)
    size = os.path.getsize(dst) if os.path.exists(dst) else 0

    cur.execute("""INSERT INTO books (id,title,sort,timestamp,pubdate,series_index,author_sort,isbn,lccn,path,flags,uuid,has_cover,last_modified)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (bid, title, title, now, '2019-01-01 00:00:00+00:00', 1.0, author, isbn, '', folder, 1,
                 '6c1f3a2e-0000-4000-8000-00000000000%d' % bid, 0, now))

    if author not in authors:
        cur.execute("INSERT INTO authors (name, sort, link) VALUES (?,?,?)", (author, author, ''))
        authors[author] = cur.lastrowid
    cur.execute("INSERT INTO books_authors_link (book, author) VALUES (?,?)", (bid, authors[author]))

    if publisher not in publishers:
        cur.execute("INSERT INTO publishers (name, sort) VALUES (?,?)", (publisher, publisher))
        publishers[publisher] = cur.lastrowid
    cur.execute("INSERT INTO books_publishers_link (book, publisher) VALUES (?,?)", (bid, publishers[publisher]))

    if lang not in languages:
        cur.execute("INSERT INTO languages (lang_code) VALUES (?)", (lang,))
        languages[lang] = cur.lastrowid
    cur.execute("INSERT INTO books_languages_link (book, lang_code, item_order, link) VALUES (?,?,?,?)",
                (bid, languages[lang], 0, ''))

    for t in btags:
        if t not in tags:
            cur.execute("INSERT INTO tags (name, sort) VALUES (?,?)", (t, t))
            tags[t] = cur.lastrowid
        cur.execute("INSERT INTO books_tags_link (book, tag) VALUES (?,?)", (bid, tags[t]))

    cur.execute("INSERT INTO comments (book, text) VALUES (?,?)", (bid, comment))
    cur.execute("INSERT INTO data (book, format, uncompressed_size, name) VALUES (?,?,?,?)",
                (bid, 'EPUB', size, '%s - %s' % (title, author)))
    cur.execute("INSERT INTO identifiers (type, value) VALUES ('isbn', ?)", (isbn,))
    cur.execute("INSERT INTO books_identifiers_link (book, identifier) VALUES (?,?)", (bid, cur.lastrowid))

con.commit()
cur.execute("SELECT count(*) FROM books")
print("books:", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM data")
print("formats:", cur.fetchone()[0])
con.close()
