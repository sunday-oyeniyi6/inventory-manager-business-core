# Inventory Manager - Business Core

Ce dépôt contient le code source du module "Business Core" (Django + DRF) pour l'application Inventory Manager.

## Démarrage en local

Voici la marche à suivre pour démarrer l'environnement de développement sur votre machine.

### 1. Démarrer la base de données (PostgreSQL)

Assurez-vous que Docker est installé et en cours d'exécution sur votre machine. Lancez la commande suivante :

```bash
docker compose up -d
```

### 2. Démarrer le serveur Backend (Django)

Placez-vous dans le répertoire du backend et utilisez le gestionnaire de paquets `uv` pour appliquer les migrations (si nécessaire) et lancer le serveur :

```bash
# Appliquer les migrations de base de données
uv run python manage.py migrate

# Démarrer le serveur de développement
uv run python manage.py runserver
```

### 3. Consulter la documentation de l'API (Swagger)

Une fois le serveur démarré, la documentation interactive de l'API (générée avec `drf-spectacular`) est accessible aux adresses suivantes :

- **Interface Swagger (Interactive)** : [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
- **Interface ReDoc (Lecture statique)** : [http://localhost:8000/api/schema/redoc/](http://localhost:8000/api/schema/redoc/)
- **Schéma OpenAPI brut** : [http://localhost:8000/api/schema/](http://localhost:8000/api/schema/)