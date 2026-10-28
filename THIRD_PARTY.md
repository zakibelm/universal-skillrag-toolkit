# Composants externes

## BookToSkill intégrés

- virgiliojr94/book-to-skill, commit `7540eefbe74933f5fc84c86becac52486b347778`, MIT, copyright (c) 2025 virgiliojr94. Le fichier `SKILL.md` est conservé sans modification comme `skillrag/upstream/virgilio/GENERATOR_SPEC.md` et sa philosophie est utilisée pour la synthèse. Licence complète adjacente.
- zhimaAi/BookToSkill, commit `b8499c103588e303eaa23c238fbe13ae632c1ff4`, Apache-2.0. `scripts/build_skill.py` et `scripts/search_index.py` sont conservés sans modification dans `skillrag/upstream/zhimaai/`, avec la licence complète. Le premier fournit validation et génération du format de skill ; le second fournit la recherche lexicale. Le code de liaison propre au toolkit est dans `skillrag/knowledge.py`.

Ces fichiers sont réutilisés, sans prétendre fusionner toutes les fonctions des projets. Leurs autres étapes de conversion ne sont pas dupliquées. Les instructions upstream sont des ressources du générateur, pas une installation de skill personnel dans ChatGPT.

## Docling optionnel

Docling est appelé via son API, sans copie de son dépôt. Son fichier LICENSE consulté indique MIT, copyright The Docling Contributors : https://github.com/docling-project/docling/blob/main/LICENSE . Les licences des modèles et dépendances doivent être contrôlées séparément avant distribution/déploiement. Référence API : https://github.com/docling-project/docling/blob/main/docs/examples/export_figures.py .

Les sources, leurs droits et les conditions du fournisseur de modèles sont indépendants des licences du code.
