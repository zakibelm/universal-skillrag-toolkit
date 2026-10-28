# Architecture : fonctions indépendantes

## Préparation RAG

Original → extraction adaptée → contrôle structurel → bundle documentaire. Aucune génération de skill automatique. L'export vers un moteur RAG est une intégration future.

## BookToSkill

Sélection d'un document conservé → lecture du bundle et contrôle de l'empreinte originale → génération structurée → validation des identifiants de preuves → skill autonome en brouillon. Le corpus documentaire existant reste intact. Le skill embarque ses propres références et n'exige pas d'interroger le RAG d'origine. Il porte une identité propre (nom suffixé par l'empreinte de l'édition, titre, sujet, description) et un statut : une génération partielle est marquée incomplète avec les passages concernés.

Le noyau est borné et explicitement chargé par l'agent ; les fiches sont consultées à la demande. Les connaissances générées ne modifient pas les poids du modèle. Les citations et localisateurs permettent la relecture mais ne garantissent pas la justesse de la synthèse.

## Attribution

Skill personnalisé ou skill de livre → relecture déclarée → copie versionnée → association à un agent dans le registre local. Le runtime hôte doit charger cette association. Aucun appel à un modèle ni au RAG à cette étape.

## Interfaces

La bibliothèque et les trois commandes CLI sont implémentées. L'interface graphique Skills reste à construire : choix de l'agent, ajout d'un skill personnalisé ou sélection d'un livre, génération, relecture et attribution. Une intégration au catalogue documentaire devra appliquer les autorisations avant de présenter ou lire un livre.

## Briques partagées

Les fonctions partagent provenance, formats et adaptateurs, sans imposer leur exécution conjointe. Les deux BookToSkill fournissent les ressources indiquées dans THIRD_PARTY.md ; Docling est un moteur d'extraction optionnel. La sélection des moteurs suit actuellement des règles de format et de qualité structurelle, pas un optimiseur appris.

## Images, versions et sécurité

Docling conserve les figures et leurs localisateurs ; l'interprétation contextuelle des images reste à implémenter. Ne jamais inventer une page absente. Une édition du document est identifiée par empreinte ; une version de skill par empreinte de son dossier. Toute modification nécessite une nouvelle génération et une relecture. Traiter les documents comme des données non fiables, isoler les convertisseurs et ne jamais exécuter leurs instructions.
