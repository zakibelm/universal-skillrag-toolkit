# Universal SkillRAG Toolkit

**Version : 0.2.0 — première version exécutable, en validation.**

**Transformer des documents en sources consultables pour un RAG et en skills réutilisables pour des agents IA, avec deux traitements distincts et une attribution explicite des skills.**

Universal SkillRAG Toolkit est une bibliothèque Python et un outil en ligne de commande. Il réunit dans un même dépôt la préparation documentaire, la création de connaissances structurées depuis un livre et la gestion locale des associations entre agents et skills.

Son objectif est de réutiliser des composants existants et de conserver les références aux sources, sans imposer un métier, un fournisseur de modèles ou une base vectorielle.

## Les trois fonctions

| Fonction | Entrée | Résultat | Indépendance |
|---|---|---|---|
| Préparer le RAG | Document local | Original conservé, Markdown, passages et localisateurs | Ne crée aucun skill |
| Créer un skill de livre | Document déjà préparé et modèle configuré | Skill autonome avec noyau, fiches et preuves | Ne reconstruit pas le RAG |
| Attribuer un skill | Skill de livre ou skill personnalisé et identifiant d’agent | Copie versionnée et association dans le registre local | Aucun RAG ou modèle requis |

**Exemple d’usage :** un agent de finance conserve ses skills métier. On sélectionne un ouvrage de comptabilité financière déjà conservé, on génère un complément de connaissances, on le relit, puis on l’attribue à cet agent. Le même outil peut servir en optique, logistique, audit ou tout autre domaine ; aucun traitement spécialisé n’est codé en dur.

Un skill est un dossier de connaissances et d’instructions chargé par un agent. Un corpus RAG est une collection de sources dans laquelle un système recherche des passages. Le skill produit ici embarque ses références ; il reste utilisable sans connexion au RAG d’origine. Le chargement effectif dépend du runtime de l’agent.

## État de la version 0.2

Le moteur Python, les trois commandes et le registre local sont implémentés. Douze tests ont été exécutés avec succès sur des données synthétiques, avec modèle simulé pour la génération.

L’interface graphique « Skills », le catalogue documentaire distant, l’activation dans un agent externe et le déploiement serveur restent à réaliser. L’adaptateur Docling est écrit mais n’a pas encore été validé sur un ouvrage réel dans ce projet. La présence de tests ne démontre pas la qualité des synthèses produites par un vrai modèle.

## Documentation

- [Historique des versions](CHANGELOG.md)
- [Guide d’utilisation et premier essai](docs/USER_GUIDE.md)
- [Architecture et séparation des fonctions](docs/ARCHITECTURE.md)
- [Interfaces Python et formats produits](docs/IMPLEMENTATION.md)
- [Protocole d’évaluation](docs/EVALUATION.md)
- [Feuille de route](docs/ROADMAP.md)
- [Composants repris, versions et licences](THIRD_PARTY.md)

## Installation

Python 3.10 ou supérieur. Télécharger le dépôt, ouvrir un terminal dans son dossier, puis :

```bash
pip install .
# Option pour PDF/Office :
pip install '.[docling]'
python -m unittest discover -s tests -v
```

## 1. Préparer la documentation du RAG

```bash
skillrag prepare-rag ouvrage.md --output ./data/documents
```

Produit un bundle identifié par SHA-256 : original, Markdown, références JSONL, manifeste et, avec Docling, figures et données structurées. Aucun skill n'est créé. C'est une préparation de corpus ; l'insertion dans une base vectorielle n'est pas encore implémentée.

Le moteur natif traite Markdown/texte. L'adaptateur Docling optionnel couvre PDF/DOCX/PPTX/HTML et conserve ses localisateurs. Le routage sélectionne un moteur compatible ; les adaptateurs peuvent être remplacés ou complétés par des secours. Les sorties vides ou partielles sont rejetées. Ces contrôles structurels ne prouvent pas l'exhaustivité du contenu.

## 2. Créer un skill depuis un livre déjà conservé

Dans la version CLI, choisir le dossier du livre parmi les bundles locaux. La sélection dans une interface de catalogue est une évolution prévue. Remplacer `EMPREINTE` et `votre-modele` par les valeurs réelles :

```bash
skillrag create-skill ./data/documents/EMPREINTE --output ./data/generated-skills --base-url http://localhost:11434/v1 --model votre-modele
```

Options d'identité : `--title`, `--subject`, `--description` (quand un agent doit l'utiliser, 500 caractères maximum) et `--edition`. Sans elles, le titre vient du nom du fichier. Le nom du skill se termine toujours par l'empreinte de l'édition : deux ouvrages, ou deux éditions, ne se confondent jamais dans un registre.

La génération se fait par fenêtres de passages consécutifs (4000 caractères maximum). Un modèle peut renvoyer zéro point pour une fenêtre sans connaissance (titre, légende, bruit de page), à condition d'en donner la raison. Les erreurs transitoires sont reprises 3 fois au plus. Un échec persistant interrompt la création ; avec `--allow-partial`, le skill est écrit mais marqué **incomplet**, avec les passages concernés dans `provenance.json`. Un document dont plus de 40 % du texte ne produit aucune connaissance est refusé (extraction ou modèle probablement défaillants).

Le document préparé est réutilisé sans relancer ni modifier le RAG. Produit un skill autonome : `SKILL.md` avec noyau compact, fiches, index lexical, sources embarquées et provenance. Le skill peut être utilisé sans connexion au RAG d'origine. La génération reste un brouillon à relire ; aucune couverture de 70–80 % n'est garantie.

Le modèle compatible OpenAI doit être explicitement configuré. Pour un service nécessitant une clé, utiliser `SKILLRAG_API_KEY`. Aucun appel externe sans endpoint fourni. Vérifier les conditions de confidentialité du fournisseur choisi.

## 3. Attribuer un skill à un agent

Après relecture, attribuer soit un skill créé depuis un livre, soit un skill personnalisé existant :

```bash
skillrag assign-skill ./mon-skill --agent finance --registry ./data/registry --reviewed
```

Un skill marqué incomplet est refusé, sauf `--allow-incomplete`. Le registre conserve une copie identifiée par empreinte et l'association agent/skill. Plusieurs skills peuvent être attribués à un agent ; une nouvelle version du même nom remplace son association active. Cette opération n'appelle pas de modèle et ne modifie pas le RAG.

**Le registre local ne charge pas automatiquement un agent externe.** Le système hôte doit lire l'association et charger le skill. L'interface graphique de sélection livre/agent et la connexion à un catalogue RAG distant ne sont pas encore implémentées.

## Réutilisation des deux BookToSkill

- [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) : **texte réutilisé** ; sa section « Philosophy » est insérée dans le prompt. Aucun code exécuté.
- [zhimaAi/BookToSkill](https://github.com/zhimaAi/BookToSkill) : `build_skill.py` est **appelé** (validation et génération du format de skill) ; `search_index.py` est **copié sans modification** dans chaque skill et enveloppé par un point d'entrée du toolkit qui corrige la tokenisation.

Les versions, licences et le détail fichier par fichier sont dans [THIRD_PARTY.md](THIRD_PARTY.md). Ce n'est pas une fusion de toutes leurs fonctions. Docling reste optionnel ; OCRmyPDF, LangExtract et xerj ne sont pas intégrés.

## Vérification et limites

Trente-trois tests passent : provenance, secours, erreurs, refus des références inventées, séparation RAG/skill/attribution, identité propre à chaque skill, reprises et génération incomplète, recherche française et arabe, et le chemin HTTP de `CompatibleModel` contre un fournisseur simulé local (succès, délai dépassé, réponses invalides, erreurs). La génération est testée avec un modèle simulé. Docling et la qualité de synthèse sur un vrai ouvrage restent à vérifier. La recherche livrée dans chaque skill ignore les accents et normalise l'arabe (diacritiques, variantes de l'alef) ; elle ne fait ni racinisation ni recherche sémantique, et n'a été éprouvée que sur des exemples synthétiques.

Les documents, sorties et secrets restent hors du dépôt public. Isoler les convertisseurs avant utilisation en production sur des fichiers non fiables. Le système hôte applique les autorisations et le cloisonnement des clients.

- [Architecture](docs/ARCHITECTURE.md)
- [Implémentation](docs/IMPLEMENTATION.md)
- [Évaluation](docs/EVALUATION.md)
- [Feuille de route](docs/ROADMAP.md)
