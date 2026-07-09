✨ Cosmopings ✨

Un bot Discord qui surveille une chaîne YouTube et notifie automatiquement des salons Discord désignés lorsqu'une nouvelle cover ou un live est publié.

## Fonctionnalités

- Interroge l'API YouTube et le flux RSS toutes les 5 minutes pour détecter les nouvelles publications
- Détecte le type de contenu (cover vs. live) grâce aux mots-clés du titre et aux hashtags de la description
- Publie des annonces de première/stream programmée avec horodatage relatif Discord
- Envoie une notification de suivi lorsqu'un événement programmé passe réellement en direct
- Gère les lives non programmés qui démarrent sans annonce préalable
- Évite les notifications en double grâce à un suivi persistant en JSON

## Fonctionnement

| Événement | Comportement |
|---|---|
| Nouvelle cover publiée | Publiée immédiatement dans le salon covers |
| Première programmée | Publie une annonce avec compte à rebours |
| La première passe en direct | Envoie une notification de suivi "c'est en direct maintenant" |
| Live non programmé | Détecté et notifié en temps réel |

Le type de contenu est déterminé par :
- Les mots-clés dans le titre (ex. cover, live, stream)
- Les hashtags dans la description

## Installation

### Prérequis

- Python 3.8+
- Un token de bot Discord
- Une clé API YouTube Data v3

### Installation

```
git clone https://github.com/palmtreepaniko/cosmopings
cd cosmopings
pip install -r requirements.txt
```

### Variables d'environnement

Crée un fichier `.env` ou définis les variables d'environnement suivantes :

```
DISCORD_TOKEN=ton_token_de_bot_discord
YOUTUBE_API_KEY=ta_cle_api_youtube
```

### Configuration

Modifie les constantes en haut de `bot.py` selon ta configuration :

```
CHANNEL_ID = "ton_id_de_chaine_youtube"
COVER_CHANNEL_ID = 000000000000000000   # ID du salon Discord pour les covers
LIVE_CHANNEL_ID  = 000000000000000000   # ID du salon Discord pour les lives

COVER_KEYWORDS = ["cover"]
LIVE_KEYWORDS  = ["live", "stream", "livestream"]

COVER_HASHTAGS = ["#ton_hashtag_cover"]
LIVE_HASHTAGS  = ["#ton_hashtag_live"]
```

## Lancer le bot

```
python bot.py
```

## Structure des fichiers

```
cosmopings/
├── bot.py           
├── posted.json      # Suit les vidéos déjà notifiées
├── scheduled.json   # Suit les événements programmés à venir
└── requirements.txt
```

## Dépendances

- discord.py
- google-api-python-client

## Permissions du bot Discord

Assure-toi que ton bot dispose des permissions suivantes :
- Envoyer des messages
- Voir les salons

## Remarques

- L'endpoint YouTube `search().list` (utilisé pour la détection des streams à venir) consomme plus de quota API. Il s'exécute tous les 6 cycles (~30 minutes) par défaut pour rester dans les limites.
- `posted.json` et `scheduled.json` sont créés automatiquement au premier lancement.
