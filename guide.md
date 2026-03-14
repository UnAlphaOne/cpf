📖 Guide d'Utilisation
1. Premier Lancement
bash

python cpf_gui_v1.py

Lors du premier démarrage, le système vous demandera un mot de passe pour chiffrer votre base de connaissances. Gardez-le précieusement !

2. Onglets et Fonctionnalités
Onglet	Description	Utilisation
💬 Chat	Dialogue avec l'IA	Posez des questions normalement
🌐 Web	Recherche manuelle	Entrez un sujet à explorer
📊 Stats	Statistiques	Visualisez la croissance
🕸️ Graphe	Visualisation	Explorez les connexions
🔬 Deep	Apprentissage profond	Suivez l'apprentissage récursif
📜 Historique	Archives	Consultez les conversations
📋 Log	Journal	Debug et monitoring

3. Exemples d'Utilisation
python

# Exemple 1 : Question simple
> qu'est ce que la photosynthèse ?
🤖 La photosynthèse est le processus par lequel les plantes...

# Exemple 2 : Apprentissage automatique
> explique moi la mécanique quantique
🤖 [Réponse] + [Suggestions: physique, atome, particule]

# Exemple 3 : Exploration profonde
> [Clic sur une suggestion]
🤖 J'apprends la physique... [puis] l'atome... [puis] l'électron...


🔒 Sécurité et Confidentialité
Chiffrement des Données

    Algorithme : AES-256 via Fernet

    Dérivation de clé : PBKDF2 avec 100,000 itérations

    Stockage : Local uniquement

Anonymisation Automatique

Les informations personnelles suivantes sont automatiquement détectées et anonymisées :

    📧 Adresses email

    📞 Numéros de téléphone

    🏠 Adresses postales

    🆔 Numéros de sécurité sociale

    💳 Informations bancaires

    🌐 Adresses IP

Bonnes Pratiques
python

# Votre mot de passe n'est jamais stocké
# Il sert uniquement à dériver la clé de chiffrement
# Sans le mot de passe, les données sont illisibles

📊 Performances
Base de connaissances	Temps de chargement	Mémoire	Taille fichier
100 concepts	< 1s	50 MB	2 MB
1,000 concepts	2s	200 MB	20 MB
10,000 concepts	15s	1.5 GB	200 MB
100,000 concepts	2min	12 GB	2 GB
🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

    Forkez le projet

    Créez votre branche (git checkout -b feature/AmazingFeature)

    Committez vos changements (git commit -m 'Add AmazingFeature')

    Pushez vers la branche (git push origin feature/AmazingFeature)

    Ouvrez une Pull Request

Guidelines de contribution

    Suivez le style de code PEP 8

    Ajoutez des tests pour les nouvelles fonctionnalités

    Mettez à jour la documentation

    Commentez le code en français


🙏 Remerciements

    Communauté open source pour les bibliothèques utilisées

    Wikipedia pour sa base de connaissances libre

    Inria pour les recherches en IA

📞 Contact

    Auteur : Gérard D

    GitHub : @UnAlphaOne


⭐ N'oubliez pas de mettre une étoile si ce projet vous plaît ! ⭐
text


### **5. Script d'installation**

Créez un fichier `install.sh` pour Linux/Mac :

```bash
#!/bin/bash
echo "🚀 Installation de CPF - Codage Prédictif Fractal"
echo "================================================"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

# Créer environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
echo "📦 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Lancer l'application
echo "✅ Installation terminée !"
echo "🚀 Lancement de CPF..."
python cpf_gui_v1.py

Et install.bat pour Windows :
batch

@echo off
echo 🚀 Installation de CPF - Codage Prédictif Fractal
echo ================================================

:: Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé
    exit /b 1
)

:: Créer environnement virtuel
echo 📦 Création de l'environnement virtuel...
python -m venv venv
call venv\Scripts\activate.bat

:: Installer dépendances
echo 📦 Installation des dépendances...
pip install --upgrade pip
pip install -r requirements.txt

:: Lancer l'application
echo ✅ Installation terminée !
echo 🚀 Lancement de CPF...
python cpf_gui_v1.py
pause