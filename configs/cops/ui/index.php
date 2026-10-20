<?php
/**
 * NAS542 library — modern web catalogue.
 * Requires the COPS config (and therefore HTTP Basic auth) before rendering.
 */
require_once dirname(__DIR__) . '/config.php';
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#faf9f7">
<title>Библиотека NAS542</title>
<link rel="icon" href="../images/favicon.ico">
<link rel="stylesheet" href="assets/app.css">
</head>
<body>

<header class="topbar">
    <a class="brand" href="#/">
        <img src="../images/nas542-logo.png" alt="" width="30" height="30">
        <span>Библиотека</span>
    </a>

    <form class="search" id="search-form" role="search">
        <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7"></circle><path d="M20 20l-3.6-3.6"></path>
        </svg>
        <input id="q" type="search" placeholder="Название или автор" autocomplete="off" spellcheck="false" aria-label="Поиск">
        <kbd class="hint">/</kbd>
    </form>

    <button class="icon-btn only-mobile" id="filters" type="button" aria-label="Фильтры">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18M6 12h12M10 18h4"></path></svg>
    </button>
    <button class="icon-btn" id="theme" type="button" aria-label="Сменить тему">
        <svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"></path></svg>
        <svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"></circle><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8"></path></svg>
    </button>
</header>

<div class="rail-backdrop" id="rail-backdrop"></div>

<div class="layout">
    <aside class="rail" id="rail">
        <nav class="rail-block">
            <a class="rail-link" href="#/" data-view="all">Все книги <span class="count" id="count-all"></span></a>
            <a class="rail-link" href="#recent" data-view="recent">Недавние поступления</a>
        </nav>

        <div class="rail-block">
            <h3>Авторы</h3>
            <div class="rail-list" id="authors"></div>
        </div>

        <div class="rail-block">
            <h3>Жанры</h3>
            <div class="chips" id="tags"></div>
        </div>

        <div class="rail-block rail-foot">
            <a class="rail-link" href="../index.php?page=19">Настройки COPS</a>
            <a class="rail-link" href="../feed.php">OPDS-каталог</a>
            <a class="rail-link" href="../index.php?page=1">Старый вид</a>
        </div>
    </aside>

    <main class="content">
        <div class="content-head">
            <div class="titles">
                <h1 id="title">Все книги</h1>
                <p class="sub" id="subtitle"></p>
            </div>
            <label class="sort">
                <span>Сортировка</span>
                <select id="sort">
                    <option value="recent">По дате</option>
                    <option value="title">По названию</option>
                    <option value="author">По автору</option>
                </select>
            </label>
        </div>

        <div class="grid" id="grid" aria-live="polite"></div>
        <div class="state" id="state" hidden></div>
        <div class="sentinel" id="sentinel"></div>
    </main>
</div>

<div class="modal" id="modal" hidden>
    <div class="modal-backdrop" data-close></div>
    <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="m-title">
        <button class="modal-close" type="button" data-close aria-label="Закрыть">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"></path></svg>
        </button>
        <div class="modal-body" id="modal-body"></div>
    </div>
</div>

<script src="assets/app.js"></script>
</body>
</html>
