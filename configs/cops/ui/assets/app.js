/* NAS542 library — catalogue front-end (vanilla JS, no build step) */
(() => {
    'use strict';

    const API = 'api.php';
    const PAGE = 36;

    const $ = (sel, root = document) => root.querySelector(sel);

    const el = {
        grid: $('#grid'),
        state: $('#state'),
        sentinel: $('#sentinel'),
        title: $('#title'),
        subtitle: $('#subtitle'),
        sort: $('#sort'),
        q: $('#q'),
        searchForm: $('#search-form'),
        authors: $('#authors'),
        tags: $('#tags'),
        countAll: $('#count-all'),
        modal: $('#modal'),
        modalBody: $('#modal-body'),
        rail: $('#rail'),
        railBackdrop: $('#rail-backdrop'),
        filters: $('#filters'),
    };

    const st = {
        view: 'all',
        id: null,
        q: '',
        sort: localStorage.getItem('nas.sort') || 'recent',
        offset: 0,
        total: 0,
        books: [],
        rendered: 0,
        loading: false,
        done: false,
        seq: 0,
        bookSeq: 0,
        facets: null,
    };

    /* ------------------------------------------------------------ helpers */

    const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ESC[c]);

    function plain(text) {
        return String(text || '')
            .replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi, ' ')
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<\/p>/gi, '\n\n')
            .replace(/<[^>]+>/g, '')
            .replace(/&nbsp;/g, ' ')
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/\n{3,}/g, '\n\n')
            .trim();
    }

    function plural(n, forms) {
        const a = Math.abs(n) % 100;
        const b = a % 10;
        if (a > 10 && a < 20) return forms[2];
        if (b > 1 && b < 5) return forms[1];
        if (b === 1) return forms[0];
        return forms[2];
    }

    const PALETTE = [
        ['#2f4858', '#14202b'], ['#6b4f3f', '#2c1f18'], ['#3f5d52', '#16241f'],
        ['#5b4a6b', '#221b2b'], ['#7a4a3a', '#2e1a14'], ['#3a4f6b', '#161f2b'],
        ['#5c5a3f', '#232110'], ['#4a4a52', '#1b1b20'], ['#4b3b52', '#1c1620'],
    ];
    const colors = (id) => PALETTE[Math.abs(Number(id) || 0) % PALETTE.length];

    function initials(title) {
        const STOP = /^(the|a|an|of|and|or|in|on|to|for|with|at|by|from|der|die|das|la|le|les|el|los|il|un|una)$/i;
        const parts = String(title || '')
            .replace(/[«»"'()[\]]/g, ' ')
            .split(/[\s:.,;—–-]+/)
            .filter((w) => w && !STOP.test(w));
        const usable = parts.length ? parts : String(title || '').split(/\s+/).filter(Boolean);
        return (usable.slice(0, 2).map((w) => w[0]).join('') || '?').toUpperCase();
    }

    function tagLabel(name) {
        return String(name || '').replace(/\s*--\s*/g, ' — ').replace(/\s+/g, ' ').trim();
    }

    const LANGS = {
        rus: 'Русский', eng: 'Английский', ukr: 'Украинский', bel: 'Белорусский',
        deu: 'Немецкий', fra: 'Французский', spa: 'Испанский', ita: 'Итальянский',
        pol: 'Польский', ces: 'Чешский', nld: 'Нидерландский', por: 'Португальский',
        swe: 'Шведский', tur: 'Турецкий', jpn: 'Японский', zho: 'Китайский',
        kor: 'Корейский', ara: 'Арабский', heb: 'Иврит', lat: 'Латинский', und: '—',
    };

    function humanSize(bytes) {
        if (!bytes) return '';
        const mb = bytes / 1048576;
        return (mb >= 1 ? mb.toFixed(1) : (bytes / 1024).toFixed(0)) + (mb >= 1 ? ' МБ' : ' КБ');
    }

    function year(value) {
        const m = String(value || '').match(/(\d{4})/);
        return m ? m[1] : '';
    }

    /* -------------------------------------------------------------- cards */

    function cardHtml(book) {
        const [c1, c2] = colors(book.id);
        const badge = book.formats && book.formats.length
            ? `<span class="card-badge">${esc(book.formats.join(' · '))}</span>`
            : '';
        const inner = book.hasCover
            ? `<img src="${esc(book.cover)}" alt="" loading="lazy" decoding="async">`
            : `<span class="initials">${esc(initials(book.title))}</span>`;
        const empty = book.hasCover ? '' : ' is-empty';
        const style = book.hasCover ? '' : ` style="--c1:${c1};--c2:${c2}"`;
        const authors = (book.authors || []).join(', ') || 'Без автора';

        return `
        <article class="card">
            <a href="#book-${book.id}" data-book="${book.id}">
                <div class="card-cover${empty}"${style}>${inner}${badge}</div>
                <div class="card-body">
                    <h3 class="card-title">${esc(book.title)}</h3>
                    <p class="card-author">${esc(authors)}</p>
                </div>
            </a>
        </article>`;
    }

    function skeletonHtml(n) {
        let out = '';
        for (let i = 0; i < n; i += 1) {
            out += `<article class="card"><div class="sk"><div class="card-cover"></div>
                <div class="card-body"><div class="card-title"></div><div class="card-author"></div></div></div></article>`;
        }
        return out;
    }

    /* --------------------------------------------------------------- head */

    function facetName(kind, id) {
        if (!st.facets) return kind === 'author' ? 'Автор' : 'Жанр';
        const list = kind === 'author' ? st.facets.authors : st.facets.tags;
        const hit = list.find((x) => Number(x.id) === Number(id));
        return hit ? hit.name : (kind === 'author' ? 'Автор' : 'Жанр');
    }

    function updateHead() {
        const n = st.total;
        const count = `${n} ${plural(n, ['книга', 'книги', 'книг'])}`;
        let title = 'Все книги';
        let sub = count;

        if (st.q) {
            title = 'Поиск';
            sub = `«${st.q}» — ${count}`;
        } else if (st.view === 'recent') {
            title = 'Недавние поступления';
            sub = count;
        } else if (st.view === 'author') {
            title = facetName('author', st.id);
            sub = count;
        } else if (st.view === 'tag') {
            title = facetName('tag', st.id);
            sub = `Жанр · ${count}`;
        }

        el.title.textContent = title;
        el.subtitle.textContent = sub;
        document.title = (st.view === 'all' && !st.q)
            ? 'Библиотека NAS542'
            : `${title} — Библиотека NAS542`;
    }

    function syncRail() {
        document.querySelectorAll('.rail-link[data-view]').forEach((a) => {
            const active = !st.q && a.dataset.view === st.view;
            a.classList.toggle('active', active);
        });
        document.querySelectorAll('[data-author]').forEach((a) => {
            a.classList.toggle('active', !st.q && st.view === 'author' && Number(a.dataset.author) === Number(st.id));
        });
        document.querySelectorAll('[data-tag]').forEach((a) => {
            a.classList.toggle('active', !st.q && st.view === 'tag' && Number(a.dataset.tag) === Number(st.id));
        });
    }

    /* --------------------------------------------------------------- data */

    function showState(html) {
        el.state.hidden = false;
        el.state.innerHTML = html;
    }

    function hideState() {
        el.state.hidden = true;
        el.state.innerHTML = '';
    }

    async function loadFacets() {
        if (st.facets) return st.facets;
        const res = await fetch(`${API}?action=facets`, { credentials: 'same-origin' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        st.facets = await res.json();

        el.countAll.textContent = st.facets.total;
        el.authors.innerHTML = (st.facets.authors || []).map((a) => `
            <a class="rail-link" href="#author-${a.id}" data-author="${a.id}">
                <span>${esc(a.name)}</span><span class="count">${a.count}</span>
            </a>`).join('');

        el.tags.innerHTML = (st.facets.tags || []).slice(0, 14).map((t) => `
            <a class="chip" href="#tag-${t.id}" data-tag="${t.id}" title="${esc(tagLabel(t.name))}">
                <span class="label">${esc(tagLabel(t.name))}</span> <span class="n">${t.count}</span>
            </a>`).join('');

        syncRail();
        return st.facets;
    }

    async function loadBooks({ reset = false } = {}) {
        if (st.loading) return;
        if (!reset && st.done) return;

        st.loading = true;
        if (reset) {
            st.offset = 0;
            st.done = false;
            st.books = [];
            st.rendered = 0;
            hideState();
            el.grid.innerHTML = skeletonHtml(12);
        }

        const seq = ++st.seq;
        const params = new URLSearchParams({
            action: 'list',
            view: st.view === 'recent' ? 'recent' : 'all',
            sort: st.sort,
            offset: String(st.offset),
            limit: String(PAGE),
        });
        if (st.q) params.set('q', st.q);
        if (st.view === 'author') params.set('author', st.id);
        if (st.view === 'tag') params.set('tag', st.id);

        try {
            const res = await fetch(`${API}?${params}`, { credentials: 'same-origin' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            if (seq !== st.seq) return;

            st.total = data.total;
            st.offset = data.offset + data.books.length;
            st.done = data.books.length === 0 || st.offset >= data.total;

            if (reset) {
                el.grid.innerHTML = '';
                st.books = data.books;
                st.rendered = 0;
            } else {
                st.books = st.books.concat(data.books);
            }

            el.grid.insertAdjacentHTML('beforeend', st.books.slice(st.rendered).map(cardHtml).join(''));
            st.rendered = st.books.length;

            updateHead();

            if (!st.total) {
                showState(`<h2>Ничего не найдено</h2>
                    <p>Попробуйте изменить запрос или сбросить фильтры.</p>
                    <a class="btn" href="#/">Сбросить фильтры</a>`);
            }
        } catch (err) {
            el.grid.innerHTML = '';
            showState(`<h2>Не удалось загрузить каталог</h2>
                <p>${esc(err.message)}</p>
                <button class="btn" type="button" onclick="location.reload()">Повторить</button>`);
        } finally {
            st.loading = false;
        }
    }

    /* -------------------------------------------------------------- modal */

    function formatActions(book) {
        const buttons = [];
        (book.formats || []).forEach((f) => {
            buttons.push(`<a class="btn${buttons.length === 0 ? ' btn-primary' : ''}"
                href="${esc(API)}?action=download&id=${book.id}&data=${f.id}">Скачать ${esc(f.format)}</a>`);
        });
        const readable = (book.formats || []).find((f) => f.reader);
        if (readable) {
            buttons.push(`<a class="btn" href="${esc(readable.reader)}" target="_blank" rel="noopener">Читать онлайн</a>`);
        }
        return buttons.join('');
    }

    function renderBook(book) {
        const [c1, c2] = colors(book.id);
        const cover = book.hasCover
            ? `<div class="m-cover"><img src="${esc(book.cover)}" alt=""></div>`
            : `<div class="m-cover is-empty" style="--c1:${c1};--c2:${c2}">${esc(initials(book.title))}</div>`;

        const authors = (book.authors || []).length
            ? book.authors.map((a) => `<a href="#author-${a.id}">${esc(a.name)}</a>`).join(', ')
            : 'Без автора';

        const tags = (book.tags || []).map((t) =>
            `<a class="chip" href="#tag-${t.id}" title="${esc(tagLabel(t.name))}">
                <span class="label">${esc(tagLabel(t.name))}</span></a>`).join('');

        const desc = plain(book.description);
        const descHtml = desc
            ? desc.split(/\n{2,}/).map((p) => `<p>${esc(p)}</p>`).join('')
            : '<p>Описание не добавлено.</p>';

        const meta = [];
        if (book.publisher) meta.push(['Издательство', book.publisher]);
        if (year(book.pubdate)) meta.push(['Год', year(book.pubdate)]);
        if (book.language) meta.push(['Язык', LANGS[book.language] || book.language]);
        if (book.series) meta.push(['Серия', book.series]);
        const sizes = (book.formats || []).map((f) => `${f.format}${f.size ? ' · ' + humanSize(f.size) : ''}`);
        if (sizes.length) meta.push(['Файлы', sizes.join(', ')]);

        const metaHtml = meta.length
            ? `<dl class="m-meta">${meta.map(([k, v]) =>
                `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`
            : '';

        el.modalBody.innerHTML = `
            ${cover}
            <div class="m-info">
                <h2 class="m-title" id="m-title">${esc(book.title)}</h2>
                <p class="m-authors">${authors}</p>
                ${tags ? `<div class="m-tags">${tags}</div>` : ''}
                <div class="m-desc">${descHtml}</div>
                ${metaHtml}
                <div class="m-actions">${formatActions(book)}</div>
            </div>`;
    }

    async function openBook(id, push = true) {
        const seq = ++st.bookSeq;
        el.modalBody.innerHTML = `<div class="m-cover"></div><div class="m-info">
            <div class="sk"><div class="card-title"></div><div class="card-author"></div></div></div>`;
        el.modal.hidden = false;
        document.body.style.overflow = 'hidden';
        if (push && location.hash !== `#book-${id}`) {
            history.pushState({ book: id }, '', `#book-${id}`);
        }

        try {
            const res = await fetch(`${API}?action=book&id=${id}`, { credentials: 'same-origin' });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const book = await res.json();
            if (seq !== st.bookSeq) return;
            renderBook(book);
        } catch (err) {
            el.modalBody.innerHTML = `<p class="m-desc">Не удалось открыть книгу (${esc(err.message)}).</p>`;
        }
    }

    function viewHash() {
        if (st.q) return `#search/${encodeURIComponent(st.q)}`;
        if (st.view === 'author') return `#author-${st.id}`;
        if (st.view === 'tag') return `#tag-${st.id}`;
        if (st.view === 'recent') return '#recent';
        return '#/';
    }

    function closeModal() {
        if (el.modal.hidden) return;
        el.modal.hidden = true;
        document.body.style.overflow = '';
        if (location.hash.startsWith('#book-')) {
            history.replaceState(null, '', viewHash());
        }
    }

    /* ------------------------------------------------------------- router */

    function parseHash() {
        const hash = location.hash.replace(/^#\/?/, '');
        if (!hash) return { view: 'all' };
        if (hash === 'recent') return { view: 'recent' };

        let m = hash.match(/^author-(\d+)$/);
        if (m) return { view: 'author', id: Number(m[1]) };

        m = hash.match(/^tag-(\d+)$/);
        if (m) return { view: 'tag', id: Number(m[1]) };

        m = hash.match(/^book-(\d+)$/);
        if (m) return { view: 'book', id: Number(m[1]) };

        m = hash.match(/^search\/(.*)$/);
        if (m) return { view: 'search', q: decodeURIComponent(m[1]) };

        return { view: 'all' };
    }

    function applyRoute() {
        const route = parseHash();

        if (route.view === 'book') {
            openBook(route.id, false);
            return;
        }

        closeModal();
        st.view = route.view === 'search' ? 'all' : route.view;
        st.id = route.id || null;
        st.q = route.view === 'search' ? route.q : '';
        el.q.value = st.q;
        syncRail();
        window.scrollTo(0, 0);
        loadBooks({ reset: true });
    }

    /* --------------------------------------------------------------- init */

    function closeNav() {
        document.body.classList.remove('nav-open');
    }

    el.q.addEventListener('input', () => {
        clearTimeout(el.q._t);
        el.q._t = setTimeout(() => {
            const value = el.q.value.trim();
            st.q = value;
            history.replaceState(null, '', value ? `#search/${encodeURIComponent(value)}` : viewHash());
            syncRail();
            loadBooks({ reset: true });
        }, 260);
    });

    el.searchForm.addEventListener('submit', (e) => e.preventDefault());

    el.sort.value = st.sort;
    el.sort.addEventListener('change', () => {
        st.sort = el.sort.value;
        localStorage.setItem('nas.sort', st.sort);
        loadBooks({ reset: true });
    });

    el.grid.addEventListener('click', (e) => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
        const link = e.target.closest('[data-book]');
        if (!link) return;
        e.preventDefault();
        openBook(Number(link.dataset.book));
    });

    el.modal.addEventListener('click', (e) => {
        if (e.target.closest('[data-close]')) {
            closeModal();
            return;
        }
        const link = e.target.closest('a[href^="#author-"], a[href^="#tag-"]');
        if (link) {
            closeModal();
        }
    });

    el.rail.addEventListener('click', (e) => {
        if (e.target.closest('a')) closeNav();
    });
    el.filters.addEventListener('click', () => document.body.classList.toggle('nav-open'));
    el.railBackdrop.addEventListener('click', closeNav);

    document.addEventListener('keydown', (e) => {
        const tag = (document.activeElement && document.activeElement.tagName) || '';
        if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) {
            e.preventDefault();
            el.q.focus();
            el.q.select();
        }
        if (e.key === 'Escape') {
            if (!el.modal.hidden) closeModal();
            else closeNav();
        }
    });

    const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting) && !st.done) {
            loadBooks();
        }
    }, { rootMargin: '700px 0px' });
    observer.observe(el.sentinel);

    window.addEventListener('hashchange', applyRoute);
    window.addEventListener('popstate', applyRoute);

    function applyTheme(theme) {
        document.documentElement.dataset.theme = theme;
        localStorage.setItem('nas.theme', theme);
        const meta = document.querySelector('meta[name="theme-color"]');
        if (meta) meta.setAttribute('content', theme === 'dark' ? '#101114' : '#f7f6f3');
    }

    const savedTheme = localStorage.getItem('nas.theme');
    applyTheme(savedTheme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));

    $('#theme').addEventListener('click', () => {
        applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
    });

    loadFacets()
        .catch(() => {})
        .then(() => applyRoute());
})();
