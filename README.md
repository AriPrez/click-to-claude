# 🚀 Click to Claude

> **Instant Linux Screenshot & Numbered Pin Tool for Claude.ai (No API Required)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Linux](https://img.shields.io/badge/Platform-Linux%20%28X11%2FGNOME%2FKDE%29-blue.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)]()

**Click to Claude** est un outil Linux ultra-rapide qui vous permet d'envoyer instantanément n'importe quelle partie de votre écran à **Claude.ai** avec des **repères numérotés (1, 2, 3...)**, de l'**OCR automatique** et l'**injection du contexte de votre application**, sans aucune clé API !

---

## ✨ Fonctionnalités Principales

- ⚡ **Raccourci 1-Clic (`Super + C`)** : Appuyez sur la touche Windows + C pour déclencher la sélection de zone à la souris.
- 📍 **Épingles Numérotées (1, 2, 3...)** : Cliquez sur la capture pour placer des pastilles repères et tapez vos questions point par point.
- ⬛ **Masquage Sensible** : Masquez les mots de passe, tokens et clés d'API en un glissé de souris avant l'envoi.
- 🧠 **Moteur de Contexte Automatique** : Détecte l'application et la fenêtre sur laquelle vous travailliez (*ex: VS Code - main.py*).
- 📄 **OCR Automatique (Tesseract)** : Extrait le code/texte brut de l'image et l'injecte dans le prompt pour une précision maximale.
- 🪟 **Mini-Onglet Claude Dédié** : Ouvre une fenêtre WebApp compacte et épurée de Claude.
- 📋 **Coller 100% Automatique (`Ctrl+V`)** : La capture et le Mega-Prompt structuré sont collés automatiquement sans aucune action manuelle !

---

## 🛠️ Installation Rapide

Ouvrez un terminal dans le dossier du projet et exécutez :

```bash
cd /home/ari_prezo/Bureau/Click
bash install.sh
```

Le script va :
1. Installer les utilitaires Linux nécessaires (`xclip`, `xdotool`, `scrot`, `tesseract-ocr`, `python3-tk`).
2. Configurer automatiquement le raccourci clavier **`Super + C`** (Touche Windows + C).

---

## 🎮 Utilisation

1. Appuyez sur **`Super + C`** (ou la touche Windows + C).
2. Sélectionnez une zone de l'écran avec votre souris.
3. Poser des épingles **(1, 2, 3...)** et choisissez votre sujet.
4. Cliquez sur **`🚀 ENVOYER À CLAUDE`** !

---

## 📂 Structure du Dépôt

- `click_claude.py` : Script Python principal (GUI, capture, OCR, gestion des fenêtres et coller).
- `install.sh` : Script d'installation automatique des dépendances et du raccourci clavier.
- `click_claude.desktop` : Fichier de raccourci d'application système Linux.
- `LICENSE` : Licence Open-Source MIT.
- `CONTRIBUTING.md` : Guide pour les contributions de la communauté.

---

## 📜 Licence

Distribué sous la licence MIT. Voir `LICENSE` pour plus d'informations.
