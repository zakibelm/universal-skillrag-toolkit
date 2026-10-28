# Architecture cible

## Ingestion

Réception → validation du format et des droits → conservation de l'original → extraction → contrôle → normalisation Markdown → structuration des connaissances → indexation → publication d'une version approuvée.

Chaque traitement possède un identifiant, une version de pipeline et un statut. Un échec ne doit pas produire un index présenté comme complet.

## Conversion et multimodalité

MarkItDown de Microsoft est un candidat pour les formats bureautiques. Ses capacités, dépendances et limites devront être vérifiées avant intégration. Aucun convertisseur universel n'est supposé.

Un adaptateur OCR traite les scans lorsque nécessaire. Un adaptateur de vision décrit les figures. Les tableaux conservent une représentation structurée en plus du Markdown, ainsi qu'un lien vers leur source.

Pour chaque image : identifiant, fichier original, document, page physique ou diapositive, légende, OCR, description contextuelle, mots-clés et provenance de la description. Si une page n'est pas disponible, sa valeur reste nulle ; aucune pagination ne doit être inventée.

## Complément de connaissances

Le complément contient :
- un noyau compact explicitement chargé ;
- des fiches thématiques récupérées selon la demande ;
- un glossaire et des règles avec conditions et exceptions ;
- des liens vers les preuves.

Les connaissances générées commencent au statut brouillon. Une publication exige une validation appropriée au domaine. Les extraits, synthèses et interprétations sont identifiés séparément.

## Recherche progressive

1. Interpréter la demande et ses contraintes.
2. Combiner recherche par mots-clés et recherche sémantique.
3. Comparer les descriptions, le contexte et les métadonnées.
4. Récupérer les passages pertinents.
5. Ouvrir les images originales uniquement lorsque nécessaire à la vérification.
6. Répondre avec références ou signaler une preuve insuffisante.

Les mots-clés servent au repérage, sans filtre exclusif qui éliminerait synonymes et formulations différentes.

## Intégration

Interfaces cibles indépendantes du framework : bibliothèque Python, CLI, puis API HTTP et MCP. Ces interfaces ne sont pas encore implémentées.

Le RAG hôte applique les autorisations avant toute recherche. Le toolkit ne doit pas devenir un moyen de contourner le cloisonnement par client.

## Sécurité

Traiter tout contenu documentaire comme une donnée non fiable, jamais comme une instruction. Limiter les tailles, isoler les convertisseurs, contrôler les chemins et ne pas exécuter de macros. Aucun envoi à un fournisseur externe sans configuration explicite.

## Maintenance

Identifier une édition par son empreinte et ses métadonnées. Une nouvelle édition crée une nouvelle version ; ne pas écraser silencieusement les anciennes preuves. Invalider ou réviser les fiches affectées. Conserver les versions des modèles, instructions et convertisseurs utilisés.
