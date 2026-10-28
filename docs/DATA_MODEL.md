# Modèle de données v0.1

Spécification proposée ; validation automatique à implémenter.

## Document

Champs : document_id, title, edition, language, original_sha256, original_path, rights_status, ingestion_version, status.

L'identifiant et l'empreinte permettent de distinguer documents et éditions. Le chemin reste relatif à un espace de stockage autorisé.

## Référence

Champs obligatoires :
- schema_version : version du format.
- record_id : identifiant stable dans une édition.
- document_id : lien vers le document.
- kind : passage, table, image ou knowledge_card.
- locator : section, page physique, page imprimée et diapositive ; valeurs nulles autorisées.
- text : contenu extrait ou dérivé.
- keywords : termes de repérage.
- source_record_ids : références justificatives des contenus dérivés.
- provenance : méthode, version de l'outil, modèle éventuel et nature du contenu.
- review_status : draft, approved ou rejected.

## Images

Ajouter asset_path, caption, ocr_text et description. Une description issue d'un modèle porte provenance.content_origin = generated_description et référence l'image source.

## Règles

Une fiche ne peut pas référencer un identifiant absent. Une référence générée ne doit pas être étiquetée comme extrait original. Les nombres, unités et exceptions doivent être vérifiés sur leur source lorsque utilisés dans une réponse à conséquence importante.

Les descriptions d'images ne remplacent pas les images originales. Les embeddings constituent un index dérivé et reconstructible, pas la source de vérité.
