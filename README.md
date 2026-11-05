# 🎮 Les Jeux des Explorateurs

Des petits jeux d'une minute pour les enfants (niveau CP) :

- 🌍 **Géo Explorateurs** : trouve les pays sur la carte du monde (Europe, Asie, Afrique, Amériques ou monde entier).
- ➕ ➖ ✖️ **Jeux de calcul** : additions, soustractions et multiplications, avec trois niveaux chacune.

Chaque partie dure **60 secondes**. À la fin, on enregistre son prénom et on retrouve les meilleurs scores.

## Jouer

Ouvrez simplement **`dist/index.html`** (le menu principal) dans un navigateur (Chrome, Edge, Safari, Firefox) par double-clic.

**Sur téléphone ou tablette**, ouvrez plutôt **`dist/jeux-explorateurs.html`** : toutes les pages sont dans ce seul fichier, ce qui évite l'erreur « Impossible d'accéder à votre fichier » quand le téléphone n'ouvre qu'un fichier isolé.
Rien à installer, ça fonctionne sans connexion Internet, sur Mac comme sur Windows.
Chaque jeu a sa propre page (`geo.html`, `additions.html`…) ; gardez les fichiers de `dist/` dans le même dossier.
Les scores sont gardés sur l'ordinateur utilisé.

## Modifier le jeu (avec Claude Code ou à la main)

Le code source est dans `src/` ; le fichier à distribuer est reconstruit par :

```
npm install        # une seule fois
npm run build      # produit les pages de dist/
npm test           # tests de bout en bout (nécessite Google Chrome)
```

Le fichier **`CLAUDE.md`** décrit le projet en détail (contraintes, architecture, pièges, idées d'évolution) :
c'est le point de départ pour continuer le développement avec Claude Code.

## Crédits des données

Fond de carte : [Natural Earth](https://www.naturalearthdata.com/) (domaine public), via les paquets npm `world-atlas` et `world-countries`.
