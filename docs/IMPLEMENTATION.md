# Implémentation 0.2

## Points d’entrée

| Service Python | Commande | Effet |
|---|---|---|
| prepare_rag(source, output, **kwargs) | prepare-rag | Prépare uniquement les sources documentaires |
| create_skill(bundle, output, generator, identity=None, allow_partial=False) | create-skill | Génère un skill autonome à partir d’un document conservé |
| assign_skill(skill, agent, registry, reviewed=False) | assign-skill | Conserve une copie versionnée et l’association locale |

Ces services sont définis dans skillrag/services.py. La CLI est dans skillrag/cli.py. Les identifiants d’agents sont ceux de l’application hôte, pas des agents créés ou contactés automatiquement par cet outil.

## Adaptateurs et sélection

Un moteur expose name, supports(path) et convert(path, work). Sa sortie contient markdown, records et partial. Chaque record possède kind, text et locator, et éventuellement asset. Les fichiers temporaires doivent rester dans work.

La primitive interne ingest essaie les moteurs configurés dans l’ordre. Les moteurs natifs par défaut sont MarkdownEngine puis DoclingEngine, chacun avec ses formats compatibles. Un échec ou rejet permet de passer au moteur suivant ; sans alternative compatible, la préparation échoue.

QualityPolicy vérifie la longueur minimale du texte, la présence de records et de localisateurs ainsi que le statut partiel. Les figures signalées comme manquantes entraînent aussi un rejet. Ces contrôles ne comparent pas l’intégralité du résultat à chaque page originale.

La primitive ingest ne génère jamais de skill : elle n’accepte plus de paramètre generator. La création d’un skill passe uniquement par create_skill, qui lit un bundle déjà conservé.

## Formats et provenance

Le SHA-256 des octets originaux identifie une édition documentaire. Les records reçoivent des identifiants document:position. Ces identifiants restent dépendants de l’ordre d’extraction et peuvent changer avec un autre moteur ou une autre version.

Le moteur texte conserve des groupes de 40 lignes et leurs bornes. Docling conserve les références d’éléments et sa provenance ainsi que son JSON riche. Aucune pagination n’est inventée.

Le format courant records.jsonl est un format de travail 0.2. Le fichier DATA_MODEL.md décrit une cible plus riche ; toutes ses propriétés ne sont pas implémentées.

## Génération BookToSkill

CompatibleModel appelle un endpoint Chat Completions explicitement fourni. Il demande un objet JSON contenant des points de connaissances, catégories et identifiants de preuves. Les documents sont présentés comme des données non fiables.

Les passages (records découpés à 4000 caractères maximum, à une frontière de ligne ou de phrase quand elle existe) sont regroupés en fenêtres consécutives de 4000 caractères au plus ; un titre ou une légende voyage donc avec ses voisins. Pour chaque fenêtre, le modèle renvoie de 0 à 12 points. Zéro point n’est accepté qu’avec un no_knowledge_reason valide (heading_only, caption_or_label, page_furniture, non_informative) ; sinon la réponse est invalide.

Les références doivent appartenir aux passages de la fenêtre (1 à 8, sans doublon). Le texte des preuves est reconstruit à partir de l’extraction, pas accepté comme une citation réécrite par le modèle. Les erreurs transitoires (délai, connexion, 429, 5xx, réponse invalide) sont reprises 3 fois avec délai croissant ; 400 et 401 ne le sont pas.

Un échec persistant interrompt la création (mode strict, par défaut). Avec allow_partial, le skill est écrit avec le statut incomplete, et provenance.json liste les passages en échec (erreur, nature, localisateurs) et les passages ignorés (raison, localisateurs). Si plus de 40 % des caractères produisent zéro point, la création est refusée en mode strict : un zéro point ne doit pas masquer une extraction ratée. assign_skill refuse un skill incomplet sauf allow_incomplete.

Identité : titre, sujet, description, édition et nom sont fournis par l’appelant ou déduits du nom du fichier, jamais inventés par le modèle. Le nom se termine par huit caractères de l’empreinte SHA-256 du document.

La génération utilise la philosophie conservée de virgiliojr94/book-to-skill et les fonctions de construction/validation ainsi que le script de recherche de zhimaAi/BookToSkill. Les copies upstream et leurs licences sont incluses dans le paquet ; les commits sont consignés dans THIRD_PARTY.md.

Le constructeur upstream emploie un nom de source comme identifiant. Le toolkit utilise un alias SHA256.md et conserve original_document_id, record_id et locator pour retrouver le document parent. Le skill contient sa propre copie de la source et reste indépendant de la disponibilité du RAG d’origine.

Le noyau utilise un budget de caractères et les fiches conservent les autres points. Les traitements fragmentés ne garantissent pas les relations globales entre chapitres ni la fidélité sémantique des synthèses.

## Attribution et versions

Le service vérifie la présence de SKILL.md, un en-tête minimal et l’absence de liens symboliques. Il calcule une empreinte de l’arborescence et copie le skill dans le registre. SQLite stocke une association active par couple agent/nom de skill.

Les scripts du skill ne sont pas exécutés pendant l’attribution. Le contrôle de structure ne constitue pas un audit de leur comportement. Le système hôte doit charger les associations ; il reste responsable des droits d’accès, du cloisonnement et de l’activation.

## Tests réalisés

Douze tests couvrent la conservation exacte du texte et de l’original, le refus du doublon, les secours après erreur ou sortie vide, le refus du partiel et des formats ou tailles non acceptés, les preuves inventées, l’échec du modèle, la recherche upstream, l’indépendance des services, l’attribution personnalisée sans RAG et le refus d’un original modifié.

La génération emploie un modèle simulé. Aucun benchmark sur un vrai livre, appel à un vrai modèle ou essai Docling n’a été réalisé dans cette validation.

## Limites et intégrations restantes

Pas encore d’interface graphique, catalogue distant, insertion vectorielle, recherche sémantique, API HTTP/MCP ou activation d’agent externe. Les images Markdown liées ne sont pas collectées automatiquement ; les descriptions contextuelles des figures restent à développer.

Le projet ne fournit pas encore de déploiement serveur, de verrou de dépendances ou d’isolation des convertisseurs. Le modèle de génération, ses ressources et ses conditions de confidentialité sont à choisir explicitement.
