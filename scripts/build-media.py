#!/usr/bin/env python3
"""Télécharge les drapeaux et les photos du « mode aidé » et les range dans data/ (images incluses en base64) :

  data/flags.json  : { code ISO3: "data:image/png;base64,…" }            drapeaux (flagcdn.com, domaine public)
  data/photos.json : { code département: {t: monument, i: "data:image/jpeg;base64,…", c: crédit} }
  data/photos-pays.json : { code ISO3: {t: lieu, i: …, c: crédit} }   (même principe, un lieu emblématique par pays)
                     photos issues de Wikipédia / Wikimedia Commons (licences libres : le crédit de chaque photo est conservé)

À relancer seulement pour changer les images :   python3 scripts/build-media.py && npm run build
Nécessite Internet et Python 3 ; le redimensionnement des photos utilise Pillow s'il est installé, sinon « sips » (macOS).
Le jeu final, lui, n'a besoin d'aucune connexion : tout est embarqué dans les pages.
"""
import base64, concurrent.futures as cf, html, json, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
UA = {'User-Agent': 'JeuxExplorateurs/1.0 (jeu educatif hors ligne; contact: plutonmail35@gmail.com)'}
FLAG_W = int(os.environ.get('FLAG_W', '80'))     # largeur des drapeaux (px)
PHOTO_W = int(os.environ.get('PHOTO_W', '180'))  # largeur des photos (px)

# Un lieu emblématique par département : titre de la page Wikipédia en français
PLACES = {
 '01':'Monastère royal de Brou','02':'Cathédrale Notre-Dame de Laon','03':'Château de La Palice','04':'Citadelle de Sisteron',
 '05':'Briançon','06':'Promenade des Anglais','07':'Pont d\'Arc','08':'Charleville-Mézières','09':'Château de Foix',
 '10':'Cathédrale Saint-Pierre-et-Saint-Paul de Troyes','11':'Cité de Carcassonne','12':'Viaduc de Millau',
 '13':'Basilique Notre-Dame-de-la-Garde','14':'Abbaye aux Hommes','15':'Puy Mary','16':'Cathédrale Saint-Pierre d\'Angoulême',
 '17':'Île d\'Oléron','18':'Cathédrale Saint-Étienne de Bourges','19':'Collonges-la-Rouge','21':'Hospices de Beaune',
 '22':'Côte de granit rose','23':'Aubusson (Creuse)','24':'Château de Beynac','25':'Citadelle de Besançon',
 '26':'Palais idéal du facteur Cheval','27':'Giverny','28':'Cathédrale Notre-Dame de Chartres','29':'Pointe du Raz',
 '2A':'Bonifacio','2B':'Calvi','30':'Pont du Gard','31':'Capitole de Toulouse','32':'Cathédrale Sainte-Marie d\'Auch',
 '33':'Dune du Pilat','34':'Place de la Comédie (Montpellier)','35':'Saint-Malo','36':'Château de Valençay',
 '37':'Château de Chenonceau','38':'Grenoble','39':'Cascades du Hérisson','40':'Hossegor','41':'Château de Chambord',
 '42':'Stade Geoffroy-Guichard','43':'Le Puy-en-Velay','44':'Château des ducs de Bretagne',
 '45':'Cathédrale Sainte-Croix d\'Orléans','46':'Pont Valentré','47':'Pont-canal d\'Agen','48':'Gorges du Tarn',
 '49':'Château d\'Angers','50':'Mont-Saint-Michel','51':'Cathédrale Notre-Dame de Reims','52':'Langres','53':'Château de Laval',
 '54':'Place Stanislas','55':'Fort de Douaumont','56':'Alignements de Carnac','57':'Cathédrale Saint-Étienne de Metz',
 '58':'Palais ducal de Nevers','59':'Vieille Bourse de Lille','60':'Château de Pierrefonds','61':'Le Pin-au-Haras',
 '62':'Cap Blanc-Nez','63':'Puy de Dôme','64':'Pic du Midi d\'Ossau','65':'Sanctuaire Notre-Dame de Lourdes',
 '66':'Château royal de Collioure','67':'Cathédrale Notre-Dame de Strasbourg','68':'Colmar',
 '69':'Basilique Notre-Dame de Fourvière','70':'Chapelle Notre-Dame du Haut','71':'Abbaye de Cluny',
 '72':'Cathédrale Saint-Julien du Mans','73':'Lac du Bourget','74':'Lac d\'Annecy','75':'Tour Eiffel','76':'Étretat',
 '77':'Château de Fontainebleau','78':'Château de Versailles','79':'Marais poitevin','80':'Cathédrale Notre-Dame d\'Amiens',
 '81':'Cathédrale Sainte-Cécile d\'Albi','82':'Abbaye Saint-Pierre de Moissac','83':'Saint-Tropez','84':'Palais des papes d\'Avignon',
 '85':'Puy du Fou','86':'Baptistère Saint-Jean de Poitiers','87':'Gare de Limoges-Bénédictins','88':'Gérardmer',
 '89':'Basilique Sainte-Marie-Madeleine de Vézelay','90':'Lion de Belfort','91':'Château de Chamarande','92':'La Défense',
 '93':'Basilique Saint-Denis','94':'Château de Vincennes','95':'Abbaye de Royaumont',
}

# Un lieu emblématique par pays : titre de la page Wikipédia en français
PLACES_PAYS = {
 'AFG':'Minaret de Djam','AGO':'Luanda','ALB':'Berat','AND':'Casa de la Vall','ARE':'Burj Khalifa','ARG':'Glacier Perito Moreno',
 'ARM':'Mont Ararat','ATG':"Nelson's Dockyard",'AUS':'Opéra de Sydney','AUT':'Château de Schönbrunn','AZE':'Tour de la Vierge',
 'BDI':'Lac Tanganyika','BEL':'Grand-Place de Bruxelles','BEN':"Palais royaux d'Abomey",'BFA':'Ruines de Loropéni',
 'BGD':'Mosquée aux soixante coupoles','BGR':'Monastère de Rila','BHR':'Fort de Bahreïn','BHS':'Nassau (Bahamas)','BIH':'Stari Most',
 'BLR':'Château de Mir','BLZ':'Grand Trou bleu','BOL':"Salar d'Uyuni",'BRA':'Christ Rédempteur','BRB':'Bridgetown',
 'BRN':'Mosquée Omar Ali Saifuddin','BTN':'Monastère de Taktsang','BWA':"Delta de l'Okavango",'CAF':'Cathédrale Notre-Dame de Bangui','CAN':'Chutes du Niagara',
 'CHE':'Cervin','CHL':'Île de Pâques','CHN':'Grande Muraille de Chine','CIV':'Basilique Notre-Dame de la Paix de Yamoussoukro',
 'CMR':'Mont Cameroun','COD':'Parc national des Virunga','COG':'Brazzaville','COL':'Château de San Felipe de Barajas','COM':'Mont Karthala',
 'CPV':'Pico do Fogo','CRI':'Volcan Arenal','CUB':'La Havane','CYP':'Kourion','CZE':'Pont Charles','DEU':'Porte de Brandebourg',
 'DJI':'Lac Assal','DMA':'Morne Trois Pitons','DNK':'Nyhavn','DOM':'Zone coloniale de Saint-Domingue','DZA':"Casbah d'Alger",
 'ECU':'Cotopaxi','EGY':'Pyramides de Gizeh','ERI':'Asmara','ESP':'Sagrada Família','EST':'Tallinn','ETH':'Églises monolithiques de Lalibela',
 'FIN':"Cathédrale d'Helsinki",'FJI':'Suva','FRA':'Tour Eiffel','FSM':'Nan Madol','GAB':'Libreville','GBR':'Big Ben','GEO':'Cathédrale de la Sainte-Trinité de Tbilissi',
 'GHA':'Château de Cape Coast','GIN':'Mont Nimba','GMB':'Île de Kunta Kinteh','GNB':'Archipel des Bijagos','GNQ':'Malabo','GRC':'Parthénon','GRD':'Saint-Georges (Grenade)',
 'GRL':"Fjord glacé d'Ilulissat",'GTM':'Tikal','GUY':'Chutes Kaieteur','HND':'Copán','HRV':'Dubrovnik','HTI':'Citadelle Laferrière',
 'HUN':'Parlement de Budapest','IDN':'Borobudur','IND':'Taj Mahal','IRL':'Falaises de Moher','IRN':'Persépolis','IRQ':"Ziggurat d'Ur",
 'ISL':'Gullfoss','ISR':'Mur des Lamentations','ITA':'Colisée','JAM':'Montego Bay','JOR':'Pétra','JPN':'Mont Fuji','KAZ':'Baïterek',
 'KEN':'Masai Mara','KGZ':'Issyk Kul','KHM':'Angkor Vat','KIR':'Tarawa','KNA':'Brimstone Hill','KOR':'Palais Gyeongbokgung',
 'KWT':'Tours du Koweït','LAO':'Luang Prabang','LBN':'Baalbek','LBR':'Parc national de Sapo','LBY':'Leptis Magna','LCA':'Gros Piton','LIE':'Château de Vaduz',
 'LKA':'Sigirîya','LSO':'Maletsunyane Falls','LTU':'Château de Trakai','LUX':'Ville de Luxembourg','LVA':'Riga','MAR':'Mosquée Hassan II',
 'MCO':'Casino de Monte-Carlo','MDA':'Chișinău','MDG':'Allée des baobabs','MDV':'Malé','MEX':'Chichén Itzá','MHL':'Majuro',
 'MKD':"Lac d'Ohrid",'MLI':'Grande Mosquée de Djenné','MLT':'Cathédrale Saint-Jean de La Valette','MMR':'Pagode Shwedagon','MNE':'Bouches de Kotor',
 'MNG':'Statue équestre de Gengis Khan','MOZ':'Île de Mozambique','MRT':"Banc d'Arguin",'MUS':'Le Morne Brabant','MWI':'Lac Malawi',
 'MYS':'Tours Petronas','NAM':'Sossusvlei','NER':'Agadez','NGA':'Zuma Rock','NIC':'Grenade (Nicaragua)','NLD':'Moulins de Kinderdijk',
 'NOR':'Geirangerfjord','NPL':'Mont Everest','NRU':'Aiwo','NZL':'Milford Sound','OMN':'Fort de Nizwa','PAK':'Mosquée Badshahi',
 'PAN':'Canal de Panama','PER':'Machu Picchu','PHL':'Rizières en terrasses de Banaue','PLW':'Rock Islands','PNG':'Port Moresby',
 'POL':'Château de Malbork','PRK':'Arc de triomphe de Pyongyang','PRT':'Tour de Belém','PRY':'Asunción','QAT':"Musée d'art islamique de Doha",
 'ROU':'Château de Bran','RUS':'Cathédrale Basile-le-Bienheureux','RWA':'Kigali','SAU':'Abraj Al-Bait','SDN':'Pyramides de Méroé','SEN':'Lac Rose',
 'SGP':'Marina Bay Sands','SLB':'Honiara','SLE':'Freetown','SLV':'San Salvador','SMR':'Mont Titano','SOM':'Mogadiscio','SRB':'Forteresse de Belgrade',
 'SSD':'Parc national de Boma','STP':'Pico Cão Grande','SUR':'Paramaribo','SVK':'Château de Bratislava','SVN':'Lac de Bled','SWE':'Gamla stan','SWZ':'Mbabane',
 'SYC':"Anse Source d'Argent",'SYR':'Palmyre','TCD':"N'Djaména",'TGO':'Lomé','THA':'Wat Arun','TJK':'Douchanbé','TKM':'Cratère de Darvaza',
 'TLS':'Statue du Christ-Roi de Dili','TON':"Nuku'alofa",'TTO':"Port-d'Espagne",'TUN':"Amphithéâtre d'El Djem",'TUR':'Sainte-Sophie','TZA':'Kilimandjaro','UGA':'Tombes des rois du Buganda à Kasubi',
 'UKR':'Cathédrale Sainte-Sophie de Kiev','URY':'Colonia del Sacramento','USA':'Statue de la Liberté','UZB':'Place du Registan',
 'VAT':'Basilique Saint-Pierre de Rome','VCT':'Kingstown','VEN':'Salto Ángel','VNM':"Baie d'Along",'VUT':'Port-Vila','WSM':'Apia','YEM':'Sanaa',
 'ZAF':'Montagne de la Table','ZMB':'Chutes Victoria','ZWE':'Grand Zimbabwe',
}

def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return r.read()
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(2 + 3 * i)

def data_uri(raw, mime): return 'data:%s;base64,%s' % (mime, base64.b64encode(raw).decode())

def flags():
    codes = json.load(open(os.path.join(ROOT, 'data/data.json'), encoding='utf8'))['countries']
    c2 = {c['cca3']: c['cca2'].lower() for c in json.loads(get('https://raw.githubusercontent.com/mledoze/countries/master/countries.json'))}
    c2['XKX'] = 'xk'                                   # Kosovo
    def one(code):
        try: return code, data_uri(get('https://flagcdn.com/w%d/%s.png' % (FLAG_W, c2[code])), 'image/png')
        except Exception: return code, None
    with cf.ThreadPoolExecutor(8) as ex: res = dict(ex.map(one, [k for k in codes if k in c2]))
    out = {k: v for k, v in res.items() if v}
    print('Drapeaux :', len(out), '/', len(codes), '| sans drapeau :', sorted(set(codes) - set(out)))
    json.dump(out, open(os.path.join(ROOT, 'data/flags.json'), 'w'), separators=(',', ':'))
    print('data/flags.json :', os.path.getsize(os.path.join(ROOT, 'data/flags.json')) // 1024, 'Ko')

def shrink(raw):
    try:
        from PIL import Image; import io
        im = Image.open(io.BytesIO(raw)).convert('RGB'); im.thumbnail((PHOTO_W, PHOTO_W))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=55, optimize=True); return b.getvalue()
    except ImportError:
        d = tempfile.mkdtemp()
        try:
            src, dst = os.path.join(d, 'a'), os.path.join(d, 'b.jpg')
            open(src, 'wb').write(raw)
            subprocess.run(['sips', '-Z', str(PHOTO_W), '--setProperty', 'format', 'jpeg', '--setProperty', 'formatOptions', '55', src, '--out', dst], check=True, capture_output=True)
            return open(dst, 'rb').read()
        finally: shutil.rmtree(d, ignore_errors=True)

BAD_NAME = re.compile(r'(carte|map|locator|flag|drapeau|blason|coat|logo|armoiries|emblem|collage|montage|mosaic|panorama_of_city|vue_de_la_ville)', re.I)

def search(title):
    r = json.loads(get('https://fr.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=4&srsearch=' + urllib.parse.quote(title)))
    return [h['title'] for h in r['query']['search']]

def photo(code, title):
    """La page nommée d'abord ; à défaut (page absente, pas de photo), les premiers résultats de recherche."""
    try: return photo_of(code, title, title)
    except Exception as first:
        for alt in search(title):
            try: return photo_of(code, title, alt)
            except Exception: pass
        raise first

def photo_of(code, title, page):
    s = json.loads(get('https://fr.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(page.replace(' ', '_'), safe='')))
    thumb = (s.get('thumbnail') or {}).get('source')
    if not thumb: raise ValueError('pas d’image')
    m = re.search(r'/thumb/\w/\w\w/([^/]+)/', thumb) or re.search(r'/commons/\w/\w\w/([^/?]+)', thumb)
    fname = urllib.parse.unquote(m.group(1)) if m else ''
    if not re.search(r'\.jpe?g$', fname, re.I) or BAD_NAME.search(fname): raise ValueError('pas une photo : ' + fname)
    url = re.sub(r'/(?:lang\w+-)?\d+px-', '/%dpx-' % (PHOTO_W if PHOTO_W in (120, 250, 330, 500, 960) else 250), thumb.split('?')[0])
    img = shrink(get(url))
    meta = json.loads(get('https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&format=json&titles=' + urllib.parse.quote('File:' + fname)))
    info = next(iter(meta['query']['pages'].values())).get('imageinfo', [{}])[0].get('extmetadata', {})
    clean = lambda k: html.unescape(re.sub(r'<[^>]+>', '', info.get(k, {}).get('value', ''))).strip()
    credit = ' · '.join(x for x in (clean('Artist')[:80] or 'Auteur inconnu', clean('LicenseShortName') or 'licence libre', 'Wikimedia Commons') if x)
    return {'t': title, 'i': data_uri(img, 'image/jpeg'), 'c': credit, 'f': fname}

def photos(places, outname):
    out, bad = {}, {}
    path = os.path.join(ROOT, 'data', outname)
    old = json.load(open(path, encoding='utf8')) if os.path.exists(path) else {}
    def one(kv):
        code, title = kv
        if old.get(code, {}).get('t') == title: return code, old[code], None      # déjà téléchargée
        try: return code, photo(code, title), None
        except Exception as e: return code, None, str(e)
    with cf.ThreadPoolExecutor(4) as ex:
        for code, p, err in ex.map(one, places.items()):
            if p: out[code] = p
            else: bad[code] = err
    print(outname, ':', len(out), '/', len(places))
    for c, e in sorted(bad.items()): print('  ! %s %s : %s' % (c, places[c], e))
    json.dump(out, open(path, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('data/' + outname, ':', os.path.getsize(path) // 1024, 'Ko')

if __name__ == '__main__':
    what = sys.argv[1:] or ['flags', 'photos', 'photos-pays']
    if 'flags' in what: flags()
    if 'photos' in what: photos(PLACES, 'photos.json')
    if 'photos-pays' in what: photos(PLACES_PAYS, 'photos-pays.json')
