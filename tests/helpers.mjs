// Outils communs aux tests : lancement d'un Chrome sans interface, chemin du jeu construit, dossier de captures.
import fs from 'fs';
import path from 'path';
import {fileURLToPath, pathToFileURL} from 'url';
import puppeteer from 'puppeteer-core';

const here = path.dirname(fileURLToPath(import.meta.url));
// Une page HTML par jeu : index.html, geo.html, additions.html, soustractions.html, multiplications.html
export const pageUrl = file => pathToFileURL(path.join(here, '..', 'dist', file)).href;
export const SHOTS = path.join(here, 'out') + path.sep;      // captures d'écran (ignoré par git)
fs.mkdirSync(SHOTS, {recursive: true});
export const sleep = ms => new Promise(r => setTimeout(r, ms));

// Cherche un Chrome/Chromium installé ; sinon repli sur le Chromium embarqué par @sparticuz/chromium (Linux).
// On peut forcer le choix avec la variable d'environnement CHROME_PATH.
const CANDIDATES = [
  process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'
].filter(Boolean);

export async function launch() {
  const viewport = {width: 1280, height: 760};
  const found = CANDIDATES.find(p => fs.existsSync(p));
  if (found) return puppeteer.launch({executablePath: found, headless: true, defaultViewport: viewport});
  let m;
  try { m = (await import('@sparticuz/chromium')).default; }
  catch { throw new Error('Chrome introuvable : installez Google Chrome ou définissez CHROME_PATH.'); }
  return puppeteer.launch({args: m.args, executablePath: await m.executablePath(), headless: 'shell', defaultViewport: viewport});
}
