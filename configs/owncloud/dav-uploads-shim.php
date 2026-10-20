<?php
/**
 * OC10-DAV-UPLOADS-SHIM
 * Implements ownCloud 10 / Nextcloud "chunked upload v2" (/remote.php/dav/uploads/...)
 * on top of ownCloud 7, which only knows the legacy chunking.
 *
 * Flow used by mobile clients:
 *   MKCOL  /remote.php/dav/uploads/<user>/<transferid>/
 *   PUT    /remote.php/dav/uploads/<user>/<transferid>/<chunknumber>     (repeated)
 *   MOVE   /remote.php/dav/uploads/<user>/<transferid>/.file
 *            Destination: .../remote.php/dav/files/<user>/<target path>
 *   DELETE /remote.php/dav/uploads/<user>/<transferid>
 */

if (!OC_User::isLoggedIn()) {
	$u = isset($_SERVER['PHP_AUTH_USER']) ? $_SERVER['PHP_AUTH_USER'] : '';
	$p = isset($_SERVER['PHP_AUTH_PW']) ? $_SERVER['PHP_AUTH_PW'] : '';
	if ($u === '' || !OC_User::login($u, $p)) {
		header('WWW-Authenticate: Basic realm="ownCloud"');
		header('HTTP/1.1 401 Unauthorized');
		exit;
	}
}

$user = OC_User::getUser();
$method = $_SERVER['REQUEST_METHOD'];
$pi = isset($_SERVER['PATH_INFO']) ? $_SERVER['PATH_INFO'] : '';

$prefix = '/dav/uploads/';
if (strpos($pi, $prefix) !== 0) {
	header('HTTP/1.1 404 Not Found');
	exit;
}

$tail = substr($pi, strlen($prefix));
$parts = explode('/', trim($tail, '/'));
$reqUser = isset($parts[0]) ? $parts[0] : '';
$tid     = isset($parts[1]) ? $parts[1] : '';
$chunk   = isset($parts[2]) ? $parts[2] : '';

if ($reqUser !== '' && $reqUser !== $user) {
	header('HTTP/1.1 403 Forbidden');
	exit;
}
if ($tid === '' || !preg_match('/^[A-Za-z0-9._-]+$/', $tid)) {
	header('HTTP/1.1 400 Bad Request');
	exit;
}

$dataDir = OC_Config::getValue('datadirectory');
$tmpRoot = rtrim($dataDir, '/') . '/uploads_shim';
$dir     = $tmpRoot . '/' . $user . '/' . $tid;

function shim_rmdir($path) {
	if (!is_dir($path)) {
		@unlink($path);
		return;
	}
	$items = @scandir($path);
	if ($items === false) {
		return;
	}
	foreach ($items as $item) {
		if ($item === '.' || $item === '..') {
			continue;
		}
		shim_rmdir($path . '/' . $item);
	}
	@rmdir($path);
}

function shim_dest_path($user) {
	$dest = isset($_SERVER['HTTP_DESTINATION']) ? $_SERVER['HTTP_DESTINATION'] : '';
	if ($dest === '') {
		return false;
	}
	$path = parse_url($dest, PHP_URL_PATH);
	if ($path === false || $path === null) {
		return false;
	}
	if (!preg_match('#/dav/files/[^/]+(/.*)$#', $path, $m)) {
		return false;
	}
	$rel = urldecode($m[1]);
	$rel = ltrim($rel, '/');
	if ($rel === '') {
		return false;
	}
	// no traversal outside the user's storage
	$safe = array();
	foreach (explode('/', $rel) as $seg) {
		if ($seg === '' || $seg === '.') {
			continue;
		}
		if ($seg === '..') {
			return false;
		}
		$safe[] = $seg;
	}
	return implode('/', $safe);
}

switch ($method) {
	case 'MKCOL':
		if (!is_dir($dir) && !@mkdir($dir, 0770, true)) {
			header('HTTP/1.1 500 Internal Server Error');
			exit;
		}
		header('HTTP/1.1 201 Created');
		exit;

	case 'PUT':
		if ($chunk === '') {
			header('HTTP/1.1 400 Bad Request');
			exit;
		}
		if (!is_dir($dir)) {
			@mkdir($dir, 0770, true);
		}
		$in  = fopen('php://input', 'rb');
		$out = fopen($dir . '/' . $chunk, 'wb');
		if (!$in || !$out) {
			header('HTTP/1.1 500 Internal Server Error');
			exit;
		}
		stream_copy_to_stream($in, $out);
		fclose($in);
		fclose($out);
		header('HTTP/1.1 201 Created');
		exit;

	case 'MOVE':
		$rel = shim_dest_path($user);
		if ($rel === false) {
			header('HTTP/1.1 400 Bad Request');
			exit;
		}
		$chunks = glob($dir . '/*');
		if ($chunks === false || count($chunks) === 0) {
			header('HTTP/1.1 404 Not Found');
			exit;
		}
		$real = array();
		foreach ($chunks as $c) {
			if (is_file($c) && basename($c) !== '.file') {
				$real[] = $c;
			}
		}
		sort($real, SORT_STRING);

		$view = new \OC\Files\View('/' . $user . '/files');
		$parent = dirname($rel);
		if ($parent !== '.' && $parent !== '' && !$view->file_exists($parent)) {
			$view->mkdir($parent, true);
		}

		$assembled = $dir . '/.assembled';
		$out = fopen($assembled, 'wb');
		if (!$out) {
			header('HTTP/1.1 500 Internal Server Error');
			exit;
		}
		foreach ($real as $c) {
			$in = fopen($c, 'rb');
			if ($in) {
				stream_copy_to_stream($in, $out);
				fclose($in);
			}
		}
		fclose($out);

		$in = fopen($assembled, 'rb');
		$ok = $view->file_put_contents($rel, $in);
		if (is_resource($in)) {
			fclose($in);
		}

		shim_rmdir($dir);
		@rmdir(dirname($dir));

		if ($ok === false) {
			header('HTTP/1.1 500 Internal Server Error');
			exit;
		}
		header('HTTP/1.1 201 Created');
		exit;

	case 'DELETE':
		$target = $chunk === '' ? $dir : $dir . '/' . $chunk;
		shim_rmdir($target);
		header('HTTP/1.1 204 No Content');
		exit;

	case 'PROPFIND':
		header('Content-Type: application/xml; charset=utf-8');
		header('HTTP/1.1 207 Multi-Status');
		echo '<?xml version="1.0" encoding="utf-8"?>' . "\n";
		echo '<d:multistatus xmlns:d="DAV:">';
		echo '<d:response><d:href>' . htmlspecialchars($pi) . '</d:href>';
		echo '<d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop>';
		echo '<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>';
		echo '</d:multistatus>';
		exit;

	case 'OPTIONS':
		header('Allow: MKCOL, PUT, MOVE, DELETE, PROPFIND, OPTIONS');
		header('DAV: 1, 3, extended-mkcol');
		header('HTTP/1.1 200 OK');
		exit;

	default:
		header('HTTP/1.1 405 Method Not Allowed');
		exit;
}
