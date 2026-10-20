<?php
/*
 * Локальная конфигурация COPS.
 * Файл генерируется scripts/07-cops.sh — правки вручную будут перезаписаны
 * при следующем запуске (меняйте шаблон configs/cops/config_local.php).
 */

/*
 * PHP CLI server (php -S) не всегда заполняет PHP_AUTH_USER/PW.
 * Разбираем заголовок Authorization сами — проверка пароля ниже, в config.php.
 */
if (!isset($_SERVER['PHP_AUTH_USER']) && !empty($_SERVER['HTTP_AUTHORIZATION'])
    && preg_match('/^Basic\s+(.+)$/i', $_SERVER['HTTP_AUTHORIZATION'], $m)) {
    $pair = base64_decode($m[1]);
    if (strpos($pair, ':') !== false) {
        list($_SERVER['PHP_AUTH_USER'], $_SERVER['PHP_AUTH_PW']) = explode(':', $pair, 2);
    }
}

/*
 * Шаблон и стиль интерфейса теперь выбираются на странице настроек COPS
 * (index.php?page=19, шестерёнка в шапке): выбор хранится в cookie.
 * Чтобы вернуть тему NAS542, выберите «NAS542 (с логотипом)» и обновите страницу.
 */

/* --- библиотека --- */
$config['calibre_directory'] = '__APPS__/calibre/';

/* --- оформление --- */
$config['cops_title_default'] = 'Библиотека NAS542';
$config['cops_subtitle_default'] = 'Домашняя библиотека';
$config['cops_language'] = 'ru';
$config['cops_template'] = 'nas542';
$config['cops_style'] = 'default';
$config['cops_icon'] = 'images/favicon.ico';
$config['cops_show_icons'] = '1';

/* --- список книг --- */
$config['cops_recentbooks_limit'] = '12';
$config['cops_max_item_per_page'] = '30';
$config['cops_use_fancyapps'] = '0';
$config['cops_prefered_format'] = array('EPUB', 'FB2', 'PDF', 'MOBI', 'AZW3');

/* --- навигация: убираем второстепенные полки --- */
$config['cops_ignored_categories'] = array('series', 'publisher', 'rating', 'language');

/* --- обложки: кэш на диске (/tmp — рамдиск) --- */
$config['cops_thumbnail_handling'] = '';
$config['cops_thumbnail_cache_directory'] = '__APPS__/calibre/.thumbs/';

/* --- доступ --- */
$config['cops_basic_authentication'] = array(
    'username' => '__COPS_USER__',
    'password' => '__COPS_PASS__',
);
