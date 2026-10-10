/* Hover tooltips for the slides. Data comes from window.TT (injected by build.py, see data/tooltips.json). */
(function () {
  var TT = window.TT || {};
  var BUILD = window.TTBUILD || '';
  var box = document.createElement('div');
  box.id = 'tt';
  document.body.appendChild(box);

  function esc(s) {
    return String(s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; });
  }
  function para(s) { return esc(s).replace(/\n/g, '<br>'); }
  function two(l, r) {
    if (!l && !r) return '';
    return '<div class="tt-two"><span>' + esc(l || '') + '</span><span>' + esc(r || '') + '</span></div>';
  }

  function render(e, src) {
    var h = '<div class="tt-head"><img src="' + src + '" alt=""><div class="tt-title">';
    var foot = '';
    if (e.k === 'spell') {
      h += '<b>' + esc(e.n) + '</b>' + (e.r ? '<i>' + esc(e.r) + '</i>' : '') + '</div></div>';
      h += two(e.cost, e.range) + two(e.cast, e.cd);
      h += '<div class="tt-desc">' + para(e.d) + '</div>';
      if (e.lvl > 1) h += '<div class="tt-req">Requires level ' + e.lvl + '</div>';
      foot = 'WoW Forever client data &middot; build ' + esc(BUILD);
    } else if (e.k === 'talent') {
      h += '<b>' + esc(e.n) + '</b></div></div>';
      h += '<div class="tt-rank">' + esc(e.rk) + '</div>';
      if (e.need) h += '<div class="tt-req red">Requires ' + e.need + ' points in ' + esc(e.tree) + ' Talents</div>';
      (e.req || []).forEach(function (r) { h += '<div class="tt-req red">Requires ' + esc(r) + '</div>'; });
      h += '<div class="tt-desc">' + para(e.d) + '</div>';
      if (e.next) h += '<div class="tt-next">Next rank:</div><div class="tt-desc">' + para(e.next) + '</div>';
      foot = 'talents.standards.gg';
    } else if (e.k === 'racial') {
      h += '<b>' + esc(e.n) + '</b><i>' + esc(e.race) + (e.passive ? ' &middot; Passive' : ' &middot; Racial') + '</i></div></div>';
      if (e.cd) h += two('', e.cd + ' cooldown');
      h += '<div class="tt-desc">' + para(e.d) + '</div>';
      foot = 'talents.standards.gg';
    } else if (e.k === 'item') {
      h += '<b class="q' + (e.q || 1) + '">' + esc(e.n) + '</b></div></div>';
      if (e.stack > 1) h += '<div class="tt-req">Max stack: ' + e.stack + '</div>';
      if (e.lvl) h += '<div class="tt-req">Requires level ' + e.lvl + '</div>';
      h += '<div class="tt-use"><span>Use:</span> ' + para(e.use) + '</div>';
      foot = 'WoW Forever client data &middot; build ' + esc(BUILD);
    }
    return h + '<div class="tt-foot">' + foot + '</div>';
  }

  function place(ev) {
    var pad = 22, w = box.offsetWidth, hgt = box.offsetHeight;
    var vw = window.innerWidth, vh = window.innerHeight;
    var x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + w > vw - 8) x = Math.max(8, ev.clientX - pad - w);
    if (y + hgt > vh - 8) y = Math.max(8, vh - hgt - 8);
    box.style.left = x + 'px';
    box.style.top = y + 'px';
  }

  function over(ev) {
    var t = ev.target.closest ? ev.target.closest('[data-tt]') : null;
    if (!t) return;
    var e = TT[t.getAttribute('data-tt')];
    if (!e) return;
    var img = t.querySelector('img');
    box.innerHTML = render(e, img ? img.getAttribute('src') : '');
    box.classList.add('on');
    place(ev);
  }
  function move(ev) {
    if (box.classList.contains('on')) place(ev);
  }
  function out(ev) {
    var t = ev.target.closest ? ev.target.closest('[data-tt]') : null;
    if (t) box.classList.remove('on');
  }
  document.addEventListener('mouseover', over);
  document.addEventListener('mousemove', move);
  document.addEventListener('mouseout', out);
  document.addEventListener('touchstart', function (ev) {
    var t = ev.target.closest ? ev.target.closest('[data-tt]') : null;
    if (!t) { box.classList.remove('on'); return; }
    over({ target: t, clientX: ev.touches[0].clientX, clientY: ev.touches[0].clientY });
  }, { passive: true });

  var marked = document.querySelectorAll('[data-tt]');
  for (var i = 0; i < marked.length; i++) marked[i].style.cursor = 'help';
})();
