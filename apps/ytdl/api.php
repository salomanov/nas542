<?php
header('Content-Type: application/json; charset=utf-8');

$jobs_dir = '/i-data/45f1aca1/Apps/ytdl/jobs';
$downloads_dir = '/i-data/45f1aca1/Apps/downloads/video';

if (!is_dir($jobs_dir)) {
    @mkdir($jobs_dir, 0777, true);
}
if (!is_dir($downloads_dir)) {
    @mkdir($downloads_dir, 0777, true);
}

$action = isset($_GET['action']) ? $_GET['action'] : (isset($_POST['action']) ? $_POST['action'] : '');

function json_out($data, $code = 200) {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

if ($action === 'start') {
    $input = json_decode(file_get_contents('php://input'), true);
    if (!$input) {
        $input = $_POST;
    }

    $url = isset($input['url']) ? trim($input['url']) : '';
    $format = isset($input['format']) && $input['format'] === 'audio' ? 'audio' : 'video';

    if (empty($url) || !preg_match('#^https?://#i', $url)) {
        json_out(array('ok' => false, 'error' => 'Пожалуйста, введите корректную ссылку (http:// или https://)'), 400);
    }

    $job_id = 'job_' . time() . '_' . substr(md5($url . microtime()), 0, 6);
    $job_log = $jobs_dir . '/' . $job_id . '.log';
    $job_pid = $jobs_dir . '/' . $job_id . '.pid';
    $job_meta = $jobs_dir . '/' . $job_id . '.json';

    $meta = array(
        'id' => $job_id,
        'url' => $url,
        'format' => $format,
        'created_at' => date('Y-m-d H:i:s'),
        'status' => 'running',
    );
    file_put_contents($job_meta, json_encode($meta, JSON_UNESCAPED_UNICODE));

    // Build command
    $safe_url = escapeshellarg($url);
    $safe_out = escapeshellarg($downloads_dir . '/%(title)s [%(id)s].%(ext)s');

    if ($format === 'audio') {
        $cmd = "/opt/bin/yt-dlp --ffmpeg-location /opt/bin -x --audio-format mp3 --audio-quality 0 -o {$safe_out} --no-colors --newline {$safe_url}";
    } else {
        $cmd = "/opt/bin/yt-dlp --ffmpeg-location /opt/bin -o {$safe_out} --no-colors --newline {$safe_url}";
    }

    // Execute in background
    $exec_cmd = "nohup {$cmd} > " . escapeshellarg($job_log) . " 2>&1 & echo $! > " . escapeshellarg($job_pid);
    exec($exec_cmd);

    json_out(array('ok' => true, 'jobId' => $job_id, 'format' => $format, 'url' => $url));
}

if ($action === 'status') {
    $job_id = isset($_GET['jobId']) ? basename($_GET['jobId']) : '';
    if (empty($job_id)) {
        json_out(array('ok' => false, 'error' => 'jobId is required'), 400);
    }

    $job_log = $jobs_dir . '/' . $job_id . '.log';
    $job_pid = $jobs_dir . '/' . $job_id . '.pid';
    $job_meta = $jobs_dir . '/' . $job_id . '.json';

    if (!file_exists($job_meta)) {
        json_out(array('ok' => false, 'error' => 'Задание не найдено'), 404);
    }

    $meta = json_decode(file_get_contents($job_meta), true);
    $pid = file_exists($job_pid) ? intval(trim(file_get_contents($job_pid))) : 0;

    $is_running = false;
    if ($pid > 0) {
        $check = shell_exec("kill -0 {$pid} 2>&1");
        $is_running = empty($check);
    }

    $log_content = file_exists($job_log) ? file_get_contents($job_log) : '';
    $log_lines = explode("\n", trim($log_content));
    $recent_lines = array_slice($log_lines, -25);

    $percent = 0;
    $speed = '';
    $eta = '';
    $title = '';
    $status = $is_running ? 'running' : 'completed';

    // Parse progress from log lines
    foreach ($log_lines as $line) {
        if (preg_match('#\[download\]\s+(\d+(?:\.\d+)?)%#', $line, $m)) {
            $percent = floatval($m[1]);
        }
        if (preg_match('#at\s+([^\s]+)\s+ETA\s+([^\s]+)#', $line, $m)) {
            $speed = $m[1];
            $eta = $m[2];
        }
        if (preg_match('#\[ExtractAudio\] Destination:\s+(.+)#', $line, $m)) {
            $title = basename($m[1]);
        }
        if (preg_match('#\[download\] Destination:\s+(.+)#', $line, $m)) {
            $title = basename($m[1]);
        }
        if (strpos($line, 'ERROR:') !== false) {
            $status = 'error';
        }
    }

    if (!$is_running && $status !== 'error') {
        $percent = 100;
        $status = 'completed';
    }

    $meta['status'] = $status;
    $meta['percent'] = $percent;
    $meta['speed'] = $speed;
    $meta['eta'] = $eta;
    $meta['title'] = $title;
    $meta['log'] = implode("\n", $recent_lines);

    file_put_contents($job_meta, json_encode($meta, JSON_UNESCAPED_UNICODE));
    json_out(array('ok' => true, 'data' => $meta));
}

if ($action === 'files') {
    $files = array();
    if (is_dir($downloads_dir)) {
        $items = scandir($downloads_dir);
        foreach ($items as $item) {
            if ($item === '.' || $item === '..' || strpos($item, '.') === 0) continue;
            $full = $downloads_dir . '/' . $item;
            if (is_file($full)) {
                $files[] = array(
                    'name' => $item,
                    'size' => filesize($full),
                    'size_human' => round(filesize($full) / (1024 * 1024), 2) . ' MB',
                    'mtime' => filemtime($full),
                    'date' => date('d.m.Y H:i', filemtime($full)),
                );
            }
        }
    }
    // Sort by modification time descending
    usort($files, function($a, $b) {
        return $b['mtime'] - $a['mtime'];
    });

    json_out(array('ok' => true, 'files' => $files));
}

if ($action === 'delete') {
    $input = json_decode(file_get_contents('php://input'), true);
    $filename = isset($input['filename']) ? basename($input['filename']) : '';
    if (empty($filename)) {
        json_out(array('ok' => false, 'error' => 'filename is required'), 400);
    }

    $full = $downloads_dir . '/' . $filename;
    if (file_exists($full) && is_file($full)) {
        @unlink($full);
        json_out(array('ok' => true));
    } else {
        json_out(array('ok' => false, 'error' => 'Файл не найден'), 404);
    }
}

json_out(array('ok' => false, 'error' => 'Unknown action'), 400);
