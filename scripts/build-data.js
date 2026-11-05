// Génère les données de la carte à partir de Natural Earth (paquet npm « world-atlas », 50 m) :
//   data/paths.frag : un <path class="c {région}" data-c="{code ISO3}" d="…"/> par morceau de pays
//   data/data.json  : { countries: {code: {n: nom FR, r: région, a: surface en px², t: 1 si « pays à trouver »}},
//                       zones: {zone: [x0, y0, x1, y1]} }  (cadrage de chaque zone, repère 1000×520)
//
// À relancer seulement si on change la carte, les noms, les zones ou la simplification :
//   npm install && npm run build:data && npm run build
//
// Réglages (variables d'environnement) :
//   SIMPL   (défaut 0.25) : part des points conservés par la simplification (plus petit = plus léger)
//   MINPOLY (défaut 0.12) : surface minimale (px²) d'un îlot pour être dessiné
import fs from 'fs';
import path from 'path';
import {fileURLToPath} from 'url';
import {createRequire} from 'module';
import {feature} from 'topojson-client';
import {presimplify, simplify, quantile} from 'topojson-simplify';
import {geoNaturalEarth1, geoPath, geoCentroid} from 'd3-geo';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(import.meta.url);
const wc = require('world-countries');

const P = parseFloat(process.env.SIMPL || '0.25');
const MINPOLY = parseFloat(process.env.MINPOLY || '0.12');

const raw = JSON.parse(fs.readFileSync(path.join(root, 'node_modules/world-atlas/countries-50m.json')));
const pre = presimplify(raw);
const topo = simplify(pre, quantile(pre, P));
const all = feature(topo, topo.objects.countries).features.filter(f => f.id !== '010'); // sans l'Antarctique

const W = 1000, H = 520;
const projection = geoNaturalEarth1().fitExtent([[10, 10], [W - 10, H - 10]], {type: 'FeatureCollection', features: all});
const path_ = geoPath(projection).digits(1);

const byCode = {};
for (const c of wc) byCode[c.ccn3] = c;
const REG = {Europe: 'E', Asia: 'A', Africa: 'F', Americas: 'M', Oceania: 'O'};

// Territoires absents de world-countries (clé = nom Natural Earth) : [code, région, nom français]
const fallback = {
  Kosovo: ['XKX', 'E', 'Kosovo'],
  Somaliland: ['SOL', 'F', 'Somaliland'],
  'N. Cyprus': ['CYN', 'E', 'Chypre du Nord']
};
// Noms français plus lisibles pour des enfants que ceux de world-countries
const NAMES = {
  SWZ: 'Eswatini', COD: 'RD Congo', COG: 'République du Congo', PLW: 'Palaos',
  CPV: 'Cap-Vert', MMR: 'Birmanie (Myanmar)', CIV: 'Côte d’Ivoire'
};

const countries = {};
let paths = '';
const dropped = [];

// Retire les minuscules îlots (alourdissent le SVG sans rien apporter au jeu), garde toujours le plus grand morceau.
function prune(f) {
  if (f.geometry.type !== 'MultiPolygon') return f;
  const polys = f.geometry.coordinates.map(p => ({p, a: path_.area({type: 'Polygon', coordinates: p})}));
  const maxA = Math.max(...polys.map(x => x.a));
  const keep = polys.filter(x => x.a >= MINPOLY || x.a === maxA).map(x => x.p);
  return {...f, geometry: {type: 'MultiPolygon', coordinates: keep}};
}

function addPiece(f0, code, reg, name, isTarget, countArea) {
  const f = prune(f0);
  const d = path_(f);
  if (!d) return;
  paths += `<path class="c ${reg}" data-c="${code}" d="${d}"/>\n`;
  if (!countries[code]) countries[code] = {n: name, r: reg, a: 0, t: isTarget ? 1 : 0};
  if (countArea) countries[code].a += path_.area(f);
}

for (const f of all) {
  const c = byCode[f.id];
  let code, reg, name, tgt;
  if (c) {
    reg = REG[c.region];
    code = c.cca3;
    name = NAMES[code] || c.translations?.fra?.common || c.name.common;
    tgt = c.independent === true || code === 'GRL';   // seuls les pays indépendants (+ Groenland) sont demandés
  } else {
    const fb = fallback[f.properties.name];
    if (!fb) { dropped.push(f.properties.name); continue; }
    [code, reg, name] = fb;
    tgt = false;
  }
  if (!reg) { dropped.push(name); continue; }

  if (code === 'FRA') {
    // La Guyane (rattachée à la France) est dessinée en vert, comme le reste de l'Amérique du Sud.
    // Elle reste cliquable comme « France », mais sa surface n'est pas comptée (sinon la France paraîtrait énorme).
    const guy = [], rest = [];
    for (const poly of f.geometry.coordinates) {
      const ctr = geoCentroid({type: 'Polygon', coordinates: poly});
      (ctr[0] > -56 && ctr[0] < -50 && ctr[1] > 1 && ctr[1] < 7 ? guy : rest).push(poly);
    }
    addPiece({...f, geometry: {type: 'MultiPolygon', coordinates: rest}}, 'FRA', reg, name, true, true);
    addPiece({...f, geometry: {type: 'MultiPolygon', coordinates: guy}}, 'FRA', 'M', name, true, false);
  } else {
    addPiece(f, code, reg, name, tgt, true);
  }
}

// Cadrage de chaque zone : boîte englobante (en repère SVG) d'un quadrillage lon/lat
function bbox(lon0, lon1, lat0, lat1) {
  let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
  for (let lo = lon0; lo <= lon1; lo += 2) {
    for (let la = lat0; la <= lat1; la += 2) {
      const p = projection([lo, la]);
      if (!p) continue;
      x0 = Math.min(x0, p[0]); y0 = Math.min(y0, p[1]);
      x1 = Math.max(x1, p[0]); y1 = Math.max(y1, p[1]);
    }
  }
  return [x0, y0, x1, y1].map(v => +v.toFixed(1));
}
const zones = {
  europe: bbox(-25, 50, 34, 72),
  asie: bbox(26, 150, -11, 58),
  afrique: bbox(-26, 52, -36, 38),
  ameriques: bbox(-170, -28, -56, 75),
  monde: [5, 5, 995, 515]
};

for (const k of Object.keys(countries)) countries[k].a = +countries[k].a.toFixed(2);

fs.mkdirSync(path.join(root, 'data'), {recursive: true});
fs.writeFileSync(path.join(root, 'data/paths.frag'), paths);
fs.writeFileSync(path.join(root, 'data/data.json'), JSON.stringify({countries, zones}));

// Rapport
const targets = Object.entries(countries).filter(([, v]) => v.t);
console.log('Pays à trouver :', targets.length, '| total de zones cliquables :', Object.keys(countries).length);
console.log('Ignorés (hors carte) :', dropped.join(', ') || '—');
console.log('data/paths.frag :', Math.round(paths.length / 1024) + ' Ko');
