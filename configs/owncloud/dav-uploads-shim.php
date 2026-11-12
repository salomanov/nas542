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
	if ($u === '' && !empty($_SERVER['HTTP_AUTHORIZATION'])) {
		if (stripos($_SERVER['HTTP_AUTHORIZATION'], 'basic ') === 0) {
			$cred = base64_decode(substr($_SERVER['HTTP_AUTHORIZATION'], 6));
			if (strpos($cred, ':') !== false) {
				list($u, $p) = explode(':', $cred, 2);
			}
		}
	}
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

// OPTIONS on root or transfer
if ($method === 'OPTIONS') {
	header('Allow: MKCOL, PUT, MOVE, DELETE, PROPFIND, OPTIONS');
	header('DAV: 1, 3, extended-mkcol');
	header('HTTP/1.1 200 OK');
	exit;
}

// PROPFIND on root
if ($method === 'PROPFIND' && $tid === '') {
	header('Content-Type: application/xml; charset=utf-8');
	header('HTTP/1.1 207 Multi-Status');
	echo '<?xml version="1.0" encoding="utf-8"?>' . "\n";
	echo '<d:multistatus xmlns:d="DAV:">';
	echo '<d:response><d:href>' . htmlspecialchars($pi) . '</d:href>';
	echo '<d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop>';
	echo '<d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>';
	echo '</d:multistatus>';
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
	if (!preg_match('#/(?:dav/files/[^/]+|webdav)(/.*)$#', $path, $m)) {
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
		$targetChunk = $dir . '/' . $chunk;
		$in  = fopen('php://input', 'rb');
		$out = fopen($targetChunk, 'wb');
		if (!$in || !$out) {
			header('HTTP/1.1 500 Internal Server Error');
			exit;
		}

		$completed = false;
		register_shutdown_function(function() use (&$completed, $targetChunk) {
			if (!$completed && file_exists($targetChunk)) {
				@unlink($targetChunk);
			}
		});

		stream_copy_to_stream($in, $out);
		fclose($in);
		fclose($out);

		if (isset($_SERVER['CONTENT_LENGTH'])) {
			$expected = (int)$_SERVER['CONTENT_LENGTH'];
			$actual   = @filesize($targetChunk);
			if ($expected > 0 && $actual !== $expected) {
				@unlink($targetChunk);
				header('HTTP/1.1 400 Bad Request');
				exit;
			}
		}

		$completed = true;
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
			if (is_file($c) && basename($c) !== '.file' && basename($c) !== '.assembled') {
				$real[] = $c;
			}
		}
		if (defined('SORT_NATURAL')) {
			sort($real, SORT_NATURAL);
		} else {
			natsort($real);
		}

		// Integrity check: if chunks are sequentially numbered (Android ownCloud style)
		if (count($real) > 1 && ctype_digit(basename($real[0]))) {
			$chunkSize = filesize($real[0]);
			for ($i = 0; $i < count($real) - 1; $i++) {
				if ((int)basename($real[$i]) !== $i || filesize($real[$i]) !== $chunkSize) {
					header('HTTP/1.1 400 Bad Request');
					exit;
				}
			}
			if ((int)basename($real[count($real) - 1]) !== count($real) - 1) {
				header('HTTP/1.1 400 Bad Request');
				exit;
			}
		}

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

		$mtime = 0;
		if (isset($_SERVER['HTTP_X_OC_MTIME'])) {
			$mtime = (int)$_SERVER['HTTP_X_OC_MTIME'];
		} elseif (isset($_SERVER['HTTP_X_OC_MTIME_PART'])) {
			$mtime = (int)$_SERVER['HTTP_X_OC_MTIME_PART'];
		}
		if ($mtime > 0) {
			$view->touch($rel, $mtime);
		}

		$info = $view->getFileInfo($rel);
		if ($info) {
			$etag = $info->getEtag();
			$fileId = $info->getId();
			if ($etag) {
				header('ETag: "' . $etag . '"');
				header('OC-ETag: "' . $etag . '"');
			}
			if ($fileId) {
				header('OC-FileId: ' . $fileId);
			}
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
		@rmdir(dirname($dir));
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
		if (is_dir($dir)) {
			$depth = isset($_SERVER['HTTP_DEPTH']) ? $_SERVER['HTTP_DEPTH'] : '1';
			if ($depth !== '0') {
				$files = glob($dir . '/*');
				if ($files) {
					foreach ($files as $f) {
						if (!is_file($f)) continue;
						$bn = basename($f);
						if ($bn === '.file' || $bn === '.assembled') continue;
						$sz = filesize($f);
						$href = rtrim($pi, '/') . '/' . $bn;
						echo '<d:response>';
						echo '<d:href>' . htmlspecialchars($href) . '</d:href>';
						echo '<d:propstat><d:prop>';
						echo '<d:getcontentlength>' . $sz . '</d:getcontentlength>';
						echo '<d:resourcetype/>';
						echo '</d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat>';
						echo '</d:response>';
					}
				}
			}
		}
		echo '</d:multistatus>';
		exit;

	case 'HEAD':
	case 'GET':
		if (is_dir($dir)) {
			header('HTTP/1.1 200 OK');
			exit;
		}
		header('HTTP/1.1 404 Not Found');
		exit;

	default:
		header('HTTP/1.1 405 Method Not Allowed');
		exit;
}
