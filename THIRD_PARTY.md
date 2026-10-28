# Composants externes

## BookToSkill : ce qui est réellement réutilisé

| Projet et commit | Fichier amont | Statut dans le toolkit |
|---|---|---|
| virgiliojr94/book-to-skill, `7540eefbe74933f5fc84c86becac52486b347778`, MIT | `SKILL.md`, conservé comme `skillrag/upstream/virgilio/GENERATOR_SPEC.md` | **Texte réutilisé comme consigne.** Seule la section « Philosophy » est insérée dans le prompt de `CompatibleModel`. Aucun code de ce projet n'est exécuté. |
| zhimaAi/BookToSkill, `b8499c103588e303eaa23c238fbe13ae632c1ff4`, Apache-2.0 | `scripts/build_skill.py` | **Moteur appelé.** Chargé dynamiquement par `skillrag/knowledge.py` : `require_text`, `optional_text_list`, `load_index`, `load_metadata`, `skill_markdown`, `build_openai_yaml`. |
| | `scripts/search_index.py` | **Copié et enveloppé.** La copie est livrée dans chaque skill sous `scripts/_search_index_upstream.py`. Le point d'entrée `scripts/search_index.py` du skill est une enveloppe du toolkit (`skillrag/skill_assets/search_index.py`) qui ne remplace que la fonction `tokens` (accents français, arabe) ; le score, la lecture JSONL et le format de sortie restent ceux de l'amont. |
| | `convert_documents.py`, `split_markdown.py`, `merge_index.py`, `batch_index.py`, `prepare_workflow.py` | **Non repris.** Ni copiés ni appelés. |

Fidélité des copies : le contenu est identique aux commits indiqués, à un retour à la ligne final près ajouté à chaque fichier copié (1 octet). L'empreinte binaire diffère donc de celle de l'amont ; les licences complètes sont adjacentes dans `skillrag/upstream/virgilio/LICENSE` et `skillrag/upstream/zhimaai/LICENSE`. Copyright de virgiliojr94 : 2025. Ce n'est pas une fusion des fonctions des deux projets.

Les instructions upstream sont des ressources du générateur, pas une installation de skill personnel dans ChatGPT.

## Docling optionnel

Docling est appelé via son API, sans copie de son dépôt. Son fichier LICENSE consulté indique MIT, copyright The Docling Contributors : https://github.com/docling-project/docling/blob/main/LICENSE . Les licences des modèles et dépendances doivent être contrôlées séparément avant distribution/déploiement. Référence API : https://github.com/docling-project/docling/blob/main/docs/examples/export_figures.py .

Les sources, leurs droits et les conditions du fournisseur de modèles sont indépendants des licences du code.
