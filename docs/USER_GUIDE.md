# Guide d’utilisation

## Choisir l’action

Les trois commandes sont indépendantes. La préparation du RAG ne déclenche pas automatiquement BookToSkill. La création d’un skill ne l’attribue pas automatiquement à un agent. L’attribution accepte un skill personnalisé même si aucun livre n’a été préparé.

La version actuelle utilise des dossiers locaux et une CLI. Les agents sont représentés par des identifiants dans un registre ; aucune interface web ni connexion à un agent distant n’est incluse.

## Installer

Depuis le dossier du dépôt, avec Python 3.10 ou supérieur :

```bash
python -m venv .venv
# Linux/macOS :
source .venv/bin/activate
# Windows PowerShell, à utiliser à la place :
# .\.venv\Scripts\Activate.ps1
python -m pip install .
skillrag --help
```

Pour les formats PDF et Office :

```bash
python -m pip install '.[docling]'
```

Docling peut télécharger des modèles au premier lancement. Prévoir du temps, de l’espace disque et de la mémoire. Les versions doivent être verrouillées et testées avant un déploiement reproductible ; le projet n’inclut pas encore de verrou de dépendances.

## Premier essai : un document simple

Choisir d’abord un document texte ou Markdown dont le contenu est connu, assez long pour dépasser le contrôle minimal de 40 caractères de texte utile.

```bash
skillrag prepare-rag ./ouvrage.md --output ./data/documents
```

La commande renvoie, au format JSON, le chemin du bundle créé. Son nom correspond à l’empreinte SHA-256 de l’original. Ce dossier contient :

| Fichier | Rôle |
|---|---|
| original.* | Copie du document fourni |
| document.md | Texte converti |
| records.jsonl | Passages et localisateurs |
| manifest.json | Identité du document, moteur et tentatives |
| docling.json, assets/ | Données riches et figures, selon l’adaptateur |

Vérifier le texte et les tableaux avant de générer des connaissances. Cette étape prépare les sources : elle ne les insère pas dans Supabase, Qdrant ou une autre base.

Une seconde préparation des mêmes octets dans le même dossier de sortie est refusée pour éviter l’écrasement silencieux. Choisir un autre dossier de sortie pour retraiter avec un nouveau moteur. Une édition modifiée reçoit une nouvelle empreinte.

## Créer le skill depuis ce document

Préparer un modèle compatible avec l’API Chat Completions et les réponses JSON demandées par le toolkit. Il peut être local ou fourni par un service HTTPS. L’URL locale ci-dessous est un exemple ; elle n’installe ni ne démarre un modèle.

```bash
skillrag create-skill ./data/documents/EMPREINTE --output ./data/generated-skills --base-url http://localhost:11434/v1 --model votre-modele
```

Pour un fournisseur nécessitant une clé, définir SKILLRAG_API_KEY dans l’environnement du terminal. Ne pas écrire la clé dans le dépôt. L’endpoint reçoit les passages utilisés pour la synthèse ; choisir un service autorisé à traiter ces documents.

La commande lit le bundle existant, vérifie l’empreinte de l’original et produit un nouveau dossier de skill sans modifier le corpus RAG.

Pour distinguer les ouvrages, ajouter `--title`, `--subject`, `--description` (quand un agent doit utiliser ce skill) et `--edition`. Le nom du skill se termine par l’empreinte de l’édition. Sans ces options, le titre est déduit du nom du fichier.

Une fenêtre qui échoue encore après trois essais interrompt la création. Avec `--allow-partial`, le skill est écrit mais marqué incomplet : `SKILL.md` le signale et `provenance.json` liste les passages concernés. Un document dont plus de 40 % du texte ne produit aucune connaissance est refusé dans tous les cas où `--allow-partial` n’est pas donné.

| Élément du skill | Usage |
|---|---|
| SKILL.md | Instructions et noyau de connaissances compact |
| references/cards.md | Fiches de connaissances générées |
| references/doc-index.jsonl | Index avec preuves exactes et localisateurs |
| references/markdown/ | Source Markdown embarquée |
| references/assets/ | Figures disponibles |
| scripts/search_index.py | Recherche lexicale locale, insensible aux accents, arabe normalisé |
| scripts/_search_index_upstream.py | Copie non modifiée de la recherche zhimaAi, chargée par le script précédent |
| provenance.json | Identité, statut (draft ou incomplete), passages ignorés ou en échec |
| agents/openai.yaml | Métadonnées d’interface |
| provenance.json | Origine, version documentaire et statut brouillon |

Le noyau est limité en taille ; les autres points restent dans les fiches et l’index. Il ne faut pas interpréter ce noyau comme une mémorisation du livre ou une garantie de couverture.

## Relire et attribuer

Comparer les fiches au document : concepts, conditions, exceptions, chiffres, unités et références. Vérifier aussi le contenu des scripts d’un skill personnalisé avant de l’utiliser. Le contrôle automatique des références ne garantit pas la justesse des conclusions.

Après relecture :

```bash
skillrag assign-skill ./data/generated-skills/VERSION --agent finance --registry ./data/registry --reviewed
```

Pour un skill personnalisé existant, remplacer le chemin par son dossier :

```bash
skillrag assign-skill ./mes-skills/ma-methode --agent audit --registry ./data/registry --reviewed
```

Le dossier doit contenir SKILL.md avec un en-tête name et description. Le contrôle actuel est minimal ; les liens symboliques sont refusés. L’option --reviewed déclare que la relecture a été faite ; ce n’est pas une validation automatique ni une installation de skill dans ChatGPT.

Le registre copie le skill sous son empreinte et conserve l’association dans assignments.sqlite. L’agent peut recevoir plusieurs noms de skills. Attribuer une nouvelle version du même nom met à jour l’association active ; les copies précédentes restent conservées.

**Étape d’intégration restante :** le runtime de l’agent doit lire ce registre et charger le dossier correspondant. Le toolkit ne prétend pas avoir activé un agent externe.

## Rechercher dans un skill produit

```bash
python ./data/generated-skills/VERSION/scripts/search_index.py "reorder point"
```

La recherche retourne jusqu’à cinq candidats avec preuves et références. Ce moteur est lexical ; la validation contextuelle revient à l’agent. Le point d’entrée du toolkit remplace la tokenisation upstream (anglais et chinois) : les accents sont ignorés (« sécurité » trouve « securite ») et l’arabe est normalisé. Il n’y a ni racinisation (« réapprovisionner » ne trouve pas « réapprovisionnement ») ni recherche sémantique ; évaluer sur vos documents.

## Difficultés courantes

| Situation | Suite à donner |
|---|---|
| Extraction insuffisante | Vérifier le texte, la taille du document et le moteur ; un scan peut nécessiter un traitement OCR adapté |
| Docling absent | Installer l’option docling dans le même environnement Python |
| Référence de preuve inconnue | La génération est rejetée ; vérifier le modèle et sa réponse structurée |
| Erreur du modèle | Vérifier endpoint, disponibilité, nom du modèle, clé et prise en charge des réponses JSON. Délai dépassé, 429 et 5xx sont repris 3 fois ; 401 et 400 ne le sont pas |
| « Most of the document produced no knowledge » | Plus de 40 % du texte n’a produit aucune connaissance : inspecter le bundle (extraction) et le modèle, ou utiliser `--allow-partial` pour obtenir un skill marqué incomplet |
| Attribution refusée : skill incomplet | Régénérer le skill, ou accepter explicitement avec `--allow-incomplete` |
| Original modifié | Utiliser une nouvelle préparation ; ne pas remplacer l’original dans un bundle existant |
| Skill attribué mais agent inchangé | Implémenter le chargement du registre dans le runtime hôte |
| Résultat lexical peu pertinent | Essayer les termes du document ; la recherche hybride reste à développer |

## Avant le test sur un vrai ouvrage

Choisir une édition autorisée, un modèle accessible et une dizaine de questions dont les réponses sont connues. Comparer source, skill et réponses de l’agent ; relever les omissions et erreurs, puis mesurer temps et coût. Les douze tests actuels valident des mécanismes logiciels avec modèle simulé, pas la qualité métier d’un ouvrage.

Conserver les livres, les données clients, les sorties et les clés hors du dépôt public. La publication du code sur GitHub n’est pas un déploiement sur serveur.
