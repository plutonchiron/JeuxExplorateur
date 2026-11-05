// Assemble le jeu en PLUSIEURS pages HTML autonomes dans dist/ : index.html (menu principal)
// + geographie.html, calcul.html et anatomie.html (sous-menus) + une page par jeu (geo, departements, capitales, eaux, organes, organes-cm2, os-5eme, squelette, additions, soustractions, multiplications).
// Chaque page contient son CSS, son JS (commun) et ses données : aucune requête réseau, s'ouvre par double-clic.
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import {fileURLToPath} from 'url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = p => fs.readFileSync(path.join(root, p), 'utf8').replace(/\n$/, '');

const MATH_HOW = 'Choisis un niveau. Tape la réponse avec le clavier ou les gros boutons.';
const PAGES = [
  {file: 'index.html', page: 'home', title: 'Les Jeux des Explorateurs'},
  {file: 'geographie.html', page: 'geoh', title: 'Géographie · Les Jeux des Explorateurs'},
  {file: 'calcul.html', page: 'calc', title: 'Calcul · Les Jeux des Explorateurs'},
  {file: 'anatomie.html', page: 'anah', title: 'Anatomie · Les Jeux des Explorateurs'},
  {file: 'geo.html', page: 'geo', mode: 'geo', emoji: '🌍', name: 'Géo Explorateurs',
    tagline: 'Trouve un maximum de pays en 1 minute !', how: 'Choisis une zone. Molette ou boutons +/− pour zoomer sur la carte.',
    mapLabel: 'Carte du monde', paths: 'data/paths.frag', data: 'data/data.json', media: 'data/flags.json', info: 'data/info-pays.json', photos: 'data/photos-pays.json',
    assistWhat: 'du pays avec son drapeau', noun: 'pays'},
  {file: 'departements.html', page: 'fra', mode: 'geo', emoji: '🗺️', name: 'Départements de France',
    tagline: 'Trouve un maximum de départements en 1 minute !', how: 'Un département est demandé : clique dessus sur la carte de France. Molette ou boutons +/− pour zoomer.',
    mapLabel: 'Carte des départements de France', paths: 'data/france-paths.frag', data: 'data/france.json', info: 'data/info-departements.json', photos: 'data/photos.json',
    assistWhat: 'du département', noun: 'département'},
  {file: 'capitales.html', page: 'cap', mode: 'qcm', parent: 'geographie.html', parentLabel: '← Géographie', emoji: '🏛️', name: 'Capitales du monde',
    tagline: 'Trouve un maximum de capitales en 1 minute !', how: 'Un pays s’affiche avec son drapeau : choisis sa capitale parmi 4 réponses.',
    mapLabel: 'Carte du monde', paths: 'data/paths.frag', data: 'data/data.json', media: 'data/flags.json', caps: 'data/capitales.json', noAssist: true},
  {file: 'eaux.html', page: 'eau', mode: 'geo', parent: 'geographie.html', parentLabel: '← Géographie', emoji: '🏞️', name: 'Eaux et montagnes',
    tagline: 'Trouve un maximum de fleuves, de lacs, de mers et de montagnes en 1 minute !', how: 'Un nom est demandé : clique sur le fleuve, le lac, la mer ou la chaîne de montagnes. Molette ou boutons +/− pour zoomer.',
    mapLabel: 'Carte de France : fleuves, lacs, mers et montagnes', paths: 'data/eaux-paths.frag', data: 'data/eaux.json', noAssist: true},
  {file: 'organes.html', page: 'org', mode: 'geo', parent: 'anatomie.html', parentLabel: '← Anatomie', emoji: '🧠', name: 'Les organes',
    tagline: 'Trouve un maximum d’organes en 1 minute !', how: 'Un organe est demandé : clique dessus sur le corps. Molette ou boutons +/− pour zoomer.',
    mapLabel: 'Le corps humain', paths: 'data/body-paths.frag', data: 'data/body.json', noAssist: true},
  {file: 'organes-cm2.html', page: 'cm2', mode: 'geo', parent: 'anatomie.html', parentLabel: '← Anatomie', emoji: '🔬', name: 'Situer les organes',
    tagline: 'Situe un maximum d’organes en 1 minute !', how: 'Un organe est demandé : clique dessus sur la planche d’anatomie. Molette ou boutons +/− pour zoomer.',
    mapLabel: 'Planche d’anatomie du tronc humain', paths: 'data/body2-paths.frag', data: 'data/body2.json', noAssist: true},
  {file: 'os-5eme.html', page: 'os5', mode: 'geo', parent: 'anatomie.html', parentLabel: '← Anatomie', emoji: '🦴', name: 'Situer les os (5ème)',
    tagline: 'Situe un maximum d’os en 1 minute !', how: 'Un os est demandé : clique dessus sur le squelette. Molette ou boutons +/− pour zoomer, surtout pour les mains et les pieds.',
    mapLabel: 'Squelette humain de face', paths: 'data/os5-paths.frag', data: 'data/os5.json', noAssist: true},
  {file: 'squelette.html', page: 'ske', mode: 'geo', parent: 'anatomie.html', parentLabel: '← Anatomie', emoji: '💀', name: 'Le squelette',
    tagline: 'Trouve un maximum d’os en 1 minute !', how: 'Un os est demandé : clique dessus sur le squelette. Molette ou boutons +/− pour zoomer.',
    mapLabel: 'Le squelette humain', paths: 'data/skeleton-paths.frag', data: 'data/skeleton.json', noAssist: true},
  {file: 'additions.html', page: 'add', mode: 'math', emoji: '➕', name: 'Additions', tagline: 'Fais un maximum d’additions en 1 minute !', how: MATH_HOW},
  {file: 'soustractions.html', page: 'sub', mode: 'math', emoji: '➖', name: 'Soustractions', tagline: 'Fais un maximum de soustractions en 1 minute !', how: MATH_HOW},
  {file: 'multiplications.html', page: 'mul', mode: 'math', emoji: '✖️', name: 'Multiplications', tagline: 'Fais un maximum de multiplications en 1 minute !', how: MATH_HOW}
];

// Les remplacements utilisent des fonctions pour éviter l'interprétation des « $ » dans le contenu.
const fill = (tpl, vars) => tpl.replace(/\{\{(\w+)\}\}/g, (_, k) => vars[k]);
const keep = (tpl, tag, on) => tpl.replace(new RegExp(`[ \\t]*<!--${tag}-->\\n([\\s\\S]*?)[ \\t]*<!--/${tag}-->\\n`, 'g'), (_, body) => on ? body : '');

const layout = read('src/index.html');
const partial = n => read('src/partials/' + n + '.html') + '\n';
const css = read('src/styles.css'), js = read('src/game.js');
// Réglage du mode aidé (pages de géographie) : bouton + explication (+ crédits des photos)
const assistHtml = p => `      <div class="modes">
        <button class="chip assist" id="btnAssist">🤝 Mode aidé</button>
        <button class="chip assist" id="btnExplore">🔎 Mode exploration</button>
      </div>
      <p class="assisthelp">Mode aidé : passe la souris sur la carte pour voir le nom ${p.assistWhat} ; chaque bonne réponse ne vaut alors que ½ point.<br>Mode exploration : pas de chrono, tu découvres des informations sur chaque ${p.noun}.</p>`;
const rawFile = p => fs.readFileSync(path.join(root, p), 'utf8');

fs.rmSync(path.join(root, 'dist'), {recursive: true, force: true});
fs.mkdirSync(path.join(root, 'dist'), {recursive: true});

const built = {};
for (const p of PAGES) {
  const home = p.page === 'home', geoh = p.page === 'geoh', calc = p.page === 'calc', anah = p.page === 'anah', geo = p.mode === 'geo', qcm = p.mode === 'qcm', map = geo || qcm;
  const back = p.parent ? {backHref: p.parent, backLabel: p.parentLabel} : geo ? {backHref: 'geographie.html', backLabel: '← Géographie'} : {backHref: 'calcul.html', backLabel: '← Calcul'};
  const screens = home ? partial('players') + partial('home') + partial('end')
    : geoh ? partial('geomenu') + partial('end')
    : calc ? partial('calc') + partial('end')
    : anah ? partial('anamenu') + partial('end')
    : fill(partial('menu'), {...p, ...back, assist: geo && !p.noAssist ? assistHtml(p) : '', levelsClass: map ? 'zones' : 'ops single', levelsId: map ? 'zones' : 'ops'})
      + keep(keep(keep(fill(partial('game'), p), 'GEO', geo), 'MATH', !map), 'QCM', qcm) + partial('end');
  const out = fill(layout, {title: p.title || p.name + ' · Les Jeux des Explorateurs', page: p.page, backHref: home ? 'index.html' : (calc || geoh || anah) ? 'index.html#menu' : back.backHref})
    .replace('<!--SCREENS-->', () => screens)
    .replace('/*CSS*/', () => css)
    .replace('/*JS*/', () => js)
    .replace('/*PATHS*/', () => map ? rawFile(p.paths) : '')
    .replace('/*DATA*/', () => map ? rawFile(p.data) : '{}')
    .replace('/*CAPS*/', () => qcm ? rawFile(p.caps) : '{}')
    .replace('/*MEDIA*/', () => map && p.media ? rawFile(p.media) : '{}')
    .replace('/*INFO*/', () => geo && p.info ? rawFile(p.info) : '{}')
    .replace('/*PHOTOS*/', () => geo && p.photos ? rawFile(p.photos) : '{}');
  fs.writeFileSync(path.join(root, 'dist', p.file), out);
  built[p.file] = out;
  console.log('OK dist/' + p.file, Math.round(out.length / 1024) + ' Ko');
}

// Appli installable (PWA) : manifeste + icônes copiés tels quels, service worker généré avec la liste des fichiers
// et une version qui change dès qu'une page change (l'ancien cache est alors remplacé).
const PWA = ['manifest.webmanifest', 'icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png'];
for (const f of PWA) fs.copyFileSync(path.join(root, 'src/pwa', f), path.join(root, 'dist', f));
const version = crypto.createHash('sha1').update(Object.values(built).join('')).digest('hex').slice(0, 10);
const cached = ['./', ...PAGES.map(p => p.file), ...PWA];
fs.writeFileSync(path.join(root, 'dist', 'sw.js'), read('src/pwa/sw.js').replace('/*VERSION*/', () => version).replace('/*FILES*/', () => JSON.stringify(cached)) + '\n');
console.log('OK dist/sw.js', cached.length, 'fichiers, version', version);

// Version « un seul fichier » : toutes les pages dans jeux-explorateurs.html (pour les téléphones et tablettes qui n'ouvrent qu'un fichier isolé).
// Un clic sur un lien remplace le document par la page demandée (document.write), sans quitter ce fichier.
const lit = s => JSON.stringify(s).replace(/<\//g, '<\\/').replace(/<!--/g, '<\\!--');
const bundle = `<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Les Jeux des Explorateurs</title></head>
<body style="font-family:sans-serif;text-align:center;padding:2em">Chargement…
<script>
window.__jxPages = {${Object.entries(built).map(([f, h]) => lit(f) + ':' + lit(h)).join(',\n')}};
window.__jxNav = function(url){
  var i = url.indexOf('#'), f = i < 0 ? url : url.slice(0, i);
  window.__jxHash = i < 0 ? '' : url.slice(i);
  document.open(); document.write(window.__jxPages[f] || window.__jxPages['index.html']); document.close();
};
setTimeout(function(){ window.__jxNav('index.html'); }, 0);
</script></body></html>`;
fs.writeFileSync(path.join(root, 'dist', 'jeux-explorateurs.html'), bundle);
console.log('OK dist/jeux-explorateurs.html', Math.round(bundle.length / 1024) + ' Ko');
