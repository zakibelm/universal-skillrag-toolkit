# Universal SkillRAG Toolkit

Outil générique pour transformer des ouvrages et documents en connaissances structurées pour agents IA, tout en conservant l'accès aux sources, tableaux et images.

## Statut

Version 0.1 : spécifications et structure de départ. Aucun pipeline de conversion, moteur OCR, modèle de synthèse ou serveur MCP n'est encore implémenté. Les performances restent à mesurer.

## Objectif

Enrichir les skills existants d'un agent avec un complément documentaire spécialisé et réutilisable dans différents systèmes RAG. Le toolkit ne dépend d'aucun secteur, fournisseur de modèles ou framework d'agents.

Deux approches inspirent la conception :
- [virgiliojr94/book-to-skill](https://github.com/virgiliojr94/book-to-skill) : connaissances et méthodes structurées.
- [zhimaAi/BookToSkill](https://github.com/zhimaAi/BookToSkill) : indexation et récupération ciblée des sources.

Il s'agit d'une conception originale inspirée des approches discutées, et non d'une intégration ou copie de leur code. Vérifier les licences à un commit précis avant toute réutilisation.

## Les couches

1. Noyau de connaissances : concepts, méthodes, formules, limites.
2. Fiches thématiques : exceptions, exemples, glossaire et règles de décision.
3. Index : recherche lexicale et sémantique avec filtres.
4. Preuves : original, Markdown, passages, tableaux et images.
5. Validation : traçabilité, qualité d'extraction et évaluation des réponses.

Le noyau est chargé explicitement lors de l'activation du complément. Les fiches et preuves sont chargées à la demande. Un skill ne modifie pas les poids du modèle et ne garantit aucune couverture de 70–80 % d'un livre.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Format des références](docs/DATA_MODEL.md)
- [Évaluation comparative](docs/EVALUATION.md)
- [Feuille de route](docs/ROADMAP.md)
- [Exemple de référence](examples/source-record.json)

## Limites actuelles

Pas encore d'installation exécutable. Les documents confidentiels ne doivent pas être déposés dans ce dépôt public. Utiliser uniquement des ouvrages pour lesquels les droits de traitement et d'utilisation sont établis. Les synthèses et descriptions générées doivent rester distinguées des extraits originaux.
