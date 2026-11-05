// Test de la page geo.html : bons/mauvais clics sur la carte, score, retour au menu du jeu, lien Accueil,
// puis ouverture d'une page de calcul (pas de carte, pavé visible).
import {launch, pageUrl, SHOTS as SH, sleep} from './helpers.mjs';

const browser = await launch();
const page = await browser.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: ' + e.message));
page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
await page.evaluateOnNewDocument(() => {
  localStorage.setItem('jeuxexplorateurs.v1.players', JSON.stringify(['Léa']));
  localStorage.setItem('jeuxexplorateurs.v1.player', JSON.stringify('Léa'));
});
await page.goto(pageUrl('geo.html')); await sleep(300);

console.log('G) écran:', await page.$eval('.screen.active', e => e.id));
await page.evaluate(() => [...document.querySelectorAll('.zone')].find(b => b.textContent.includes('Europe')).click());
await page.waitForFunction(() => document.getElementById('tLabel').textContent === 'Trouve', {timeout: 40000});
console.log('G) mode jeu:', await page.$eval('#game', e => e.dataset.mode),
  '| carte visible:', await page.$eval('#mapwrap', e => getComputedStyle(e).display !== 'none'),
  '| pavé visible:', await page.$eval('#pad', e => getComputedStyle(e).display !== 'none'));

const codes = await page.evaluate(() => {
  const src = [...document.scripts].map(s => s.textContent).join('\n');
  const d = JSON.parse(src.match(/const DATA = (\{.*?\});\nconst TIME/s)[1]);
  const o = {}; for (const [k, v] of Object.entries(d.countries)) o[v.n] = k; return o;
});
async function centerOf(code) {
  return page.evaluate((code) => {
    const best = [...document.querySelectorAll('path[data-c="' + code + '"]')].sort((a, b) => { const x = a.getBBox(), y = b.getBBox(); return y.width * y.height - x.width * x.height; })[0];
    const b = best.getBBox(), svg = document.getElementById('map'), pt = svg.createSVGPoint(), m = best.getScreenCTM();
    for (let i = 1; i < 12; i++) for (let j = 1; j < 12; j++) {
      pt.x = b.x + b.width * i / 12; pt.y = b.y + b.height * j / 12;
      if (best.isPointInFill(pt)) { const s = pt.matrixTransform(m); const top = document.elementFromPoint(s.x, s.y); if (top && top.dataset && top.dataset.c === code) return {x: s.x, y: s.y}; }
    }
    return null;
  }, code);
}
const waitTarget = () => page.waitForFunction(() => document.getElementById('tLabel').textContent === 'Trouve', {timeout: 8000});
let good = 0;
for (let n = 0; n < 4; n++) {
  const name = await page.$eval('#tName', e => e.textContent);
  const p = await centerOf(codes[name]);
  if (!p) { console.log('G) introuvable:', name); await page.click('#btnSkip'); await waitTarget(); continue; }
  if (n === 2) {
    const other = name === 'Allemagne' ? 'France' : 'Allemagne';
    const q = await centerOf(codes[other]);
    await page.mouse.click(q.x, q.y); await sleep(150);
    console.log('G) mauvais clic ->', await page.$eval('#tLabel', e => e.textContent), '|', await page.$eval('#tName', e => e.textContent));
    await waitTarget(); continue;
  }
  await page.mouse.click(p.x, p.y); good++;
  await sleep(150);
  await waitTarget();
}
console.log('G) bonnes réponses envoyées:', good, '| score affiché:', await page.$eval('#score', e => e.textContent));
await page.click('#btnQuit'); await sleep(150);
console.log('G) bouton Menu ->', await page.$eval('.screen.active', e => e.id));
// Le lien « Accueil » ramène à index.html, puis une page de calcul s'ouvre sans carte
await Promise.all([page.waitForNavigation(), page.click('#menu a.chip')]);
console.log('G) lien Accueil ->', page.url().split('/').pop());
await page.goto(pageUrl('multiplications.html')); await sleep(200);
await page.evaluate(() => document.querySelectorAll('.lvl')[2].click());
await page.waitForFunction(() => document.getElementById('tLabel').textContent === 'Calcule !', {timeout: 20000});
console.log('G) page multiplications -> mode:', await page.$eval('#game', e => e.dataset.mode),
  '| carte absente:', !(await page.$('#mapwrap')),
  '| pavé visible:', await page.$eval('#pad', e => getComputedStyle(e).display !== 'none'));
console.log('erreurs JS:', errors);
console.log('FIN DU TEST');
await browser.close();
