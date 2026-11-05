// Test de bout en bout (une page HTML par jeu) : accueil, reprise des anciens scores, questions des 9 niveaux de calcul,
// partie complète (soustraction Super), enregistrement du prénom, classements et persistance.
// Affiche un compte rendu à lire (voir CLAUDE.md) ; dure environ 2 minutes.
import {launch, pageUrl, SHOTS as SH, sleep} from './helpers.mjs';

const browser = await launch();
const errors = [];
const hook = p => { p.on('pageerror', e => errors.push('pageerror: ' + e.message)); p.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); }); };
const active = p => p.$eval('.screen.active', e => e.id);

// ============ 1) Reprise des anciens scores (contexte vierge) ============
const page = await browser.newPage(); hook(page);
{
  await page.evaluateOnNewDocument(() => {
    if (!localStorage.getItem('jeuxexplorateurs.v1.players')) {   // un joueur déjà choisi, comme après le menu des joueurs
      localStorage.setItem('jeuxexplorateurs.v1.players', JSON.stringify(['Léa']));
      localStorage.setItem('jeuxexplorateurs.v1.player', JSON.stringify('Léa'));
    }
    if (!localStorage.getItem('geoexplorateurs.v1')) {
      localStorage.setItem('geoexplorateurs.v1', JSON.stringify({europe: [{n: 'Zoé', s: 12, d: 1}]}));
      localStorage.setItem('superadditions.v1', JSON.stringify({dix: [{n: 'Max', s: 9, d: 2}]}));
      localStorage.setItem('superadditions.v1.name', JSON.stringify('Max'));
    }
  });
  await page.goto(pageUrl('index.html')); await sleep(300);
  console.log('1) arrivée sur l’accueil:', await active(page), '| joueurs:', await page.$$eval('#plist .zn', e => e.map(x => x.textContent)));
  await page.click('#plist .zone'); await sleep(100);
  await page.click('#btnBoardHome'); await sleep(150);
  console.log('1) migration géo (total):', await page.$$eval('#board li', e => e.map(x => x.textContent)), '| podium:', await page.$$eval('#podium .pn', e => e.map(x => x.textContent)));
  await page.evaluate(() => [...document.querySelectorAll('#gtabs .tab')].find(b => b.textContent.includes('Calcul')).click());
  console.log('1) migration calcul (total):', await page.$$eval('#board li', e => e.map(x => x.textContent)));
}

// ============ 2) Accueil + questions des 3 opérations (une page chacune) ============
await page.goto(pageUrl('index.html') + '#menu'); await sleep(300);
console.log('2) menu principal:', await active(page), '| entrées:', await page.$$eval('.bigcard', e => e.map(x => x.getAttribute('href'))));
await page.screenshot({path: SH + 'hub-home.png'});
await page.goto(pageUrl('calcul.html')); await sleep(300);
console.log('2) sous-menu calcul:', await active(page), '| jeux:', await page.$$eval('.bigcard', e => e.map(x => x.getAttribute('href'))));
await page.goto(pageUrl('geo.html')); await sleep(300);
console.log('2) page géo:', await active(page), '| zones:', await page.$$eval('.zone .zn', e => e.map(x => x.textContent)));

const SIGN = {'+': 'add', '−': 'sub', '×': 'mul'};
const L = {
  add: [{min: 2, max: 10}, {min: 6, max: 20}, {min: 11, max: 30}],
  sub: [{min: 3, max: 10}, {min: 8, max: 20}, {min: 15, max: 30}],
  mul: [{t: [2, 5, 10], bmin: 1, bmax: 10}, {t: [2, 3, 4, 5], bmin: 2, bmax: 10}, {t: [2, 3, 4, 5, 6, 7, 8, 9, 10], bmin: 2, bmax: 10}]
};
const N = 10;
async function playLevel(lvlIdx, n, wrongAt = -1) {
  await page.evaluate(l => document.querySelectorAll('.lvl')[l].click(), lvlIdx);
  await page.waitForFunction(() => document.getElementById('tLabel').textContent === 'Calcule !', {timeout: 20000});
  const res = {bad: 0, dups: 0, maxDigits: 0, dots: -1};
  let prev = '';
  const seen = [];
  for (let i = 0; i < n; i++) {
    const q = await page.evaluate(() => ({a: +document.getElementById('qa').textContent, op: document.getElementById('qop').textContent, b: +document.getElementById('qb').textContent, dots: document.querySelectorAll('.dot').length}));
    const id = SIGN[q.op]; const p = L[id][lvlIdx];
    let r, valid;
    if (id === 'add') { r = q.a + q.b; valid = r >= p.min && r <= p.max && q.a >= 1 && q.b >= 1; }
    else if (id === 'sub') { r = q.a - q.b; valid = q.a >= p.min && q.a <= p.max && q.b >= 1 && r >= 1; }
    else { r = q.a * q.b; const okAB = p.t.includes(q.a) && q.b >= p.bmin && q.b <= p.bmax, okBA = p.t.includes(q.b) && q.a >= p.bmin && q.a <= p.bmax; valid = okAB || okBA; }
    if (!valid) { res.bad++; console.log('   question hors plage:', JSON.stringify(q)); }
    const key = [q.a, q.b].sort().join(q.op);
    if (key === prev) res.dups++; prev = key; seen.push(key);
    res.maxDigits = Math.max(res.maxDigits, String(r).length);
    if (i === 0) res.dots = q.dots;
    let digits = String(r);
    if (i === wrongAt) digits = digits.length === 1 ? String((r + 1) % 10) : '9'.repeat(digits.length);
    for (const ch of digits) await page.keyboard.press(ch);
    await sleep(30);
    await page.waitForFunction(() => document.getElementById('qcard').className === 'qcard', {timeout: 4000});
  }
  res.score = await page.$eval('#score', e => e.textContent);
  return res;
}
const names = ['add', 'sub', 'mul'], files = ['additions.html', 'soustractions.html', 'multiplications.html'];
for (let o = 0; o < 3; o++) {
  await page.goto(pageUrl(files[o])); await sleep(300);
  console.log(`2) page ${files[o]}:`, await active(page), '| niveaux:', await page.$$eval('.lvl .ln', e => e.length), '| carte absente:', !(await page.$('#mapwrap')));
  for (let l = 0; l < 3; l++) {
    const r = await playLevel(l, N);
    console.log(`2) ${names[o]} niveau ${l + 1}: hors plage=${r.bad}, doublons consécutifs=${r.dups}, chiffres max=${r.maxDigits}, points d'aide (1re question)=${r.dots}, score=${r.score}/${N}`);
    await page.click('#btnQuit'); await sleep(100);
    if (await active(page) !== 'menu') console.log('   !! retour au menu du jeu inattendu:', await active(page));
  }
}

// ============ 3) Partie complète : soustraction niveau Super, avec une erreur ============
await page.goto(pageUrl('soustractions.html')); await sleep(300);
await page.evaluate(() => document.querySelectorAll('.lvl')[1].click());
await page.waitForFunction(() => document.getElementById('tLabel').textContent === 'Calcule !', {timeout: 20000});
await page.screenshot({path: SH + 'hub-play-sub.png'});
const waitNext = () => page.waitForFunction(() => document.getElementById('tLabel').textContent === 'Calcule !', {timeout: 5000});
for (let i = 0; i < 5; i++) {
  const q = await page.evaluate(() => ({a: +document.getElementById('qa').textContent, b: +document.getElementById('qb').textContent}));
  const r = q.a - q.b;
  const digits = i === 2 ? (String(r).length === 1 ? String((r + 1) % 10) : '99') : String(r);
  for (const ch of digits) await page.keyboard.press(ch);
  await sleep(80);
  if (i === 2) console.log('3) mauvaise réponse ->', await page.$eval('#tLabel', e => e.textContent), '|', await page.$eval('#hint', e => e.textContent));
  await waitNext();
}
await page.waitForSelector('#end.active', {timeout: 70000}); await sleep(200);
console.log('3) fin: score', await page.$eval('#endScore', e => e.textContent), '|', await page.$eval('#endUnit', e => e.textContent), '|', await page.$eval('#endErr', e => e.textContent),
  '| record:', await page.$eval('#endRecord', e => getComputedStyle(e).display !== 'none'));
await sleep(150);   // le score est enregistré tout seul au nom du joueur
console.log('3) msg:', await page.$eval('#savedMsg', e => e.textContent));
console.log('3) classement affiché:', await page.$eval('#gtabs .tab.on', e => e.textContent), '/', await page.$eval('#tabs .tab.on', e => e.textContent), '→', await page.$$eval('#board li', e => e.map(x => x.textContent)));
await page.screenshot({path: SH + 'hub-end.png'});
await page.click('#btnMenu'); await sleep(150);
console.log('3) bouton Menu ->', await active(page), '| records:', await page.$$eval('.lvl .lr', e => e.map(x => x.textContent)));
await page.goto(pageUrl('calcul.html')); await sleep(300);
await page.click('#btnBoardHome'); await sleep(100);
await page.evaluate(() => [...document.querySelectorAll('#gtabs .tab')].find(b => b.textContent.includes('Soustractions')).click());
console.log('3) après rechargement, Soustractions (total par joueur):', await page.$$eval('#board li', e => e.map(x => x.textContent)));
await page.evaluate(() => [...document.querySelectorAll('#gtabs .tab')].find(b => b.textContent.includes('Multiplications')).click());
console.log('3) Multiplications (total):', await page.$$eval('#board li', e => e.map(x => x.textContent)));
await page.click('#btnBack'); await sleep(100);
console.log('3) Retour depuis le classement ->', await active(page));
console.log('erreurs JS:', errors);
console.log('FIN DU TEST');
await browser.close();
