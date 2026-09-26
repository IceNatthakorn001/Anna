(function () {
  var root = document.documentElement;

  // theme toggle
  var themeBtn = document.getElementById('themeBtn');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var cur = root.dataset.theme ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = cur === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
  });

  // reading progress
  var bar = document.getElementById('progress');
  function onScroll() {
    var h = document.body.scrollHeight - innerHeight;
    if (bar) bar.style.width = (h > 0 ? (scrollY / h) * 100 : 0) + '%';
  }
  addEventListener('scroll', onScroll, { passive: true });

  // mobile TOC
  var toc = document.getElementById('toc');
  var tocToggle = document.getElementById('tocToggle');
  if (toc && tocToggle) {
    tocToggle.addEventListener('click', function () { toc.classList.toggle('open'); });
    toc.addEventListener('click', function (e) { if (e.target.tagName === 'A' && e.target.hash) toc.classList.remove('open'); });
  }

  // active section highlight
  var links = toc ? Array.prototype.slice.call(toc.querySelectorAll('ol a')) : [];
  if (links.length && 'IntersectionObserver' in window) {
    var map = {};
    links.forEach(function (a) { map[decodeURIComponent(a.hash.slice(1))] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && map[en.target.id]) {
          links.forEach(function (l) { l.classList.remove('active'); });
          map[en.target.id].classList.add('active');
          var a = map[en.target.id];
          if (a.scrollIntoView && innerWidth > 900) {
            var box = toc.getBoundingClientRect(), r = a.getBoundingClientRect();
            if (r.top < box.top || r.bottom > box.bottom) toc.scrollTop += r.top - box.top - 80;
          }
        }
      });
    }, { rootMargin: '-70px 0px -70% 0px' });
    document.querySelectorAll('.prose h2[id]').forEach(function (h) { obs.observe(h); });
  }

  // image lightbox
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.tagName === 'IMG' && t.closest('.prose')) {
      var lb = document.createElement('div');
      lb.className = 'lightbox';
      var img = document.createElement('img');
      img.src = t.src; img.alt = t.alt;
      lb.appendChild(img);
      lb.addEventListener('click', function () { lb.remove(); });
      document.body.appendChild(lb);
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { var lb = document.querySelector('.lightbox'); if (lb) lb.remove(); }
  });

  // home search
  var q = document.getElementById('q'), results = document.getElementById('results');
  if (q && results && window.SEARCH_INDEX) {
    q.addEventListener('input', function () {
      var term = q.value.trim().toLowerCase();
      results.innerHTML = '';
      if (!term) return;
      var hits = [];
      window.SEARCH_INDEX.forEach(function (l) {
        if (l.t.toLowerCase().indexOf(term) !== -1) hits.push({ l: l, h: null });
        l.h.forEach(function (h) { if (h.toLowerCase().indexOf(term) !== -1) hits.push({ l: l, h: h }); });
      });
      hits.slice(0, 30).forEach(function (x) {
        var li = document.createElement('li'), a = document.createElement('a');
        a.href = x.l.u;
        var small = document.createElement('small');
        small.textContent = x.l.s + ' · ' + x.l.t;
        a.textContent = x.h || x.l.t;
        a.appendChild(small);
        li.appendChild(a); results.appendChild(li);
      });
      if (!hits.length) results.innerHTML = '<li><a>ไม่พบหัวข้อที่ค้นหา</a></li>';
    });
  }
})();
