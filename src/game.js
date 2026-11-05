(function(){
'use strict';
const DATA = /*DATA*/;
const MEDIA = /*MEDIA*/;                           // mode aidé : drapeaux des pays (geo.html)
const INFO = /*INFO*/;                             // mode exploration : fiches des pays / des départements
const PHOTOS = /*PHOTOS*/;                         // mode exploration : une photo par pays / par département (avec crédit)
const CAPS = /*CAPS*/;                              // quiz des capitales : { code du pays : capitale } (data/capitales.json)
const TIME = 60, MIN_PX2 = 50, KEY = 'jeuxexplorateurs.v1';
const PAGE = document.body.dataset.page;          // 'home' | 'geoh' | 'calc' | 'anah' | 'geo' | 'fra' | 'cap' | 'eau' | 'org' | 'cm2' | 'os5' | 'ske' | 'add' | 'sub' | 'mul' : une page HTML par écran principal
const HOME = 'index.html#menu';                  // menu principal, sans repasser par le choix du joueur
// Un élément absent de la page (ex. la carte sur une page de calcul) est remplacé par un élément détaché : le code commun n'a pas à tester sa présence.
const $ = id => document.getElementById(id) || document.createElement('div');
const svg = $('map'), mapwrap = $('mapwrap');
function el(tag, cls, text){ const e = document.createElement(tag); if(cls) e.className = cls; if(text != null) e.textContent = text; return e; }
const fmt = n => Number.isInteger(n) ? String(n) : String(n).replace('.', ',');   // les points du mode aidé valent 0,5
const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1));

/* ---------- Définition des jeux ---------- */
const GAMES = {
  geo: {id:'geo', mode:'geo', ask:'Trouve', assistHint:4, name:'Géo Explorateurs', short:'Géo', emoji:'🌍', def:'monde',
    one:'pays trouvé', many:'pays trouvés', b1:'pays', bn:'pays',
    levels:[
      {k:'europe',    n:'Europe',       e:'🏰', c:'#B8A9F2', reg:['E']},
      {k:'asie',      n:'Asie',         e:'🐼', c:'#FFD97D', reg:['A']},
      {k:'afrique',   n:'Afrique',      e:'🦁', c:'#FFB48A', reg:['F']},
      {k:'ameriques', n:'Amériques',    e:'🦜', c:'#93D8A0', reg:['M']},
      {k:'monde',     n:'Monde entier', e:'🌍', c:'#8FD3FF', reg:['E','A','F','M','O']}
    ]},
  fra: {id:'fra', mode:'geo', ask:'Trouve le département', minpx:100, hintAfter:4, name:'Départements de France', short:'Départements', emoji:'🗺️', def:'france',
    one:'département trouvé', many:'départements trouvés', b1:'département', bn:'départements',
    levels:[{k:'france', n:'Toute la France', e:'🇫🇷', c:'#8FD3FF', reg:['E','A','F','M']}]},
  eau: {id:'eau', mode:'geo', ask:'Trouve', minpx:1, keepOrder:true, noAssist:true, name:'Eaux et montagnes', short:'Eaux et montagnes', emoji:'🏞️',
    one:'lieu trouvé', many:'lieux trouvés', b1:'lieu', bn:'lieux',
    levels:[{k:'eaux', n:'Toute la France', e:'🏞️', c:'#8FD3FF', reg:['W']}]},
  cap: {id:'cap', mode:'qcm', noAssist:true, name:'Capitales du monde', short:'Capitales', emoji:'🏛️', def:'monde',
    one:'capitale trouvée', many:'capitales trouvées', b1:'capitale', bn:'capitales',
    levels:[
      {k:'decouverte', n:'Découverte',   e:'🌱', c:'#93D8A0', zone:'monde',  codes:['FRA','ITA','ESP','DEU','GBR','PRT','BEL','CHE','NLD','GRC','IRL','AUT','SWE','USA','CAN','MEX','BRA','ARG','CHN','JPN','IND','EGY','MAR','AUS']},
      {k:'europe',     n:'Europe',       e:'🏰', c:'#B8A9F2', zone:'europe', reg:['E']},
      {k:'monde',      n:'Monde entier', e:'🌍', c:'#8FD3FF', zone:'monde',  reg:['E','A','F','M','O']}
    ]},
  org: {id:'org', mode:'geo', ask:'Trouve', minpx:1, noAssist:true, keepOrder:true, direct:true, exit:'anatomie.html', name:'Les organes', short:'Organes', emoji:'🧠',
    one:'organe trouvé', many:'organes trouvés', b1:'organe', bn:'organes',
    levels:[{k:'tous', n:'Tous les organes', e:'🧠', c:'#F7A8C8', reg:['A','B','C']}]},
  cm2: {id:'cm2', mode:'geo', ask:'Situe', minpx:1, noAssist:true, keepOrder:true, direct:true, exit:'anatomie.html', name:'Situer les organes', short:'Organes CM2', emoji:'🔬',
    one:'organe situé', many:'organes situés', b1:'organe', bn:'organes',
    levels:[{k:'tous', n:'Tous les organes', e:'🔬', c:'#B8A9F2', reg:['A']}]},
  os5: {id:'os5', mode:'geo', ask:'Situe', minpx:1, noAssist:true, keepOrder:true, direct:true, exit:'anatomie.html', name:'Situer les os (5ème)', short:'Os 5ème', emoji:'🦴',
    one:'os situé', many:'os situés', b1:'os', bn:'os',
    levels:[{k:'tous', n:'Tout le squelette', e:'🦴', c:'#E8D7B4', reg:['A']}]},
  ske: {id:'ske', mode:'geo', ask:'Trouve', minpx:1, noAssist:true, keepOrder:true, direct:true, exit:'anatomie.html', name:'Le squelette', short:'Squelette', emoji:'💀',
    one:'os trouvé', many:'os trouvés', b1:'os', bn:'os',
    levels:[{k:'tous', n:'Tout le squelette', e:'💀', c:'#E8D7B4', reg:['A','B','C']}]},
  add: {id:'add', mode:'math', name:'Additions', short:'Additions', emoji:'➕', sign:'+', color:'#93D8A0',
    one:'addition réussie', many:'additions réussies', b1:'addition', bn:'additions',
    levels:[
      {k:'dix',    n:'Découverte', sub:'Sommes jusqu’à 10', e:'🌱', min:2,  max:10, dots:true},
      {k:'vingt',  n:'Super',      sub:'Sommes jusqu’à 20', e:'🌟', min:6,  max:20},
      {k:'trente', n:'Champion',   sub:'Sommes jusqu’à 30', e:'🚀', min:11, max:30}
    ]},
  sub: {id:'sub', mode:'math', name:'Soustractions', short:'Soustractions', emoji:'➖', sign:'−', color:'#7FC8F8',
    one:'soustraction réussie', many:'soustractions réussies', b1:'soustraction', bn:'soustractions',
    levels:[
      {k:'dix',    n:'Découverte', sub:'Nombres jusqu’à 10', e:'🌱', min:3,  max:10, dots:true},
      {k:'vingt',  n:'Super',      sub:'Nombres jusqu’à 20', e:'🌟', min:8,  max:20},
      {k:'trente', n:'Champion',   sub:'Nombres jusqu’à 30', e:'🚀', min:15, max:30}
    ]},
  mul: {id:'mul', mode:'math', name:'Multiplications', short:'Multiplications', emoji:'✖️', sign:'×', color:'#F7A8C8',
    one:'multiplication réussie', many:'multiplications réussies', b1:'multiplication', bn:'multiplications',
    levels:[
      {k:'t1', n:'Découverte', sub:'Tables de 2, 5 et 10', e:'🌱', tables:[2,5,10],            bmin:1, bmax:10},
      {k:'t2', n:'Super',      sub:'Tables de 2 à 5',      e:'🌟', tables:[2,3,4,5],           bmin:2, bmax:10},
      {k:'t3', n:'Champion',   sub:'Tables de 2 à 10',     e:'🚀', tables:[2,3,4,5,6,7,8,9,10], bmin:2, bmax:10}
    ]}
};
const defLevel = G => G.def || G.levels[0].k;
const levelOf = (G, k) => G.levels.find(l => l.k === k);

/* ---------- Stockage (localStorage avec repli mémoire) ---------- */
// Version « un seul fichier » (jeux-explorateurs.html) : les pages sont embarquées dans le fichier et échangées sans changer d'adresse
// (utile quand le téléphone/la tablette n'ouvre qu'un fichier isolé et ne retrouve pas les autres pages).
const NAV = window.__jxNav;                          // défini seulement par le fichier tout-en-un
const goTo = (url, replace) => NAV ? NAV(url) : (replace ? location.replace(url) : (location.href = url));
const HASH = NAV ? (window.__jxHash || '') : location.hash;
if(NAV) document.addEventListener('click', e => {
  const a = e.target.closest && e.target.closest('a[href]');
  if(a && !/^(https?:|#)/.test(a.getAttribute('href'))){ e.preventDefault(); NAV(a.getAttribute('href')); }
});
if(window.__jxStop) window.__jxStop();               // arrête les minuteries de la page précédente
const mem = window.__jxMem || (window.__jxMem = {}); // repli mémoire conservé d'une page à l'autre
const store = {
  get(k, d){ try{ const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; }catch(e){ return k in mem ? mem[k] : d; } },
  set(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){ mem[k] = v; } }
};
const scores = () => store.get(KEY, {});
const bkey = (gid, lk) => gid + ':' + lk;
const bestOf = (gid, lk) => (scores()[bkey(gid, lk)] || []).reduce((m, e) => Math.max(m, e.s), 0);

// Reprise des scores des anciens fichiers (jeu des pays, additions) s'ils existent sur cet ordinateur
(function migrate(){
  if(store.get(KEY + '.migrated', false)) return;
  const all = scores(); let changed = false;
  const take = (oldKey, prefix) => {
    const o = store.get(oldKey, null);
    if(o && typeof o === 'object') Object.keys(o).forEach(k => {
      if(Array.isArray(o[k]) && !all[prefix + k]){ all[prefix + k] = o[k]; changed = true; }
    });
  };
  take('geoexplorateurs.v1', 'geo:');
  take('superadditions.v1', 'add:');
  if(changed) store.set(KEY, all);
  const nm = store.get('geoexplorateurs.v1.name', '') || store.get('superadditions.v1.name', '');
  if(nm && !store.get(KEY + '.name', '')) store.set(KEY + '.name', nm);
  store.set(KEY + '.migrated', true);
})();

/* ---------- Joueurs ---------- */
const PKEY = KEY + '.players', CKEY = KEY + '.player';
const players = () => store.get(PKEY, []);
// Les anciennes versions ne gardaient que le dernier prénom : on le reprend comme premier joueur
(function(){ const old = store.get(KEY + '.name', ''); if(old && !players().length) store.set(PKEY, [old]); })();
let player = store.get(CKEY, '');
let assist = !!store.get(KEY + '.assist', false);      // mode aidé des jeux de géographie
if(!players().includes(player)) player = '';
if(PAGE !== 'home' && !player) goTo('index.html', true);   // pas de joueur choisi : retour au choix du joueur
function setPlayer(n){ player = n; store.set(CKEY, n); refreshWho(); }
function refreshWho(){ document.querySelectorAll('.who').forEach(w => w.textContent = '👤 ' + player + (w.tagName === 'BUTTON' ? ' · changer' : '')); }
function addPlayer(){
  const inp = $('newName'), name = inp.value.trim().slice(0, 14);
  if(!name) { inp.focus(); return; }
  const list = players(), known = list.find(n => n.toLowerCase() === name.toLowerCase());
  if(!known){ list.push(name); store.set(PKEY, list); }
  inp.value = ''; setPlayer(known || name); enterHome();
}
const AVATARS = ['🦊','🐼','🦁','🐯','🐸','🐙','🦄','🐧','🐨','🦉'], AVCOL = ['#FFD97D','#8FD3FF','#93D8A0','#F7A8C8','#B8A9F2','#FFB48A'];
function buildPlayers(){
  const pl = $('plist'); pl.textContent = '';
  players().forEach((n, i) => {
    const b = el('button', 'zone'); b.style.setProperty('--zc', AVCOL[i % AVCOL.length]);
    b.append(el('div', 'emo', AVATARS[i % AVATARS.length]), el('div', 'zn', n));
    b.addEventListener('click', () => { audio(); setPlayer(n); enterHome(); });
    pl.appendChild(b);
  });
  $('plTagline').textContent = players().length ? 'Qui joue ? Choisis ton prénom, ou ajoute un joueur.' : 'Bienvenue ! Ajoute ton prénom pour commencer.';
}
function enterHome(){ $('hello').textContent = 'Salut ' + player + ' ! À quoi veux-tu jouer ?'; show('home'); }
$('btnAddPlayer').addEventListener('click', addPlayer);
$('newName').addEventListener('keydown', e => { if(e.key === 'Enter') addPlayer(); });
$('btnSwitch').addEventListener('click', () => { buildPlayers(); show('players'); });
// Sur les autres pages de menu, la pastille du joueur renvoie au choix du joueur (index.html sans #menu)
document.querySelectorAll('.who').forEach(w => { if(w.id !== 'btnSwitch') w.addEventListener('click', () => goTo('index.html')); });
refreshWho();

/* ---------- Sons ---------- */
let ac = window.__jxAc || null, muted = !!store.get(KEY + '.muted', false);
function audio(){
  if(!ac){ try{ ac = new (window.AudioContext || window.webkitAudioContext)(); window.__jxAc = ac; }catch(e){} }
  if(ac && ac.state === 'suspended') ac.resume();
  return ac;
}
function beep(freq, t0, dur, type, vol){
  const a = audio(); if(!a || muted) return;
  const o = a.createOscillator(), g = a.createGain(), t = a.currentTime + t0;
  o.type = type || 'sine'; o.frequency.value = freq;
  g.gain.setValueAtTime(0.0001, t);
  g.gain.linearRampToValueAtTime(vol || 0.15, t + 0.012);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  o.connect(g); g.connect(a.destination);
  o.start(t); o.stop(t + dur + 0.03);
}
const sfx = {
  ok(){ beep(660,0,.12); beep(880,.09,.2); },
  ko(){ beep(260,0,.16,'triangle',.18); beep(190,.12,.26,'triangle',.18); },
  key(){ beep(520,0,.04,'sine',.05); },
  tick(){ beep(1000,0,.05,'square',.05); },
  count(){ beep(520,0,.14,'sine',.14); },
  go(){ beep(784,0,.2,'sine',.16); },
  end(){ [523,659,784,1047].forEach((f,i)=>beep(f,i*.13,.28)); }
};
/* ---------- Nouveau record : feu d'artifice (canvas) + texte qui jaillit lettre par lettre ---------- */
let fxRaf = 0, fxTimer = 0, fxEnd = 0;
function boom(){                                     // détonation : bruit court, filtré
  const a = audio(); if(!a || muted || a.state !== 'running') return;
  const len = Math.floor(a.sampleRate * .5), buf = a.createBuffer(1, len, a.sampleRate), d = buf.getChannelData(0);
  for(let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3);
  const s = a.createBufferSource(), f = a.createBiquadFilter(), g = a.createGain();
  s.buffer = buf; f.type = 'lowpass'; f.frequency.value = 600 + Math.random() * 600; g.gain.value = .2;
  s.connect(f); f.connect(g); g.connect(a.destination); s.start();
}
sfx.fanfare = () => { [523, 659, 784, 1047].forEach((f, i) => beep(f, i * .11, .3, 'triangle', .16)); [784, 1047, 1319, 1568].forEach(f => beep(f, .5, .7, 'triangle', .1)); };
function stopFx(){
  cancelAnimationFrame(fxRaf); clearTimeout(fxTimer); clearTimeout(fxEnd); fxRaf = 0;
  const o = $('recordfx'); o.hidden = true; o.classList.remove('out');
}
function recordFx(unit){
  stopFx();
  const ov = $('recordfx'), cv = $('fxCanvas'), calm = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const word = (box, txt, d0) => {
    box.textContent = ''; box.setAttribute('aria-label', txt);
    [...txt].forEach((ch, i) => {
      const s = el('span', 'rl', ch === ' ' ? ' ' : ch); s.setAttribute('aria-hidden', 'true');
      s.style.animationDelay = (d0 + i * .07) + 's, ' + (1.6 + i * .12) + 's'; box.appendChild(s);
    });
  };
  word($('recW1'), 'Nouveau', .2); word($('recW2'), 'Record !', .75);
  $('recSub').textContent = fmt(S.score) + ' ' + unit;
  cv.hidden = calm; ov.hidden = false; ov.classList.remove('out');
  sfx.fanfare();
  ov.onpointerdown = stopFx;                         // un toucher ferme l'animation
  const life = calm ? 3500 : 7000;
  fxEnd = setTimeout(() => { ov.classList.add('out'); fxEnd = setTimeout(stopFx, 700); }, life);
  if(calm) return;
  const dpr = Math.min(2, window.devicePixelRatio || 1), W = innerWidth, H = innerHeight, ctx = cv.getContext('2d');
  cv.width = W * dpr; cv.height = H * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  const rockets = [], parts = [], t0 = performance.now(); let last = t0, nextLaunch = t0 + 100, booms = 0;
  function explode(x, y){
    const hue = rnd(0, 360), n = rnd(60, 90), two = Math.random() < .5;
    for(let i = 0; i < n; i++){
      const a = Math.PI * 2 * i / n + Math.random() * .1, sp = (two && i % 2 ? .55 : 1) * (130 + Math.random() * 110);
      parts.push({x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 1, decay: .5 + Math.random() * .45, h: (hue + (two && i % 2 ? 40 : 0)) % 360, s: 1.6 + Math.random() * 1.8});
    }
    if(booms++ < 8) boom();
  }
  (function frame(now){
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    if(now < t0 + 5200 && now >= nextLaunch){ rockets.push({x: W * (.12 + Math.random() * .76), y: H, ty: H * (.12 + Math.random() * .36), vx: (Math.random() - .5) * 40}); nextLaunch = now + 350 + Math.random() * 350; }
    ctx.globalCompositeOperation = 'destination-out'; ctx.fillStyle = 'rgba(0,0,0,.22)'; ctx.fillRect(0, 0, W, H);   // les traînées s'effacent doucement
    ctx.globalCompositeOperation = 'lighter';
    for(let i = rockets.length - 1; i >= 0; i--){
      const r = rockets[i]; r.y -= H * .95 * dt; r.x += r.vx * dt;
      ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(r.x, r.y, 2.4, 0, 7); ctx.fill();
      if(r.y <= r.ty){ explode(r.x, r.y); rockets.splice(i, 1); }
    }
    for(let i = parts.length - 1; i >= 0; i--){
      const p = parts[i]; p.vy += 170 * dt; p.vx *= .992; p.x += p.vx * dt; p.y += p.vy * dt; p.life -= p.decay * dt;
      if(p.life <= 0){ parts.splice(i, 1); continue; }
      ctx.fillStyle = 'hsla(' + p.h + ',100%,' + (55 + 25 * p.life) + '%,' + p.life + ')';
      ctx.beginPath(); ctx.arc(p.x, p.y, p.s * (.4 + p.life * .6), 0, 7); ctx.fill();
    }
    fxRaf = requestAnimationFrame(frame);
  })(last);
}
function refreshMute(){ document.querySelectorAll('.muteBtn').forEach(b => b.textContent = muted ? '🔇' : '🔊'); }
document.querySelectorAll('.muteBtn').forEach(b => b.addEventListener('click', () => { muted = !muted; store.set(KEY + '.muted', muted); refreshMute(); if(!muted) sfx.count(); }));
refreshMute();

/* ---------- Thème Halloween (manoir hanté) ---------- */
const TKEY = KEY + '.theme';
let theme = store.get(TKEY, 'classic') === 'halloween' ? 'halloween' : 'classic';
let decor = null, ghostTimer = 0;
const DECOR_HTML = '<div class="moon"></div><span class="bat b1">🦇</span><span class="bat b2">🦇</span>'
  + '<div class="fog f1"></div><div class="fog f2"></div>'
  + '<svg class="web" viewBox="0 0 120 120"><g stroke="rgba(255,255,255,.38)" stroke-width="1" fill="none"><path d="M0 0 L120 0 M0 0 L110 40 M0 0 L85 85 M0 0 L40 110 M0 0 L0 120"/>'
  + '<path d="M28 0 Q22 22 0 28 M55 0 Q44 44 0 55 M85 0 Q66 66 0 85 M112 0 Q88 88 0 112"/></g></svg>'
  + '<div class="spider s1"><i></i>🕷️</div><div class="spider s2"><i></i>🕷️</div><div class="spider s3"><i></i>🕷️</div>'
  + '<div class="gleyes e1"></div><div class="gleyes e2"></div><div class="gleyes e3"></div>'
  + '<svg class="manor" viewBox="0 0 400 240" preserveAspectRatio="xMaxYMax meet"><g fill="#06030d">'
  + '<rect x="110" y="120" width="180" height="120"/><polygon points="100,122 200,60 300,122"/>'
  + '<rect x="60" y="90" width="52" height="150"/><polygon points="52,92 86,30 120,92"/>'
  + '<rect x="290" y="105" width="44" height="135"/><polygon points="282,107 312,50 342,107"/>'
  + '<rect x="250" y="60" width="14" height="40"/><rect x="0" y="228" width="400" height="12"/></g>'
  + '<path d="M365 240 V170 M365 192 l-24 -24 M365 182 l28 -30 M393 152 l8 -12 M341 168 l-10 -20" stroke="#06030d" stroke-width="5" fill="none" stroke-linecap="round"/>'
  + '<g fill="#FFC857"><rect class="win" x="135" y="150" width="18" height="26"/><rect class="win" x="247" y="150" width="18" height="26" style="animation-delay:-1.3s"/>'
  + '<rect class="win" x="77" y="120" width="14" height="22" style="animation-delay:-2.6s"/><rect class="win" x="303" y="135" width="12" height="20" style="animation-delay:-.7s"/>'
  + '<circle class="win" cx="200" cy="100" r="10" style="animation-delay:-3.2s"/></g></svg>'
  + '<div class="pk pk1"><i class="glow"></i>🎃</div><div class="pk pk2"><i class="glow"></i>🎃</div>';
// « Ouuuuh » : une voix qui monte puis retombe, avec un vibrato lent. Silencieux tant qu'aucun clic n'a débloqué le son.
function ooh(sec){
  if(!ac || ac.state !== 'running' || muted) return;
  const t = ac.currentTime, d = sec || 2.2;
  const o = ac.createOscillator(), f = ac.createBiquadFilter(), g = ac.createGain(), lfo = ac.createOscillator(), lg = ac.createGain();
  o.type = 'sawtooth';
  o.frequency.setValueAtTime(170, t); o.frequency.linearRampToValueAtTime(290, t + d * .35); o.frequency.linearRampToValueAtTime(200, t + d);
  f.type = 'lowpass'; f.Q.value = 5; f.frequency.setValueAtTime(380, t); f.frequency.linearRampToValueAtTime(820, t + d * .4); f.frequency.linearRampToValueAtTime(300, t + d);
  lfo.frequency.value = 5.5; lg.gain.value = 9; lfo.connect(lg); lg.connect(o.frequency);
  g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.1, t + d * .3); g.gain.linearRampToValueAtTime(0.07, t + d * .65); g.gain.exponentialRampToValueAtTime(0.0001, t + d);
  o.connect(f); f.connect(g); g.connect(ac.destination);
  o.start(t); lfo.start(t); o.stop(t + d + .05); lfo.stop(t + d + .05);
}
// Petite musique de boîte à musique (valse mineure) : jouée seulement dans les menus, une fois le son débloqué par un clic
const NOTE = {A3:220, C4:261.6, E4:329.6, Ab4:415.3, A4:440, B4:493.9, C5:523.3, D5:587.3, Eb5:622.3, E5:659.3};
const PHRASES = [
  [['E5',0],['C5',1],['A4',2],['B4',3],['C5',4],['B4',5],['A4',6],['Ab4',7],['B4',8],['E5',10]],
  [['A4',0],['C5',1],['E5',2],['D5',3],['C5',4],['B4',5],['C5',6],['D5',7],['B4',8],['A4',10]],
  [['E5',0],['Eb5',1],['E5',2],['Eb5',3],['E5',4],['B4',5],['D5',6],['C5',7],['A4',8],['A4',10]]
];
let musicTimer = 0, phraseIx = 0;
function musicTick(){
  clearTimeout(musicTimer);
  if(theme !== 'halloween') return;
  if(!ac || ac.state !== 'running' || muted || $('game').classList.contains('active') || document.hidden){ musicTimer = setTimeout(musicTick, 800); return; }
  const beat = .42, ph = PHRASES[phraseIx++ % PHRASES.length];
  ph.forEach(([n, b]) => beep(NOTE[n] || 622.3, b * beat, 1.1, 'sine', .06));
  [0, 3, 6, 9].forEach(b => { beep(NOTE.A3, b * beat, 1.0, 'triangle', .06); beep(NOTE.E4, (b + 1) * beat, .5, 'triangle', .022); beep(NOTE.C4, (b + 2) * beat, .5, 'triangle', .022); });
  musicTimer = setTimeout(musicTick, 14 * beat * 1000);
}
// Orage lointain : éclair doux (jamais de clignotement rapide) puis grondement
function thunder(){
  if(!ac || ac.state !== 'running' || muted) return;
  const len = Math.floor(ac.sampleRate * 2.6), buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0);
  for(let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2);
  const s = ac.createBufferSource(), f = ac.createBiquadFilter(), g = ac.createGain();
  s.buffer = buf; f.type = 'lowpass'; f.frequency.value = 160; g.gain.value = .85;
  s.connect(f); f.connect(g); g.connect(ac.destination); s.start();
}
let lightTimer = 0, flashEl = null, boltBox = null;
function drawBolt(){                                 // un éclair en zigzag, avec une branche, à une place différente à chaque fois
  const NS = 'http://www.w3.org/2000/svg', pts = [];
  let x = rnd(12, 88), y = 0; pts.push([x, y]);
  while(y < 64){ y += rnd(6, 11); x = Math.max(3, Math.min(97, x + rnd(-9, 9))); pts.push([x, y]); }
  const line = a => 'M' + a.map(p => p[0] + ' ' + p[1]).join(' L');
  const k = rnd(2, pts.length - 3), br = [pts[k]];
  for(let i = 0, bx = pts[k][0], by = pts[k][1]; i < 3; i++){ bx = Math.max(3, Math.min(97, bx + rnd(-3, 12) * (Math.random() < .5 ? -1 : 1))); by += rnd(5, 9); br.push([bx, by]); }
  boltBox.textContent = '';
  [line(pts), line(br)].forEach((d, i) => {
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', d); p.setAttribute('class', i ? 'bolt branch' : 'bolt'); boltBox.appendChild(p);
  });
}
function scheduleLightning(ms){
  clearTimeout(lightTimer);
  lightTimer = setTimeout(() => {
    if(theme === 'halloween' && flashEl && !document.hidden && !$('game').classList.contains('active') && !matchMedia('(prefers-reduced-motion: reduce)').matches){
      // deux éclats espacés d'un peu plus d'un tiers de seconde (jamais plus de 3 par seconde)
      drawBolt();
      flashEl.animate([{opacity:0}, {opacity:.5, offset:.12}, {opacity:.06, offset:.3}, {opacity:.38, offset:.42}, {opacity:0}], {duration: 1300});
      boltBox.animate([{opacity:0}, {opacity:1, offset:.1}, {opacity:.3, offset:.3}, {opacity:1, offset:.4}, {opacity:0}], {duration: 1300});
      setTimeout(thunder, 650);
    }
    scheduleLightning(rnd(9000, 20000));
  }, ms);
}
sfx.spooky = () => { beep(392, 0, .35, 'triangle', .08); beep(311, .25, .4, 'triangle', .08); beep(233, .55, .8, 'triangle', .08); };
// Un fantôme traverse l'écran, ou surgit au milieu en grossissant
function surge(){
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const size = rnd(90, 170), g = el('div', 'ghost', '👻'), dur = rnd(3600, 5200);
  g.style.fontSize = size + 'px'; document.body.appendChild(g);
  let an;
  if(Math.random() < .5){
    const left = Math.random() < .5, x0 = left ? -size * 1.5 : innerWidth + size * .5, x1 = left ? innerWidth + size * .5 : -size * 1.5, fr = [];
    g.style.top = rnd(6, 60) + 'vh';
    for(let i = 0; i <= 8; i++){ const k = i / 8, w = Math.sin(k * Math.PI * 3);
      fr.push({transform:'translate(' + (x0 + (x1 - x0) * k) + 'px,' + (w * 40) + 'px) scaleX(' + (left ? 1 : -1) + ') rotate(' + (w * 8) + 'deg)', opacity: k < .1 || k > .9 ? 0 : .85}); }
    an = g.animate(fr, {duration: dur, easing:'linear'});
  } else {
    g.style.left = rnd(8, 75) + 'vw'; g.style.top = rnd(12, 60) + 'vh';
    an = g.animate([{transform:'scale(.2)', opacity:0}, {transform:'scale(1.1)', opacity:.9, offset:.4}, {transform:'scale(1.7) translateY(-30px)', opacity:0}], {duration: 2600, easing:'ease-out'});
  }
  an.onfinish = () => g.remove();
  ooh(dur / 1000 * .55);
}
function scheduleGhost(ms){
  clearTimeout(ghostTimer);
  ghostTimer = setTimeout(() => {
    if(theme === 'halloween' && !document.hidden && !$('game').classList.contains('active')) surge();   // jamais pendant une partie
    scheduleGhost(rnd(9000, 22000));
  }, ms);
}
function applyTheme(first){
  document.documentElement.dataset.theme = theme;
  if(theme === 'halloween' && !decor){
    decor = el('div'); decor.id = 'decor'; decor.setAttribute('aria-hidden', 'true');
    decor.innerHTML = DECOR_HTML;                     // texte fixe, aucun contenu saisi par un joueur
    document.body.insertBefore(decor, $('app'));
    flashEl = el('div'); flashEl.id = 'flash'; document.body.appendChild(flashEl);
    boltBox = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); boltBox.id = 'boltbox';
    boltBox.setAttribute('viewBox', '0 0 100 100'); boltBox.setAttribute('preserveAspectRatio', 'none'); document.body.appendChild(boltBox);
  }
  document.querySelectorAll('#players .logo .globe, #home .logo .globe, #geoh .logo .globe, #calc .logo .globe').forEach(gl => {
    if(!gl.dataset.orig) gl.dataset.orig = gl.textContent;
    gl.textContent = theme === 'halloween' ? '🎃' : gl.dataset.orig;
  });
  document.querySelectorAll('.themeBtn').forEach(b => b.textContent = theme === 'halloween' ? '☀️ Thème normal' : '🎃 Halloween');
  clearTimeout(ghostTimer); clearTimeout(lightTimer); clearTimeout(musicTimer);
  if(theme === 'halloween'){ scheduleGhost(first ? rnd(6000, 10000) : 1500); scheduleLightning(rnd(4000, 9000)); musicTick(); }
}
document.querySelectorAll('.themeBtn').forEach(b => b.addEventListener('click', () => {
  theme = theme === 'halloween' ? 'classic' : 'halloween'; store.set(TKEY, theme);
  audio(); if(theme === 'halloween') sfx.spooky(); else sfx.count();
  applyTheme(false);
}));
document.addEventListener('pointerdown', () => { if(theme === 'halloween') audio(); }, {once: true});   // débloque le son pour les « ouuuh »
applyTheme(true);

/* ---------- Navigation & menus ---------- */
function show(id){ document.querySelectorAll('.screen').forEach(s => s.classList.toggle('active', s.id === id)); }
function go(id){ buildMenus(); show(id); }
const home = () => goTo(HOME);
const toMenu = () => S.game && S.game.exit ? goTo(S.game.exit) : go('menu');   // jeux sans menu de niveau (anatomie) : retour au sous-menu

function refreshAssist(){
  const b = $('btnAssist'); b.textContent = assist ? '🤝 Mode aidé : oui (points ÷ 2)' : '🤝 Mode aidé : non';
  b.classList.toggle('on', assist); b.setAttribute('aria-pressed', assist);
}
$('btnAssist').addEventListener('click', () => { assist = !assist; store.set(KEY + '.assist', assist); refreshAssist(); sfx.key(); });
function buildMenus(){
  if(GAMES[PAGE] && GAMES[PAGE].mode !== 'math'){
    const G = GAMES[PAGE], zb = $('zones'); zb.textContent = ''; refreshAssist(); zb.classList.toggle('single', G.levels.length === 1);
    G.levels.forEach(z => {
      const b = el('button', 'zone' + (z.k === G.def ? ' world' : ''));
      b.style.setProperty('--zc', z.c);
      const best = bestOf(G.id, z.k);
      b.append(el('div', 'emo', z.e), el('div', 'zn', z.n), el('div', 'rec', best ? '🏅 Record : ' + fmt(best) : 'Pas encore joué'));
      b.addEventListener('click', () => { audio(); startGame(G.id, z.k); });
      zb.appendChild(b);
    });
  } else if(GAMES[PAGE]){
    const G = GAMES[PAGE], ob = $('ops'); ob.textContent = '';
    const card = el('div', 'opcard'); card.style.setProperty('--zc', G.color);
    const head = el('div', 'ophead');
    head.append(el('div', 'opsign', G.sign), el('div', 'opname', G.name));
    card.appendChild(head);
    G.levels.forEach(l => {
      const b = el('button', 'lvl');
      const best = bestOf(G.id, l.k);
      const ln = el('div', 'ln', l.n); ln.appendChild(el('small', null, l.sub));
      b.append(el('span', 'le', l.e), ln, el('span', 'lr', best ? '🏅 ' + best : ''));
      b.addEventListener('click', () => { audio(); startGame(G.id, l.k); });
      card.appendChild(b);
    });
    ob.appendChild(card);
  }
}

/* ---------- Carte : index, vue, zoom, déplacement ---------- */
const byCode = {};
svg.querySelectorAll('path[data-c]').forEach(p => { (byCode[p.dataset.c] = byCode[p.dataset.c] || []).push(p); });
const MAPBOX = DATA.box ? {x0:DATA.box[0], y0:DATA.box[1], x1:DATA.box[2], y1:DATA.box[3]} : {x0:0, y0:0, x1:1000, y1:520};
let zoneView = {x:0,y:0,w:1000,h:520}, view = {x:0,y:0,w:1000,h:520};   // remplacés dès le début d'une partie par le cadrage de la zone
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

function fitView(zone){
  const [x0,y0,x1,y1] = DATA.zones[zone];
  const r = mapwrap.getBoundingClientRect();
  const ar = (r.width / r.height) || 1.6;
  let w = (x1 - x0) * 1.06, h = (y1 - y0) * 1.06;
  const cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
  if(w / h < ar) w = h * ar; else h = w / ar;
  return {x:cx - w/2, y:cy - h/2, w, h};
}
function applyView(){ svg.setAttribute('viewBox', view.x + ' ' + view.y + ' ' + view.w + ' ' + view.h); }
function clampPan(){
  view.x = clamp(view.x, MAPBOX.x0 - view.w * .25, MAPBOX.x1 - view.w * .75);
  view.y = clamp(view.y, MAPBOX.y0 - view.h * .25, MAPBOX.y1 - view.h * .75);
}
function zoomAt(factor, cx, cy){
  const r = svg.getBoundingClientRect();
  const fx = (cx - r.left) / r.width, fy = (cy - r.top) / r.height;
  const nw = clamp(view.w * factor, zoneView.w / 12, zoneView.w);
  const nh = nw * view.h / view.w;
  view = {x: view.x + (view.w - nw) * fx, y: view.y + (view.h - nh) * fy, w:nw, h:nh};
  clampPan(); applyView();
}
function zoomCenter(f){ const r = svg.getBoundingClientRect(); zoomAt(f, r.left + r.width/2, r.top + r.height/2); }
svg.addEventListener('wheel', e => {
  e.preventDefault();
  zoomAt(Math.exp(clamp(e.deltaY, -100, 100) * 0.002), e.clientX, e.clientY);
}, {passive:false});
$('zIn').addEventListener('click', () => zoomCenter(0.7));
$('zOut').addEventListener('click', () => zoomCenter(1/0.7));
$('zReset').addEventListener('click', () => { view = {...zoneView}; applyView(); });

let drag = null, dragMoved = false;
svg.addEventListener('pointerdown', e => {
  if(e.pointerType === 'mouse' && e.button !== 0) return;
  drag = {x:e.clientX, y:e.clientY, vx:view.x, vy:view.y};
  dragMoved = false;
});
window.addEventListener('pointermove', e => {
  if(!drag) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if(!dragMoved && Math.hypot(dx, dy) < 6) return;
  dragMoved = true; svg.classList.add('dragging');
  const k = view.w / svg.getBoundingClientRect().width;
  view.x = drag.vx - dx * k; view.y = drag.vy - dy * k;
  clampPan(); applyView();
});
window.addEventListener('pointerup', () => {
  if(!drag) return;
  drag = null; svg.classList.remove('dragging');
  setTimeout(() => { dragMoved = false; }, 80);
});
window.addEventListener('resize', () => {
  if($('game').classList.contains('active') && S.game && S.game.mode !== 'math'){ zoneView = fitView(S.zoneKey || S.level.zone || S.level.k); view = {...zoneView}; applyView(); }
});

/* ---------- État de partie ---------- */
const S = {game:null, level:null, pool:[], queue:[], cur:null, q:null, typed:'', recent:[], score:0, wrong:0, t0:0, running:false, locked:true, timerId:null, runId:0, saved:false, entry:null, lastSec:99, from:'menu'};
function later(fn, ms){ const id = S.runId; return setTimeout(() => { if(id === S.runId) fn(); }, ms); }
function shuffle(a){ a = a.slice(); for(let i = a.length - 1; i > 0; i--){ const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function setTarget(label, name, cls){
  $('tLabel').textContent = label; $('tName').textContent = name; $('target').className = 'target' + (cls ? ' ' + cls : '');
  const m = PAGE === 'geo' && S.cur && MEDIA[S.cur], f = $('tFlag');            // pays : le drapeau à gauche du nom
  f.hidden = !m; if(m) f.src = m.i || m;
  const ic = $('tIcon'), ps = PAGE === 'eau' && S.cur && byCode[S.cur], cl = ps && ps[0].classList;      // eaux et montagnes : une icône à gauche du nom
  ic.hidden = !cl; if(cl) ic.textContent = cl.contains('mtn') ? '🏔️' : cl.contains('sea') ? '🌊' : cl.contains('lake') ? '💧' : '🏞️';
}
function setScore(){ $('score').textContent = fmt(S.score); }
function setTime(left){
  $('time').textContent = Math.max(0, Math.ceil(left));
  $('barFill').style.width = Math.max(0, left / TIME * 100) + '%';
  $('bar').className = 'bar' + (left <= 5 ? ' danger' : left <= 15 ? ' warn' : '');
  $('timePill').classList.toggle('danger', left <= 5);
}

function startGame(gid, lk){
  stopFx(); S.runId++; clearInterval(S.timerId);
  S.game = GAMES[gid]; S.level = levelOf(S.game, lk);
  S.score = 0; S.wrong = 0; S.saved = false; S.entry = null;
  S.assist = assist && S.game.mode === 'geo' && !S.game.noAssist;
  S.explore = false; $('game').classList.remove('explore');
  hideTip();
  S.running = false; S.locked = true; S.lastSec = 99; S.typed = ''; S.recent = []; S.zoneKey = null;
  const geo = S.game.mode === 'geo', qcm = S.game.mode === 'qcm';
  $('game').dataset.mode = S.game.mode;
  show('game');
  setScore(); setTime(TIME);
  if(qcm){
    unmark(); $('qFlag').hidden = true; $('qChoices').textContent = '';
    zoneView = fitView(S.level.zone); view = {...zoneView}; applyView();
    S.pool = capPool(S.level); S.queue = shuffle(S.pool);
    setTarget('Prépare-toi !', S.level.e + ' ' + S.level.n);
  } else if(geo){
    unmark();
    zoneView = fitView(S.level.k); view = {...zoneView}; applyView();
    const scale = svg.getBoundingClientRect().width / view.w;
    S.pool = eligible(S.level, scale); S.queue = shuffle(S.pool);
    $('btnSkip').disabled = true;
    setTarget('Prépare-toi !', S.level.e + ' ' + S.level.n);
  } else {
    $('qcard').className = 'qcard hide';
    $('hint').textContent = '';
    $('qop').textContent = S.game.sign;
    setTarget('Prépare-toi !', S.game.emoji + ' ' + S.level.n + ' · ' + S.level.sub);
  }
  countdown(() => {
    S.running = true; S.t0 = performance.now();
    if(qcm) nextCapital(); else if(geo) nextTarget(); else nextQuestion();
    S.timerId = setInterval(tick, 100);
  });
}

/* ---------- Mode exploration : pas de chrono, une fiche au survol (ou au toucher) ---------- */
const CONT = {E:'Europe', A:'Asie', F:'Afrique', M:'Amériques', O:'Océanie'};
const FRANCE_KM2 = 551695;
const nf = n => n.toLocaleString('fr-FR');
const up = s => s.charAt(0).toUpperCase() + s.slice(1);
function popText(n){
  if(n >= 1e6){
    const big = n >= 1e9, v = n / (big ? 1e9 : 1e6), t = v >= 10 ? String(Math.round(v)) : v.toFixed(1).replace('.', ',').replace(',0', '');
    return 'environ ' + t + (big ? (v < 2 ? ' milliard' : ' milliards') : (v < 2 ? ' million' : ' millions')) + ' de personnes';
  }
  return 'environ ' + nf(n >= 10000 ? Math.round(n / 1000) * 1000 : n >= 1000 ? Math.round(n / 100) * 100 : n) + ' personnes';
}
function areaText(a, withFrance){
  let s = nf(a < 10 ? a : Math.round(a)).replace('.', ',') + ' km²';
  if(withFrance){
    const r = a / FRANCE_KM2;
    if(r >= 1.5) s += ' (environ ' + (r >= 10 ? nf(Math.round(r)) : r.toFixed(1).replace('.', ',').replace(',0', '')) + ' fois la France)';
    else if(r > 0.67) s += ' (à peu près comme la France)';
    else if(r < 0.002) s += ' (minuscule !)';
    else s += ' (environ ' + nf(Math.round(1 / r)) + ' fois plus petit que la France)';
  }
  return s;
}
function infoRow(dl, label, value){ if(value) dl.append(el('dt', null, label), el('dd', null, value)); }
let infoCode = '';
function hideInfo(){ infoCode = ''; }
function showInfo(code){
  if(code === infoCode) return;
  const c = DATA.countries[code]; if(!c) return;
  infoCode = code;
  const i = INFO[code], ph = PHOTOS[code], geo = PAGE === 'geo', dl = $('infoList'); dl.textContent = '';
  $('infoHint').hidden = true; $('infoBody').hidden = false;
  $('infoName').textContent = c.n;
  const flag = geo && MEDIA[code]; $('infoFlag').hidden = !flag; if(flag) $('infoFlag').src = MEDIA[code];
  $('infoPhoto').hidden = !ph; if(ph) $('infoPhoto').src = ph.i;
  $('infoCredit').textContent = ph ? '📷 ' + (geo ? '' : ph.t + ' · ') + ph.c : '';
  if(i){
    const nb = (i.nb || []).map(k => DATA.countries[k] && DATA.countries[k].n).filter(Boolean);
    if(geo){
      infoRow(dl, 'Capitale', i.cap); infoRow(dl, 'Continent', CONT[c.r]);
      infoRow(dl, 'Habitants', i.pop && popText(i.pop)); infoRow(dl, 'Superficie', i.area && areaText(i.area, code !== 'FRA'));
      infoRow(dl, 'Langues', i.lang && i.lang.slice(0, 4).map(up).join(', ') + (i.lang.length > 4 ? '…' : ''));
      infoRow(dl, 'Monnaie', i.cur && i.cur.map(up).join(', '));
      infoRow(dl, 'Voisins', nb.length ? nb.slice(0, 8).join(', ') + (nb.length > 8 ? '…' : '') : 'aucun voisin par la terre');
    } else {
      infoRow(dl, 'Numéro', code); infoRow(dl, 'Préfecture', i.pref); infoRow(dl, 'Région', i.reg);
      infoRow(dl, 'Habitants', i.pop && popText(i.pop)); infoRow(dl, 'Superficie', i.area && areaText(i.area, false));
      infoRow(dl, 'Voisins', nb.join(', '));
    }
  }
  $('infoFact').textContent = i && i.fact ? '💡 Le savais-tu ? ' + i.fact : (i ? '' : 'Ce territoire n’est pas un pays indépendant.');
  $('infoBox').scrollTop = 0;
}
function exploreAt(e){
  if(!S.explore) return;
  const p = e.target.closest ? e.target.closest('path[data-c]') : null;
  if(p) showInfo(p.dataset.c);                      // dans la mer : on garde la fiche affichée
}
svg.addEventListener('pointermove', exploreAt);
svg.addEventListener('pointerdown', exploreAt);      // sur tablette : on touche un pays pour voir sa fiche
function startExplore(gid){
  S.runId++; clearInterval(S.timerId);
  S.game = GAMES[gid]; S.level = levelOf(S.game, S.game.def);
  S.running = false; S.locked = true; S.assist = false; S.explore = true;
  hideTip(); hideInfo(); unmark();
  $('infoBody').hidden = true; $('infoHint').hidden = false;
  $('game').dataset.mode = 'geo'; $('game').classList.add('explore');
  show('game');
  zoneView = fitView(S.level.k); view = {...zoneView}; applyView();
  setTarget('🔎 Exploration', 'Survole ' + (gid === 'fra' ? 'un département' : 'un pays'));
}
$('btnExplore').addEventListener('click', () => { audio(); startExplore(PAGE); });

function countdown(done){
  const elc = $('count'), steps = ['3','2','1','Go !'];
  let i = 0;
  elc.classList.add('show');
  (function step(){
    const old = $('countTxt');                       // on remplace l'élément pour relancer l'animation
    const fresh = old.cloneNode(false); fresh.id = 'countTxt'; fresh.textContent = steps[i];
    old.parentNode.replaceChild(fresh, old);
    if(i < 3){ sfx.count(); i++; later(step, 700); }
    else { sfx.go(); done(); later(() => elc.classList.remove('show'), 350); }
  })();
}

function tick(){
  if(!S.running) return;
  const left = TIME - (performance.now() - S.t0) / 1000;
  if(left <= 0){ endGame(); return; }
  setTime(left);
  const sec = Math.ceil(left);
  if(sec <= 5 && sec !== S.lastSec){ sfx.tick(); }
  S.lastSec = sec;
}

function bumpScore(){ const pill = $('scorePill'); pill.classList.remove('bump'); void pill.offsetWidth; pill.classList.add('bump'); }

/* ===== Jeu de géographie ===== */
function eligible(level, scale){
  const all = Object.entries(DATA.countries).filter(([k, v]) => v.t && level.reg.includes(v.r));
  let thr = S.game.minpx || MIN_PX2, pool = [];
  while(thr >= 0){
    pool = all.filter(([, v]) => v.a * scale * scale >= thr).map(([k]) => k);
    if(pool.length >= 12 || thr === 0) break;
    thr = Math.max(0, thr - 10);
  }
  return pool;
}
function mark(code, cls){
  const ps = byCode[code] || [];
  ps.forEach(p => { p.classList.add(cls); if(!S.game.keepOrder) p.parentNode.appendChild(p); });   // organes : on garde l'ordre de superposition du dessin
  const dec = ps.length && ps[ps.length - 1].nextElementSibling;           // organes : les détails dessinés par-dessus s'estompent pour que le vert se voie bien
  if(S.game.keepOrder && dec && dec.classList.contains('deco')) dec.classList.add('dim');
}
function unmark(){ clearTimeout(S.hintT); hidePin();  svg.querySelectorAll('.ok,.ko,.show,.gray,.hl').forEach(p => p.classList.remove('ok','ko','show','gray','hl')); svg.querySelectorAll('.deco.dim').forEach(g => g.classList.remove('dim')); }
// Indice des départements : sans clic au bout de 4 s, les zones où le département n'est pas passent en gris
// Pays (mode aidé) : au bout de 4 s, les 2/3 des autres pays de la zone, les plus éloignés du pays demandé, passent en gris
const centers = {};
function centerOf(code){                             // centre du plus grand morceau du pays (la France compte aussi ses îles lointaines : on les ignore)
  if(centers[code]) return centers[code];
  let best = null, area = -1;
  (byCode[code] || []).forEach(p => {
    (p.getAttribute('d').match(/M[^M]+/g) || []).forEach(sub => {          // un sous-tracé par morceau du pays
      const n = sub.match(/-?\d+\.?\d*/g).map(Number); let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      for(let i = 0; i + 1 < n.length; i += 2){ x0 = Math.min(x0, n[i]); x1 = Math.max(x1, n[i]); y0 = Math.min(y0, n[i + 1]); y1 = Math.max(y1, n[i + 1]); }
      const a = (x1 - x0) * (y1 - y0);
      if(a > area){ area = a; best = [(x0 + x1) / 2, (y0 + y1) / 2] }
    });
  });
  return centers[code] = best || [0, 0];
}
function grayFar(){
  const t = centerOf(S.cur), dist = k => { const c = centerOf(k); return Math.hypot(c[0] - t[0], c[1] - t[1]); };
  const others = Object.keys(DATA.countries).filter(k => k !== S.cur && byCode[k] && S.level.reg.includes(DATA.countries[k].r));
  others.sort((a, b) => dist(a) - dist(b));
  others.slice(Math.ceil(others.length / 3)).forEach(k => byCode[k].forEach(p => p.classList.add('gray')));
}
function grayOut(){
  if(S.locked || !S.running) return;
  if(S.game.id === 'geo') grayFar();
  else {
    const zone = DATA.countries[S.cur].r;
    svg.querySelectorAll('path[data-c]').forEach(p => { if(DATA.countries[p.dataset.c].r !== zone) p.classList.add('gray'); });
  }
  $('tLabel').textContent = S.game.ask + ' · 💡 indice';
}
function nextTarget(){
  unmark(); hideTip();
  if(!S.queue.length){                              // nouveau tour : on évite de redemander l'organe qui vient de passer
    S.queue = shuffle(S.pool);
    if(S.queue.length > 1 && S.queue[S.queue.length - 1] === S.cur) S.queue.unshift(S.queue.pop());
  }
  S.cur = S.queue.pop();
  setTarget(S.game.ask, DATA.countries[S.cur].n);
  S.locked = false; $('btnSkip').disabled = false;
  const hs = S.game.hintAfter || (S.assist && S.game.assistHint);        // départements : toujours ; pays : seulement en mode aidé
  if(hs) S.hintT = later(grayOut, hs * 1000);
}
function popAtMouse(cx, cy, text){
  const r = mapwrap.getBoundingClientRect();
  const p = el('div', 'pop', text);
  p.style.left = (cx - r.left) + 'px'; p.style.top = (cy - r.top) + 'px';
  mapwrap.appendChild(p); setTimeout(() => p.remove(), 950);
}
function geoGood(e){
  S.locked = true; $('btnSkip').disabled = true;
  S.score += S.assist ? .5 : 1; setScore(); bumpScore();           // mode aidé : chaque bonne réponse vaut un demi-point
  mark(S.cur, 'ok'); sfx.ok(); popAtMouse(e.clientX, e.clientY, S.assist ? '+½' : '+1');
  setTarget('Bravo !', DATA.countries[S.cur].n, 'ok');
  later(nextTarget, 450);
}
function geoBad(clicked){
  S.locked = true; $('btnSkip').disabled = true; S.wrong++;
  const info = DATA.countries[clicked];
  mark(clicked, 'ko'); mark(S.cur, 'show'); sfx.ko();
  setTarget('Tu as cliqué sur : ' + (info ? info.n : '…'), 'C’était : ' + DATA.countries[S.cur].n, 'ko');
  later(nextTarget, 1500);
}
function geoSkip(){
  if(!S.running || S.locked || S.game.mode !== 'geo') return;
  S.locked = true; $('btnSkip').disabled = true;
  mark(S.cur, 'show');
  setTarget('Pas de souci !', 'C’était : ' + DATA.countries[S.cur].n, 'ko');
  later(nextTarget, 1500);
}
svg.addEventListener('click', e => {
  if(dragMoved){ dragMoved = false; return; }
  if(!S.running || S.locked || !S.game || S.game.mode !== 'geo') return;
  const p = e.target.closest ? e.target.closest('path[data-c]') : null;
  if(!p) return;                     // clic dans la mer : on ignore
  if(p.dataset.c === S.cur) geoGood(e); else geoBad(p.dataset.c);
});
$('btnSkip').addEventListener('click', geoSkip);

/* ---------- Mode aidé : nom + drapeau (pays) ou photo (départements) au survol ---------- */
let tipCode = '';
function hideTip(){ tipCode = ''; $('tip').hidden = true; }
function showTip(code, e){
  const c = DATA.countries[code], tip = $('tip'); if(!c){ hideTip(); return; }
  if(code !== tipCode){
    tipCode = code;
    const m = MEDIA[code], img = $('tipImg'), src = m ? (m.i || m) : '';
    $('tipName').textContent = c.n;
    img.hidden = !src; if(src) img.src = src;
    tip.classList.toggle('photo', !!src && PAGE === 'fra');
    tip.hidden = false;
  }
  const r = mapwrap.getBoundingClientRect(), w = tip.offsetWidth, h = tip.offsetHeight;
  let x = e.clientX - r.left + 16, y = e.clientY - r.top + 16;
  if(x + w > r.width - 6) x = e.clientX - r.left - w - 16;
  if(y + h > r.height - 6) y = e.clientY - r.top - h - 16;
  tip.style.left = Math.max(4, x) + 'px'; tip.style.top = Math.max(4, y) + 'px';
}
function tipAt(e){
  if(!S.assist || !S.running || (drag && dragMoved)){ hideTip(); return; }
  const p = e.target.closest ? e.target.closest('path[data-c]') : null;
  if(p) showTip(p.dataset.c, e); else hideTip();
}
svg.addEventListener('pointermove', tipAt);
svg.addEventListener('pointerdown', tipAt);          // sur tablette : le doigt posé fait apparaître l'aide
svg.addEventListener('pointerleave', hideTip);

/* ===== Quiz des capitales : un pays (drapeau + carte), 4 capitales au choix ===== */
let capPin = null;
function hidePin(){ if(capPin) capPin.setAttribute('visibility', 'hidden'); }
function showPin(code){                              // repère sur le pays, même quand il est minuscule
  if(!capPin){
    const NS = 'http://www.w3.org/2000/svg'; capPin = document.createElementNS(NS, 'g');
    ['pinring', 'pindot'].forEach(c => { const e = document.createElementNS(NS, 'circle'); e.setAttribute('class', c); capPin.appendChild(e); });
    svg.appendChild(capPin);
  }
  const [x, y] = centerOf(code), k = view.w / 110;
  [[capPin.firstChild, 3.4 * k], [capPin.lastChild, k]].forEach(([c, r]) => { c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', r); });
  capPin.removeAttribute('visibility'); svg.appendChild(capPin);
}
function capPool(L){ return Object.keys(CAPS).filter(k => DATA.countries[k] && (L.codes ? L.codes.includes(k) : L.reg.includes(DATA.countries[k].r))); }
function capChoices(code, L){                        // la bonne capitale + 3 autres : de la même région (Europe, continent) ou parmi les pays connus
  const right = CAPS[code], r = DATA.countries[code].r;
  const pool = L.codes ? L.codes : L.reg.length === 1 ? capPool(L) : Object.keys(CAPS).filter(k => DATA.countries[k] && DATA.countries[k].r === r);
  const ok = k => k !== code && CAPS[k] && CAPS[k] !== right;
  const picks = shuffle(pool.filter(ok)).slice(0, 3);
  if(picks.length < 3) shuffle(Object.keys(CAPS).filter(k => ok(k) && !picks.includes(k))).slice(0, 3 - picks.length).forEach(k => picks.push(k));
  return shuffle([right].concat(picks.map(k => CAPS[k])));
}
function nextCapital(){
  unmark();
  if(!S.queue.length){
    S.queue = shuffle(S.pool);
    if(S.queue.length > 1 && S.queue[S.queue.length - 1] === S.cur) S.queue.unshift(S.queue.pop());
  }
  S.cur = S.queue.pop();
  const c = DATA.countries[S.cur], m = MEDIA[S.cur], fl = $('qFlag');
  setTarget('Quelle est la capitale de', c.n);
  fl.hidden = !m; if(m) fl.src = m.i || m;
  S.zoneKey = S.level.reg && S.level.reg.length === 1 ? S.level.zone : ({E:'europe', A:'asie', F:'afrique', M:'ameriques'}[c.r] || 'monde');   // la carte se cadre sur le continent du pays
  zoneView = fitView(S.zoneKey); view = {...zoneView}; applyView();
  mark(S.cur, 'hl'); showPin(S.cur);
  const box = $('qChoices'); box.textContent = '';
  capChoices(S.cur, S.level).forEach(name => {
    const b = el('button', 'choice' + (name.length > 14 ? ' long' : ''), name); b.dataset.n = name;
    b.addEventListener('click', () => pickCap(b)); box.appendChild(b);
  });
  S.locked = false;
}
function popAtEl(elm, text){
  const box = $('qcm'), r = box.getBoundingClientRect(), b = elm.getBoundingClientRect(), p = el('div', 'pop', text);
  p.style.left = (b.left + b.width / 2 - r.left) + 'px'; p.style.top = (b.top - r.top) + 'px';
  box.appendChild(p); setTimeout(() => p.remove(), 950);
}
function pickCap(b){
  if(!S.running || S.locked || !S.game || S.game.mode !== 'qcm') return;
  S.locked = true;
  const right = CAPS[S.cur];
  if(b.dataset.n === right){
    S.score++; setScore(); bumpScore(); b.classList.add('ok'); sfx.ok(); popAtEl(b, '+1');
    setTarget('Bravo !', right, 'ok'); later(nextCapital, 650);
  } else {
    S.wrong++; b.classList.add('ko');
    [...$('qChoices').children].forEach(x => { if(x.dataset.n === right) x.classList.add('ok'); });
    sfx.ko(); setTarget('Presque ! C’est', right, 'ko'); later(nextCapital, 1700);
  }
}

/* ===== Jeux de calcul ===== */
function qAdd(L){ const s = rnd(L.min, L.max), a = rnd(1, s - 1), b = s - a; return {a, b, r:s, key:[a, b].sort((x, y) => x - y).join('+')}; }
function qSub(L){ const a = rnd(L.min, L.max), b = rnd(1, a - 1); return {a, b, r:a - b, key:a + '-' + b}; }
function qMul(L){
  const t = L.tables[rnd(0, L.tables.length - 1)], m = rnd(L.bmin, L.bmax), swap = Math.random() < .5;
  return {a: swap ? m : t, b: swap ? t : m, r:t * m, key:[t, m].sort((x, y) => x - y).join('x')};
}
function makeQ(){
  const id = S.game.id, L = S.level; let q, tries = 0;
  do{ q = id === 'add' ? qAdd(L) : id === 'sub' ? qSub(L) : qMul(L); tries++; }
  while(S.recent.includes(q.key) && tries < 40);
  S.recent.push(q.key); if(S.recent.length > 8) S.recent.shift();
  return q;
}
function frame(n, clsOf){
  const fr = el('div', 'frame');
  fr.style.gridTemplateColumns = 'repeat(' + Math.min(n, 5) + ', var(--d))';
  for(let i = 0; i < n; i++) fr.appendChild(el('span', 'dot ' + clsOf(i)));
  return fr;
}
function renderFrames(){
  const f = $('frames'); f.textContent = '';
  if(!S.level.dots){ f.classList.remove('on'); return; }
  f.classList.add('on');
  const q = S.q;
  if(S.game.id === 'add'){ f.append(frame(q.a, () => 'a'), frame(q.b, () => 'b')); }
  else if(S.game.id === 'sub'){ f.append(frame(q.a, i => i < q.r ? 'a' : 'x')); }   // les points barrés = ceux qu'on enlève
}
function renderAns(){
  const a = $('ans');
  a.textContent = S.typed || '?';
  a.classList.toggle('empty', !S.typed);
}
function nextQuestion(){
  S.q = makeQ(); S.typed = '';
  $('qa').textContent = S.q.a; $('qb').textContent = S.q.b;
  $('hint').textContent = '';
  $('qcard').className = 'qcard';
  renderAns(); renderFrames();
  setTarget('Calcule !', S.game.emoji + ' ' + S.level.n);
  S.locked = false;
}
function popAtAnswer(text){
  const stage = $('stage'), sr = stage.getBoundingClientRect(), ar = $('ans').getBoundingClientRect();
  const p = el('div', 'pop', text); p.style.fontSize = '44px';
  p.style.left = (ar.left + ar.width / 2 - sr.left) + 'px'; p.style.top = (ar.top + ar.height / 2 - sr.top) + 'px';
  stage.appendChild(p); setTimeout(() => p.remove(), 950);
}
const isMath = () => S.game && S.game.mode === 'math';
function press(d){
  if(!S.running || S.locked || !isMath()) return;
  if(S.typed.length >= String(S.q.r).length) return;
  S.typed += d; sfx.key(); renderAns();
  if(S.typed.length === String(S.q.r).length) check();   // validation automatique
}
function back(){
  if(!S.running || S.locked || !isMath() || !S.typed) return;
  S.typed = S.typed.slice(0, -1); renderAns();
}
function validate(){
  if(!S.running || S.locked || !isMath() || !S.typed) return;
  check();
}
function check(){
  S.locked = true;
  const ok = parseInt(S.typed, 10) === S.q.r;
  const eq = S.q.a + ' ' + S.game.sign + ' ' + S.q.b + ' = ' + S.q.r;
  if(ok){
    S.score++; setScore(); bumpScore();
    $('qcard').className = 'qcard ok';
    sfx.ok(); popAtAnswer('+1');
    setTarget('Bravo !', eq, 'ok');
    later(nextQuestion, 450);
  } else {
    S.wrong++;
    $('qcard').className = 'qcard ko';
    $('hint').textContent = 'La réponse est ' + S.q.r;
    sfx.ko();
    setTarget('Presque !', eq, 'ko');
    later(nextQuestion, 1500);
  }
}

(function buildPad(){
  const pad = $('pad');
  ['1','2','3','4','5','6','7','8','9','del','0','go'].forEach(k => {
    const b = el('button');
    b.dataset.k = k;
    if(k === 'del'){ b.className = 'del'; b.textContent = '⌫'; b.setAttribute('aria-label', 'Effacer'); }
    else if(k === 'go'){ b.className = 'go'; b.textContent = '✓'; b.setAttribute('aria-label', 'Valider'); }
    else b.textContent = k;
    pad.appendChild(b);
  });
  pad.addEventListener('pointerdown', e => {
    const b = e.target.closest('button'); if(!b) return;
    e.preventDefault();
    const k = b.dataset.k;
    if(k === 'del') back(); else if(k === 'go') validate(); else press(k);
  });
})();
document.addEventListener('keydown', e => {
  if(!$('game').classList.contains('active') || !isMath()) return;
  if(/^[0-9]$/.test(e.key)){ e.preventDefault(); press(e.key); }
  else if(e.key === 'Backspace'){ e.preventDefault(); back(); }
  else if(e.key === 'Enter'){ e.preventDefault(); validate(); }
});

/* ---------- Quitter / fin de partie ---------- */
$('btnQuit').addEventListener('click', () => {
  S.runId++; clearInterval(S.timerId); S.running = false; hideTip();
  S.explore = false; $('game').classList.remove('explore');
  $('count').classList.remove('show'); unmark();
  toMenu();
});
function endGame(){
  clearInterval(S.timerId); S.running = false; S.locked = true; $('btnSkip').disabled = true;
  unmark(); hideTip(); sfx.end();
  setTarget('⏰ Temps écoulé !', fmt(S.score) + ' ' + (S.score > 1 ? S.game.many : S.game.one));
  later(showEnd, 1000);
}
function msgFor(n){
  if(n === 0) return 'Pas de panique, on s’entraîne !';
  if(n < 5)  return 'C’est un bon début, continue !';
  if(n < 10) return 'Pas mal du tout !';
  if(n < 20) return 'Super ! Tu es rapide !';
  return 'Incroyable ! Champion ! 🏆';
}
function showEnd(){
  const G = S.game, L = S.level, prev = bestOf(G.id, L.k);
  $('endwrap').classList.remove('boardonly');
  $('endTitle').textContent = '⏰ Temps écoulé !';
  $('endScore').textContent = fmt(S.score);
  $('endUnit').textContent = (S.score > 1 ? G.many : G.one) + ' · ' + (G.mode !== 'math' ? L.e + ' ' + L.n : G.emoji + ' ' + L.n);
  $('endErr').textContent = (S.wrong === 0 ? 'Aucune erreur 👏' : (S.wrong === 1 ? '1 erreur' : S.wrong + ' erreurs')) + (S.assist ? ' · 🤝 Mode aidé : points ÷ 2' : '');
  $('btnMenu').textContent = G.exit ? '← Anatomie' : '📋 Menu';
  $('endMsg').textContent = msgFor(S.score);
  const record = S.score > 0 && S.score > prev;
  $('endRecord').hidden = !record;
  if(record) fxTimer = setTimeout(() => recordFx(S.score > 1 ? G.many : G.one), 450);   // feu d'artifice + « Nouveau Record ! »
  $('savedMsg').textContent = S.score <= 0 ? 'Trouve au moins 1 point pour entrer au classement.' : '';
  S.saved = false; S.entry = null;
  saveScore();
  if(S.score <= 0) renderBoard(G.id, L.k, null);
  show('end');
}
function saveScore(){
  if(S.saved || S.score <= 0) return;
  const name = player || 'Joueur';
  const all = scores(), k = bkey(S.game.id, S.level.k), list = all[k] || [];
  const entry = {n:name, s:S.score, d:Date.now()};
  if(S.assist) entry.a = 1;
  list.push(entry);
  list.sort((a, b) => b.s - a.s || a.d - b.d);
  all[k] = list.slice(0, 30);
  store.set(KEY, all);
  S.saved = true; S.entry = entry;
  const rank = all[k].findIndex(e => e.d === entry.d);
  $('savedMsg').textContent = rank >= 0 ? '✅ Bien joué ' + name + ' ! Tu es n°' + (rank + 1) + ' au classement.' : '✅ Enregistré ! (hors du top 10 cette fois)';
  renderBoard(S.game.id, S.level.k, entry);
}
$('btnAgain').addEventListener('click', () => { audio(); startGame(S.game.id, S.level.k); });
$('btnMenu').addEventListener('click', toMenu);
$('btnHome').addEventListener('click', home);
$('btnBack').addEventListener('click', () => go(S.from));

/* ---------- Classements ---------- */
const BOARD_SHOWN = 15;                            // lignes affichées ; on en garde 30 par niveau pour les totaux
const AGG = {                                      // classements « tous les jeux d'une famille »
  calc:   {id:'calc',   emoji:'🧮', short:'Tous les calculs',     games:['add','sub','mul']},
  geoall: {id:'geoall', emoji:'🌍', short:'Toute la géographie', games:['geo','fra','cap','eau']},
  anaall: {id:'anaall', emoji:'🦴', short:'Toute l’anatomie',    games:['org','cm2','os5','ske']}
};
let bGame = 'geo', bLevel = 'total';
// Classement d'un niveau : les meilleurs scores enregistrés. Classement « total » : pour chaque joueur,
// la somme de son meilleur score de chaque niveau (d'un jeu, ou de tous les calculs).
function boardRows(gid, lk){
  const all = scores();
  if(!AGG[gid] && lk !== 'total'){                // un même joueur peut revenir à des rangs différents, mais pas deux fois avec le même score
    const seen = new Set();
    return (all[bkey(gid, lk)] || []).filter(e => { const k = e.n + '\n' + e.s; if(seen.has(k)) return false; seen.add(k); return true; });
  }
  const best = {};
  (AGG[gid] ? AGG[gid].games : [gid]).forEach(g => GAMES[g].levels.forEach(l => {
    const mine = {};
    (all[bkey(g, l.k)] || []).forEach(e => { mine[e.n] = Math.max(mine[e.n] || 0, e.s); });
    Object.keys(mine).forEach(n => { best[n] = (best[n] || 0) + mine[n]; });
  }));
  return Object.keys(best).map(n => ({n, s:best[n]})).sort((x, y) => y.s - x.s || x.n.localeCompare(y.n));
}
// Podium : trois joueurs différents (leur meilleur score) ; s'il y en a moins de trois, on complète avec les scores suivants
function podiumRows(rows){
  const top = [], names = new Set();
  rows.forEach(r => { if(top.length < 3 && !names.has(r.n)){ top.push(r); names.add(r.n); } });
  rows.forEach(r => { if(top.length < 3 && !top.includes(r)) top.push(r); });
  return top.sort((a, b) => b.s - a.s);
}
function renderPodium(all){
  const rows = podiumRows(all), pd = $('podium'); pd.textContent = ''; pd.hidden = !rows.length;
  const medals = ['🥇','🥈','🥉'];
  [1, 0, 2].filter(i => rows[i]).forEach(i => {                // ordre d'affichage : 2e, 1er, 3e
    const col = el('div', 'pod p' + (i + 1));
    col.append(el('div', 'pm', medals[i]), el('div', 'pn', rows[i].n + (rows[i].a ? ' 🤝' : '')), el('div', 'ps', fmt(rows[i].s)), el('div', 'pb', String(i + 1)));
    pd.appendChild(col);
  });
}
function renderBoard(gid, lk, hl){
  bGame = gid; bLevel = lk;
  const G = AGG[gid] || GAMES[gid], total = !!AGG[gid] || lk === 'total';
  // Onglets du haut : accueil = Géographie / Calcul ; page Calcul = Tous / Additions / Soustractions / Multiplications
  const family = a => [[a.id, a.emoji + ' ' + a.short]].concat(a.games.map(g => [g, GAMES[g].emoji + ' ' + GAMES[g].short]));
  const tops = PAGE === 'home' ? [['geoall', '🌍 Géographie'], ['calc', '🧮 Calcul'], ['anaall', '🦴 Anatomie']]
    : PAGE === 'calc' ? family(AGG.calc) : PAGE === 'geoh' ? family(AGG.geoall) : PAGE === 'anah' ? family(AGG.anaall) : [];
  const gt = $('gtabs'); gt.textContent = '';
  tops.forEach(([g, label]) => {
    const b = el('button', 'tab' + (g === gid ? ' on' : ''), label);
    b.addEventListener('click', () => renderBoard(g, 'total', null));
    gt.appendChild(b);
  });
  gt.hidden = !tops.length;
  // Onglets de niveau : seulement sur la page d'un jeu (Total + un onglet par niveau)
  const tabs = $('tabs'); tabs.textContent = '';
  if(GAMES[PAGE] && G.levels.length > 1) [{k:'total', e:'🏅', n:'Total'}].concat(G.levels).forEach(l => {
    const b = el('button', 'tab' + (l.k === lk ? ' on' : ''), l.e + ' ' + l.n);
    b.addEventListener('click', () => renderBoard(gid, l.k, S.entry));
    tabs.appendChild(b);
  });
  tabs.hidden = !tabs.children.length;
  $('btnClear').hidden = total;                       // on n'efface qu'un niveau, jamais un total
  const rows = boardRows(gid, lk), ol = $('board'); ol.textContent = '';
  renderPodium(rows);
  if(!rows.length){
    const li = el('li', 'empty', 'Aucun score pour l’instant. Sois le premier !'); li.style.display = 'block';
    ol.appendChild(li); return;
  }
  const medals = ['🥇','🥈','🥉'], unit = total ? ['point', 'points'] : [G.b1, G.bn];
  rows.slice(0, BOARD_SHOWN).forEach((e, i) => {
    const me = total ? e.n === player : hl && e.d === hl.d;
    const li = el('li', me ? 'me' : '');
    li.append(el('span', 'rk', medals[i] || (i + 1) + '.'), el('span', 'nm', e.n + (e.a ? ' 🤝' : '')), el('span', 'sc', fmt(e.s) + ' ' + (e.s > 1 ? unit[1] : unit[0])));
    ol.appendChild(li);
  });
}
function showBoardOnly(from, gid){
  S.entry = null; S.from = from;
  $('endwrap').classList.add('boardonly');
  renderBoard(gid, 'total', null);
  show('end');
}
$('btnBoardHome').addEventListener('click', () => showBoardOnly(PAGE, PAGE === 'calc' ? 'calc' : PAGE === 'anah' ? 'anaall' : 'geoall'));
$('btnBoardGame').addEventListener('click', () => showBoardOnly('menu', PAGE));
$('btnClear').addEventListener('click', () => {
  if(!confirm('Effacer tous les scores de ce niveau ?')) return;
  const all = scores(); delete all[bkey(bGame, bLevel)]; store.set(KEY, all);
  renderBoard(bGame, bLevel, null);
});

window.__jxStop = () => { stopFx(); clearTimeout(ghostTimer); clearTimeout(lightTimer); clearTimeout(musicTimer); clearInterval(S.timerId); clearTimeout(S.hintT); S.runId++; };
buildMenus();
buildPlayers();
if(GAMES[PAGE] && GAMES[PAGE].direct && player) startGame(PAGE, GAMES[PAGE].levels[0].k);   // anatomie : un seul niveau, on joue tout de suite
if(PAGE === 'home' && player && HASH === '#menu') enterHome();   // retour d'un jeu : on garde le joueur
// Appli installable (PWA) : le service worker met les pages en cache pour jouer hors ligne. Seulement en http(s) : en double-clic (file://) on s'en passe.
if('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) navigator.serviceWorker.register('sw.js').catch(() => {});
})();
