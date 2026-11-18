# Hublot Raspberry Pi — note de conception

Programme d'interface humain-machine pour Raspberry Pi 3B, sans nom officiel pour l'instant.
Inspiré du fonctionnement de l'interface web Frontier Silicon (onglets Statut / Réseau / Système / Mise à jour / Rapport, PIN, nom convivial, Wi-Fi), mais avec sa propre conception visuelle.

## Comportement attendu

1. **Premier démarrage**
   - Vérifie la connexion internet.
   - Télécharge et installe Spotify Soloist (voir « Points à confirmer »).
   - Crée la configuration par défaut et active les services.
2. **Démarrages suivants**
   - Si le Pi a une adresse IP sur le réseau local (Ethernet ou Wi-Fi), l'interface web est servie sur cette IP.
   - Sinon, le Pi crée son propre réseau Wi-Fi (point d'accès) ; l'utilisateur s'y connecte, ouvre l'interface, choisit son Wi-Fi domestique, puis le Pi bascule en mode client.

## Architecture

| Élément | Choix proposé |
|---|---|
| OS | Raspberry Pi OS Lite (64 bits ou 32 bits selon le Pi 3B) |
| Backend | Python 3 + Flask (léger, adapté au Pi 3B) |
| Réseau | NetworkManager (`nmcli`) : scan, connexion, point d'accès |
| Service | systemd (`hublot.service`) lancé au boot |
| Config | fichier JSON (`/etc/hublot/config.json`), PIN haché |
| Interface | HTML/CSS/JS sans framework, servie par Flask |

## Onglets de l'interface (inspirés de la capture)

- **Statut** : nom convivial, version, adresse IP, SSID, force du signal, état de Spotify Soloist.
- **Réseau** : mode Wi-Fi / Ethernet, scan des réseaux, saisie SSID et mot de passe, DHCP, réseaux enregistrés.
- **Système** : nom convivial, PIN, réglages audio (égaliseur simple : graves / aigus).
- **Mise à jour** : vérifier et appliquer les mises à jour du programme et de Soloist.
- **Rapport** : journaux utiles pour le diagnostic (sans données sensibles).

Le PIN (par défaut à changer au premier lancement) protège les pages de réglage.

## Structure du projet

```
hublot/
  README.md
  app/
    main.py          # serveur Flask, routes et PIN
    network.py       # wrapper nmcli : statut, scan, connexion, mode AP
    config.py        # lecture / écriture de la configuration
    templates/
      index.html     # interface à onglets
  scripts/
    first_boot.sh    # installation initiale
  systemd/
    hublot.service      # lancement au démarrage
```

## Points à confirmer

1. **Spotify Soloist** : je ne connais pas avec certitude sa méthode d'installation (dépôt, paquet, script). Le script `first_boot.sh` contient une variable `SOLOIST_URL` à renseigner. Si c'est un paquet Debian ou un script, dis-moi où le récupérer.
2. **Mot de passe du point d'accès** : faut-il un mot de passe fixe (ex. affiché sur un autocollant) ou généré au premier boot ?
3. **Langue de l'interface** : français seulement, ou aussi anglais (la capture était en anglais avec sélecteur de langue) ?
4. **Égaliseur** : garder graves / aigus simples, ou un réglage plus fin ?

## Sécurité

- Pas de PIN par défaut figé : générer un PIN à l'installation ou forcer le changement au premier accès.
- Le PIN est stocké haché, jamais en clair.
- L'interface n'est pas exposée sur internet : accès réseau local ou point d'accès uniquement.
