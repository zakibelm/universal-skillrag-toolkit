# Historique des versions

## Non publié

Correctifs issus de l'audit du code de la version 0.2.0.

- Recherche : chaque skill reçoit un point d'entrée `scripts/search_index.py` qui enveloppe la copie non modifiée de l'amont (`_search_index_upstream.py`) et remplace seulement la tokenisation : accents ignorés, arabe normalisé.
- Identité : nom (suffixé par l'empreinte de l'édition), titre, sujet, description et édition propres à chaque skill ; options CLI `--title`, `--subject`, `--description`, `--edition`.
- Génération : fenêtres de passages consécutifs, zéro point autorisé avec raison, reprises limitées, mode `--allow-partial` produisant un skill marqué incomplet avec les passages concernés ; refus si plus de 40 % du texte ne produit rien.
- Attribution : un skill incomplet est refusé sauf `--allow-incomplete`.
- `CompatibleModel` : erreurs typées (`ModelError` : timeout, connexion, http_error, invalid_response) ; dix tests HTTP contre un fournisseur simulé local.
- API : `ingest` ne génère plus de skill (le paramètre `generator` est supprimé) ; la clé `knowledge_generation` disparaît du manifeste du bundle.
- THIRD_PARTY.md : statut exact de chaque réutilisation (texte, moteur appelé, copie enveloppée, non repris).

## 0.2.0 — 28 octobre 2026

Première version exécutable : préparation documentaire du RAG, création de skills depuis les documents conservés et attribution de skills de livres ou personnalisés dans un registre local. Ajout du moteur texte, du branchement Docling optionnel, des ressources BookToSkill identifiées et de douze tests sur données synthétiques.

Documentation : description détaillée, guide d’utilisation, architecture, interfaces et limites. Les essais avec Docling, un véritable modèle et un ouvrage réel restent à effectuer. Interface graphique et déploiement serveur non fournis.

## 0.1 — socle documentaire

Positionnement générique, architecture cible, modèle de références, protocole d’évaluation et feuille de route. Aucun moteur exécutable dans cette étape initiale.
