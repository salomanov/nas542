<?php
/**
 * NAS542 library — JSON API for the modern web interface.
 *
 * Loads the COPS config, which also enforces HTTP Basic auth, then reads the
 * Calibre database directly (read-only) and serves covers and book files.
 *
 *   api.php?action=list&view=all|recent&q=&author=&tag=&sort=&offset=&limit=
 *   api.php?action=book&id=
 *   api.php?action=facets
 *   api.php?action=cover&id=
 *   api.php?action=download&id=<book>&data=<data>
 */

require_once dirname(__DIR__) . '/config.php';

$root = rtrim($config['calibre_directory'], '/');
$action = isset($_GET['action']) ? $_GET['action'] : 'list';

function fail($code, $message)
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(array('error' => $message), JSON_UNESCAPED_UNICODE);
    exit;
}

function db()
{
    global $root;
    static $pdo = null;
    if ($pdo === null) {
        try {
            $pdo = new PDO('sqlite:' . $root . '/metadata.db');
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
            $pdo->exec('PRAGMA busy_timeout = 5000');
        } catch (Exception $e) {
            fail(500, 'database is not available');
        }
    }
    return $pdo;
}

function rows($sql, $params = array())
{
    $stmt = db()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll();
}

function row($sql, $params = array())
{
    $stmt = db()->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetch();
}

/* ---------------------------------------------------------------- covers */

if ($action === 'cover') {
    $id = isset($_GET['id']) ? (int) $_GET['id'] : 0;
    $book = row('SELECT path, has_cover FROM books WHERE id = ?', array($id));
    $file = $book ? $root . '/' . $book['path'] . '/cover.jpg' : '';
    if (!$book || !$book['has_cover'] || !is_file($file)) {
        http_response_code(404);
        header('Content-Type: image/svg+xml');
        echo '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>';
        exit;
    }
    header('Content-Type: image/jpeg');
    header('Content-Length: ' . filesize($file));
    header('Cache-Control: public, max-age=604800');
    readfile($file);
    exit;
}

/* -------------------------------------------------------------- download */

if ($action === 'download') {
    $bookId = isset($_GET['id']) ? (int) $_GET['id'] : 0;
    $dataId = isset($_GET['data']) ? (int) $_GET['data'] : 0;
    $data = row(
        'SELECT d.name, d.format, b.path FROM data d JOIN books b ON b.id = d.book
         WHERE d.id = ? AND d.book = ?',
        array($dataId, $bookId)
    );
    if (!$data) {
        fail(404, 'file not found');
    }
    $ext = strtolower($data['format']);
    $file = $root . '/' . $data['path'] . '/' . $data['name'] . '.' . $ext;
    $real = realpath($file);
    if ($real === false || strpos($real, realpath($root)) !== 0 || !is_file($real)) {
        fail(404, 'file not found');
    }
    $filename = $data['name'] . '.' . $ext;
    header('Content-Type: application/octet-stream');
    header('Content-Length: ' . filesize($real));
    header("Content-Disposition: attachment; filename*=UTF-8''" . rawurlencode($filename));
    header('Cache-Control: private, max-age=0');
    readfile($real);
    exit;
}

/* ------------------------------------------------------------ json stuff */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

function authors_of($bookId)
{
    return rows(
        'SELECT a.id, a.name FROM authors a
         JOIN books_authors_link l ON l.author = a.id
         WHERE l.book = ? ORDER BY a.name COLLATE NOCASE',
        array($bookId)
    );
}

function tags_of($bookId)
{
    return rows(
        'SELECT t.id, t.name FROM tags t
         JOIN books_tags_link l ON l.tag = t.id
         WHERE l.book = ? ORDER BY t.name COLLATE NOCASE',
        array($bookId)
    );
}

function formats_of($bookId)
{
    return rows(
        'SELECT id, format, uncompressed_size FROM data WHERE book = ? ORDER BY format',
        array($bookId)
    );
}

if ($action === 'book') {
    $id = isset($_GET['id']) ? (int) $_GET['id'] : 0;
    $book = row(
        'SELECT b.id, b.title, b.path, b.has_cover, b.pubdate, b.series_index, b.timestamp,
                (SELECT text FROM comments WHERE book = b.id) AS description,
                (SELECT s.name FROM series s JOIN books_series_link l ON l.series = s.id
                  WHERE l.book = b.id) AS series,
                (SELECT p.name FROM publishers p JOIN books_publishers_link l ON l.publisher = p.id
                  WHERE l.book = b.id) AS publisher,
                (SELECT g.lang_code FROM languages g JOIN books_languages_link l ON l.lang_code = g.id
                  WHERE l.book = b.id) AS language
         FROM books b WHERE b.id = ?',
        array($id)
    );
    if (!$book) {
        fail(404, 'book not found');
    }
    $formats = formats_of($id);
    echo json_encode(array(
        'id' => (int) $book['id'],
        'title' => $book['title'],
        'authors' => authors_of($id),
        'tags' => tags_of($id),
        'formats' => array_map(function ($f) {
            return array(
                'id' => (int) $f['id'],
                'format' => $f['format'],
                'size' => (int) $f['uncompressed_size'],
                'reader' => strtolower($f['format']) === 'epub' ? '../epubreader.php?data=' . (int) $f['id'] : null,
            );
        }, $formats),
        'description' => $book['description'],
        'publisher' => $book['publisher'],
        'series' => $book['series'],
        'seriesIndex' => $book['series_index'] !== null ? (float) $book['series_index'] : null,
        'language' => $book['language'],
        'pubdate' => $book['pubdate'],
        'hasCover' => (int) $book['has_cover'],
        'cover' => 'api.php?action=cover&id=' . (int) $book['id'],
    ), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($action === 'facets') {
    $authors = rows(
        'SELECT a.id, a.name, COUNT(*) AS count FROM authors a
         JOIN books_authors_link l ON l.author = a.id
         GROUP BY a.id ORDER BY a.name COLLATE NOCASE'
    );
    $tags = rows(
        'SELECT t.id, t.name, COUNT(*) AS count FROM tags t
         JOIN books_tags_link l ON l.tag = t.id
         GROUP BY t.id ORDER BY count DESC, t.name COLLATE NOCASE'
    );
    $total = row('SELECT COUNT(*) AS n FROM books');
    echo json_encode(array(
        'total' => (int) $total['n'],
        'authors' => $authors,
        'tags' => $tags,
    ), JSON_UNESCAPED_UNICODE);
    exit;
}

if ($action === 'list') {
    $view = isset($_GET['view']) ? $_GET['view'] : 'all';
    $q = isset($_GET['q']) ? trim($_GET['q']) : '';
    $author = isset($_GET['author']) && $_GET['author'] !== '' ? (int) $_GET['author'] : null;
    $tag = isset($_GET['tag']) && $_GET['tag'] !== '' ? (int) $_GET['tag'] : null;
    $sort = isset($_GET['sort']) ? $_GET['sort'] : 'recent';
    $offset = isset($_GET['offset']) ? max(0, (int) $_GET['offset']) : 0;
    $limit = isset($_GET['limit']) ? min(96, max(1, (int) $_GET['limit'])) : 36;

    $where = array();
    $params = array();

    if ($q !== '') {
        $where[] = '(b.title LIKE ? OR b.id IN (
                        SELECT l.book FROM books_authors_link l
                        JOIN authors a ON a.id = l.author WHERE a.name LIKE ?))';
        $params[] = '%' . $q . '%';
        $params[] = '%' . $q . '%';
    }
    if ($author !== null) {
        $where[] = 'b.id IN (SELECT book FROM books_authors_link WHERE author = ?)';
        $params[] = $author;
    }
    if ($tag !== null) {
        $where[] = 'b.id IN (SELECT book FROM books_tags_link WHERE tag = ?)';
        $params[] = $tag;
    }
    $whereSql = $where ? ' WHERE ' . implode(' AND ', $where) : '';

    switch ($sort) {
        case 'title':
            $orderSql = ' ORDER BY b.sort COLLATE NOCASE';
            break;
        case 'author':
            $orderSql = ' ORDER BY (SELECT MIN(a.sort) FROM authors a
                          JOIN books_authors_link l ON l.author = a.id
                          WHERE l.book = b.id) COLLATE NOCASE, b.sort COLLATE NOCASE';
            break;
        default:
            $orderSql = ' ORDER BY b.timestamp DESC, b.id DESC';
            break;
    }

    $total = row('SELECT COUNT(*) AS n FROM books b' . $whereSql, $params);
    $books = rows(
        'SELECT b.id, b.title, b.path, b.has_cover, b.pubdate, b.timestamp,
                (SELECT GROUP_CONCAT(a.name, char(31)) FROM authors a
                  JOIN books_authors_link l ON l.author = a.id
                  WHERE l.book = b.id) AS authors,
                (SELECT GROUP_CONCAT(d.format, char(31)) FROM data d
                  WHERE d.book = b.id) AS formats
         FROM books b' . $whereSql . $orderSql . ' LIMIT ' . (int) $limit . ' OFFSET ' . (int) $offset,
        $params
    );

    $out = array();
    foreach ($books as $b) {
        $out[] = array(
            'id' => (int) $b['id'],
            'title' => $b['title'],
            'authors' => $b['authors'] !== null ? explode(chr(31), $b['authors']) : array(),
            'formats' => $b['formats'] !== null ? array_values(array_unique(explode(chr(31), $b['formats']))) : array(),
            'hasCover' => (int) $b['has_cover'],
            'pubdate' => $b['pubdate'],
            'cover' => 'api.php?action=cover&id=' . (int) $b['id'],
        );
    }

    echo json_encode(array(
        'total' => (int) $total['n'],
        'offset' => $offset,
        'limit' => $limit,
        'view' => $view,
        'books' => $out,
    ), JSON_UNESCAPED_UNICODE);
    exit;
}

fail(400, 'unknown action');
