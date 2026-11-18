# Hublot

Interface de configuration web pour un Raspberry Pi 3B qui fait office d'enceinte Spotify Connect (via Spotify Soloist).

Le fonctionnement s'inspire des interfaces de configuration des enceintes réseau : onglets Statut / Réseau / Système / Mise à jour / Rapport, protection par PIN, nom convivial, configuration Wi-Fi.

> Statut : version de développement, non testée sur matériel réel.

## Comportement

1. **Premier démarrage** : installe Spotify Soloist depuis le site officiel, puis active les services.
2. **Démarrages suivants** :
   - si le Pi obtient une adresse IP sur le réseau local (Ethernet ou Wi-Fi), l'interface est servie sur cette adresse ;
   - sinon, le Pi crée son propre réseau Wi-Fi (point d'accès). On s'y connecte, on ouvre l'interface, on choisit le Wi-Fi domestique, et le Pi passe en mode client.

## Installation

Sur un Raspberry Pi OS Lite (32 ou 64 bits), avec accès à internet :

```bash
curl -fsSL https://raw.githubusercontent.com/len12-dev/hublot/main/install.sh | sudo bash
```

## Architecture

| Élément | Choix |
|---|---|
| Système | Raspberry Pi OS Lite |
| Backend | Python 3 + Flask, servi par gunicorn |
| Réseau | NetworkManager (`nmcli`) : scan, connexion, point d'accès |
| Service | systemd (`hublot.service`) |
| Configuration | `/etc/hublot/config.json` (PIN haché, nom convivial) |
| Interface | HTML / CSS / JavaScript sans framework |

## Onglets

- **Statut** : nom, mode réseau, SSID, adresse IP.
- **Réseau** : scan des réseaux Wi-Fi, connexion.
- **Système** : nom convivial, changement de PIN, réglages des graves et des aigus.
- **Mise à jour** : à implémenter.
- **Rapport** : à implémenter.

## Structure du dépôt

```
install.sh              # installation en une commande (télécharge la release)
app/
  main.py               # serveur Flask, routes et PIN
  network.py            # wrapper nmcli
  templates/            # login.html, index.html
scripts/
  first_boot.sh         # installation de Soloist et des services
systemd/
  hublot.service        # lancement au démarrage
```

## Sécurité

- Pas de PIN par défaut figé : le PIN est défini par l'utilisateur.
- Le PIN est stocké haché (PBKDF2), jamais en clair.
- L'interface est prévue pour le réseau local ou le point d'accès, pas pour internet.
- Le point d'accès de configuration est ouvert (sans mot de passe) : on s'y connecte physiquement près de l'enceinte, puis on saisit le Wi-Fi domestique.
