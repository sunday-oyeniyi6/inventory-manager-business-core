import os
import time
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

# We connect to the Master realm to configure everything
print("Connexion à Keycloak (master)...")
keycloak_admin = KeycloakAdmin(
    server_url="http://localhost:8085/",
    username="admin",
    password="admin",
    realm_name="master",
    client_id="admin-cli",
    verify=True
)

REALM_NAME = "visiontech"
CLIENT_ID = "inventory-manager-frontend"
ADMIN_CLIENT_ID = "inventory-manager-backend"
CLIENT_SECRET = "6YaLd86mJLJIbmM1ecMm"

# Wait a bit just in case
time.sleep(1)

print(f"Création du realm '{REALM_NAME}'...")
try:
    keycloak_admin.create_realm(payload={
        "realm": REALM_NAME,
        "enabled": True,
        "displayName": "Vision Tech",
        "registrationAllowed": False
    })
    print("✅ Realm créé avec succès.")
    time.sleep(1)
except KeycloakError as e:
    if "409" in str(e):
        print("ℹ️ Le Realm existe déjà.")
    else:
        raise e

# Switch context to the new realm for next operations
keycloak_admin.realm_name = REALM_NAME

print(f"Création du client public '{CLIENT_ID}' (pour le frontend)...")
try:
    keycloak_admin.create_client(payload={
        "clientId": CLIENT_ID,
        "enabled": True,
        "publicClient": True,
        "directAccessGrantsEnabled": True,
        "standardFlowEnabled": True,
        "redirectUris": ["*"],
        "webOrigins": ["*"]
    })
    print(f"✅ Client '{CLIENT_ID}' créé.")
except KeycloakError as e:
    print(f"DEBUG EXCEPTION: {e}")
    if "409" in str(e):
        print(f"ℹ️ Le client '{CLIENT_ID}' existe déjà.")
    else:
        raise e

print(f"Création du client confidentiel '{ADMIN_CLIENT_ID}' (pour le backend Django)...")
try:
    keycloak_admin.create_client(payload={
        "clientId": ADMIN_CLIENT_ID,
        "enabled": True,
        "publicClient": False,
        "secret": CLIENT_SECRET,
        "serviceAccountsEnabled": True,
        "directAccessGrantsEnabled": False,
        "standardFlowEnabled": False
    })
    print(f"✅ Client '{ADMIN_CLIENT_ID}' créé.")
except KeycloakError as e:
    print(f"DEBUG EXCEPTION: {e}")
    if "409" in str(e):
        print(f"ℹ️ Le client '{ADMIN_CLIENT_ID}' existe déjà. Mise à jour du secret...")
        client_internal_id = keycloak_admin.get_client_id(ADMIN_CLIENT_ID)
        keycloak_admin.update_client(client_internal_id, payload={
            "secret": CLIENT_SECRET,
            "serviceAccountsEnabled": True
        })
        print(f"✅ Secret du client '{ADMIN_CLIENT_ID}' mis à jour.")
    else:
        raise e

# Grant 'realm-management' -> 'manage-users' role to the Service Account
print("Attribution des droits 'manage-users' au client Django...")
client_id_internal = keycloak_admin.get_client_id(ADMIN_CLIENT_ID)
service_account_user = keycloak_admin.get_client_service_account_user(client_id_internal)

# Get the management client
realm_management_client_id = keycloak_admin.get_client_id(f"{REALM_NAME}-realm")
manage_users_role = keycloak_admin.get_client_role(realm_management_client_id, "manage-users")

# Assign role
keycloak_admin.assign_client_role(
    user_id=service_account_user['id'],
    client_id=realm_management_client_id,
    roles=[manage_users_role]
)
print("✅ Droits attribués avec succès.")

print("\n🎉 Configuration de Keycloak terminée avec succès ! 🎉")
print("Votre fichier .env est déjà configuré avec ces valeurs.")
