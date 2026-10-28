# Universal SkillRAG Toolkit

Un dépôt générique, trois fonctions indépendantes : préparer les documents pour un RAG, transformer un livre en skill, attribuer un skill à un agent.

## Installation

Python 3.10 ou supérieur :

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

Choisir le bundle du livre dans le catalogue documentaire, puis :

```bash
skillrag create-skill ./data/documents/EMPREINTE --output ./data/generated-skills --base-url http://localhost:11434/v1 --model votre-modele
```

Le document préparé est réutilisé sans relancer ni modifier le RAG. Produit un skill autonome : `SKILL.md` avec noyau compact, fiches, index lexical, sources embarquées et provenance. Le skill peut être utilisé sans connexion au RAG d'origine. La génération reste un brouillon à relire ; aucune couverture de 70–80 % n'est garantie.

Le modèle compatible OpenAI doit être explicitement configuré. Pour un service nécessitant une clé, utiliser `SKILLRAG_API_KEY`. Aucun appel externe sans endpoint fourni. Vérifier les conditions de confidentialité du fournisseur choisi.

## 3. Attribuer un skill à un agent

Après relecture, attribuer soit un skill créé depuis un livre, soit un skill personnalisé existant :

```bash
skillrag assign-skill ./mon-skill --agent finance --registry ./data/registry --reviewed
```

Le registre conserve une copie identifiée par empreinte et l'association agent/skill. Plusieurs skills peuvent être attribués à un agent ; une nouvelle version du même nom remplace son association active. Cette opération n'appelle pas de modèle et ne modifie pas le RAG.

**Le registre local ne charge pas automatiquement un agent externe.** Le système hôte doit lire l'association et charger le skill. L'interface graphique de sélection livre/agent et la connexion à un catalogue RAG distant ne sont pas encore implémentées.

## Réutilisation des deux BookToSkill

- [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) : spécification de génération conservée ; sa philosophie guide la synthèse structurée.
- [zhimaAi/BookToSkill](https://github.com/zhimaAi/BookToSkill) : constructeur/validateur et recherche lexicale réellement réutilisés.

Les versions et licences sont consignées dans [THIRD_PARTY.md](THIRD_PARTY.md). Ce n'est pas une fusion de toutes leurs fonctions. Docling reste optionnel ; OCRmyPDF, LangExtract et xerj ne sont pas intégrés.

## Vérification et limites

Douze tests passent : provenance, secours, erreurs, refus des références inventées, conservation du RAG pendant la création du skill et attribution d'un skill personnalisé sans RAG. La génération est testée avec un modèle simulé. Docling et la qualité de synthèse sur un vrai ouvrage restent à vérifier. Les recherches lexicales upstream sont surtout adaptées à l'anglais/chinois ; la recherche française/arabe doit être améliorée et évaluée.

Les documents, sorties et secrets restent hors du dépôt public. Isoler les convertisseurs avant utilisation en production sur des fichiers non fiables. Le système hôte applique les autorisations et le cloisonnement des clients.

- [Architecture](docs/ARCHITECTURE.md)
- [Implémentation](docs/IMPLEMENTATION.md)
- [Évaluation](docs/EVALUATION.md)
- [Feuille de route](docs/ROADMAP.md)
