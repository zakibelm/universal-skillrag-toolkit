# Implémentation 0.2

Le code Python ajoute le premier circuit d'extraction au socle documentaire 0.1.

## Contrat d'adaptateur

Un moteur expose `name`, `supports(path)` et `convert(path, work)`. Sa sortie contient `markdown`, `records` et `partial`. Chaque record possède `kind`, `text` et `locator`, et éventuellement `asset`. Il écrit ses fichiers uniquement dans `work`.

`ingest(source, output, engines=[...], policy=...)` essaie les moteurs dans l'ordre configuré. Un moteur absent ou en erreur ne devient pas une réussite silencieuse. Après épuisement des moteurs, le traitement échoue sans publier de bundle. La priorité actuelle est configurable et ne constitue pas une comparaison scientifique des moteurs.

## Provenance

Le SHA-256 identifie les octets de l'original. Les identifiants d'éléments sont stables pour une même extraction ordonnée ; ils ne sont pas garantis entre versions de convertisseurs. Le moteur texte conserve les lignes exactes ; Docling conserve ses références d'éléments, sa provenance et son JSON riche. Le schéma 0.2 est un format de travail, distinct du schéma cible documenté dans DATA_MODEL.md.

## Validation réalisée

Neuf tests unitaires couvrent : reconstruction exacte du texte et original conservé ; refus du doublon ; secours après extraction vide ; secours après exception ; refus d'une conversion partielle ; refus de taille excessive et format inconnu. Aucun benchmark sur ouvrage réel ni exécution de Docling n'a été réalisé ici.

## Limites explicites

Le noyau et les fiches sont produits par un générateur configuré ; les tests de ce chemin emploient un modèle simulé. Le constructeur/validateur et le moteur lexical de zhimaAi sont réellement réutilisés ; la philosophie de génération de virgilio est incluse dans les instructions du modèle. Pas encore de recherche vectorielle, analyse contextuelle des figures, OCRmyPDF, API HTTP ou MCP. Les images Markdown liées ne sont pas copiées ; leur ingestion multimodale reste à développer. Le seuil de texte est configurable et peut refuser un document court légitime.

Les contrôles ne détectent pas tous les tableaux déformés ou passages omis. La qualité sémantique exige un corpus annoté et une relecture. Ajouter des modèles visuels exige une configuration explicite des ressources et de la confidentialité. Isoler les convertisseurs pour des documents non fiables avant exploitation en production.

Les mises à jour de moteur doivent être testées puis figées dans un environnement reproductible avant déploiement ; la plage de dépendance déclarée n'est pas un verrou de production.

## Pipeline commun BookToSkill et RAG

L'appel `ingest(..., generator=...)` extrait une seule fois le document puis génère les deux sorties avant publication atomique. Une erreur du modèle ou une référence inventée bloque la sortie complète. La bibliothèque autorise `generator=None` pour les usages extraction seule ; la CLI exige explicitement `--extract-only` pour ce mode.

Chaque unité envoyée au modèle contient au maximum 4000 caractères. Le modèle retourne des points structurés, des catégories et des identifiants de preuves. Le programme reconstruit les citations à partir du texte extrait, sans accepter de citations réécrites par le modèle. La génération fragmentée ne remplace pas une validation globale des relations entre chapitres.

Le format du constructeur upstream utilise le nom de source comme identifiant : un alias SHA256.md est utilisé dans le complément. `original_document_id`, `record_id` et `locator` préservent le lien vers le bundle RAG. Les métadonnées de l'original sont conservées dans le manifeste parent. Les fichiers de licences sont distribués avec le code vendored.

## Révision : services indépendants

La décision finale remplace l'exécution couplée par trois opérations dans `services.py` et la CLI : `prepare-rag`, `create-skill`, `assign-skill`. Les descriptions historiques du pipeline commun ci-dessus concernent la primitive interne `ingest(generator=...)`, conservée pour compatibilité technique et tests, pas le parcours public recommandé.

`create_skill` lit un bundle existant, contrôle l'empreinte de l'original, génère dans un espace temporaire et publie son propre dossier identifié par empreinte. Il ne change pas le bundle RAG. `assign_skill` accepte le même format de dossier pour un skill personnalisé et pour un skill de livre. Le registre SQLite est une association locale, pas une activation d'un agent distant. La validation de dossier/frontmatter est minimale et ne constitue pas un audit du contenu ou des scripts.

Trois tests supplémentaires vérifient les opérations indépendantes, l'attribution personnalisée sans RAG et le refus d'un original modifié. Total : douze tests. Aucun livre réel, appel de modèle réel ou convertisseur Docling n'a été évalué ici.
