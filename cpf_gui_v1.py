"""
Codage Prédictif Fractal (CPF)
Toutes les fonctionnalités avancées sont incluses et fonctionnelles
Avec correction du problème de modèle NLP
"""

# ========== CONFIGURATION ==========
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import warnings
warnings.filterwarnings('ignore')

print("="*60)
print("🚀 DÉMARRAGE CPF V1.0")
print("="*60)

# ========== IMPORTS STANDARDS ==========
import sys
import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time
import json
import hashlib
from collections import deque, Counter
import random
import threading
import requests
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime, timedelta
import re
import pickle
import networkx as nx
from fpdf import FPDF
import csv
from textblob import TextBlob
# ===== SÉCURITÉ ET CHIFFREMENT =====
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import getpass
import os

# ========== IMPORTS OPTIONNELS ==========
# Synthèse vocale
try:
    import pyttsx3
    SPEAKER_AVAILABLE = True
except:
    SPEAKER_AVAILABLE = False

print("✅ Tous les imports standards réussis")

# ========== CLASSE CONCEPT ==========
class Concept:
    """Représente un concept avec son texte et ses métadonnées"""
    
    def __init__(self, texte, source="inconnue", url=None):
        self.id = hashlib.md5(texte.encode()).hexdigest()[:8]
        self.texte = texte
        self.source = source
        self.url = url
        self.date = datetime.now().isoformat()
        self.mots_cles = self._extraire_mots_cles(texte)
        self.vecteur = self._encoder_texte(texte)
        
        # Métadonnées pour auto-apprentissage
        self.auto_meta = {
            'consultations': 0,
            'notes_utilisateur': [],
            'note_moyenne': 3.0,
            'pertinence_calculee': 1.0,
            'derniere_consultation': None,
            'sujets_connexes': []
        }
    
    def _encoder_texte(self, texte):
        hash_obj = hashlib.sha256(texte.encode())
        vecteur = np.frombuffer(hash_obj.digest(), dtype=np.uint8).astype(np.float32) / 255.0
        if len(vecteur) > 64:
            vecteur = vecteur[:64]
        elif len(vecteur) < 64:
            vecteur = np.pad(vecteur, (0, 64 - len(vecteur)))
        return vecteur
    
    def _extraire_mots_cles(self, texte):
        texte = texte.lower()
        texte = re.sub(r'[^\w\s]', ' ', texte)
        accents = {'é':'e','è':'e','ê':'e','ë':'e','à':'a','â':'a','ä':'a',
                   'î':'i','ï':'i','ô':'o','ö':'o','ù':'u','û':'u','ü':'u','ç':'c'}
        for acc, sans in accents.items():
            texte = texte.replace(acc, sans)
        mots = re.findall(r'\b\w{4,}\b', texte)
        stop = {'dans','pour','avec','sans','tout','tous','toute','toutes',
                'une','des','les','ces','mais','donc','est','sont','qui','que',
                'dont','ou','par','sur','aussi','tres','plus','moins','cette',
                'ce','cet','ces','mon','ton','son','mes','tes','ses','notre',
                'votre','leur','nos','vos','leurs','lui','elle','eux','elles',
                'ils','je','tu','il','nous','vous','elles','vers','chez',
                'pendant','depuis','jusque','hormis','sauf','et','ou','donc',
                'or','ni','car','comme','lorsque','quand','si','ainsi','enfin',
                'ensuite','alors','puis','voila','voici','peut','peux','peuvent'}
        compteur = {}
        for mot in mots:
            if mot not in stop and len(mot) > 3:
                compteur[mot] = compteur.get(mot, 0) + 1
        mots_frequents = sorted(compteur.items(), key=lambda x: x[1], reverse=True)
        return [m for m, _ in mots_frequents[:15]]


# ========== CLASSE BASE DE CONNAISSANCES ==========
class BaseConnaissances:
    """Base de connaissances avec indexation avancée"""
    
    def __init__(self):
        self.concepts = {}
        self.index_mots_cles = {}
    
    def ajouter(self, concept):
        if not concept or not concept.id:
            return None
        
        concept.id = f"{concept.id}_{int(time.time())}_{random.randint(1000,9999)}"
        self.concepts[concept.id] = concept
        
        for mot in concept.mots_cles:
            if mot not in self.index_mots_cles:
                self.index_mots_cles[mot] = []
            if concept.id not in self.index_mots_cles[mot]:
                self.index_mots_cles[mot].append(concept.id)
        return concept.id
    
    def taille(self):
        return len(self.concepts)
    
    def rechercher(self, requete, seuil=0.1):
        """Recherche avancée avec pondération"""
        mots_requete = self._extraire_mots(requete)
        if not mots_requete:
            return []
        
        scores = {}
        details = {}
        
        for mot in mots_requete:
            # Chercher le mot et ses variantes
            variantes = [mot]
            if mot.endswith('s'):
                variantes.append(mot[:-1])
            if not mot.endswith('s'):
                variantes.append(mot + 's')
            
            for m in variantes:
                if m in self.index_mots_cles:
                    for cid in self.index_mots_cles[m]:
                        scores[cid] = scores.get(cid, 0) + 1
                        if cid not in details:
                            details[cid] = []
                        if mot not in details[cid]:
                            details[cid].append(mot)
        
        # Recherche dans les textes
        if len(scores) < 3:
            for cid, concept in self.concepts.items():
                texte = concept.texte.lower()
                score = 0
                for mot in mots_requete:
                    if mot in texte:
                        score += 1
                if score > 0:
                    scores[cid] = scores.get(cid, 0) + score
        
        resultats = []
        for cid, score in scores.items():
            concept = self.concepts[cid]
            similarite = score / len(mots_requete)
            
            # Bonus pour les définitions
            if "est un" in concept.texte.lower() or "sont des" in concept.texte.lower():
                similarite += 0.1
            
            if similarite >= seuil:
                resultats.append({
                    "concept": concept,
                    "score": similarite,
                    "mots_communs": details.get(cid, []),
                    "nb_mots": score
                })
        
        resultats.sort(key=lambda x: x["score"], reverse=True)
        return resultats
    
    def _extraire_mots(self, texte):
        texte = texte.lower()
        texte = re.sub(r'[^\w\s]', ' ', texte)
        accents = {'é':'e','è':'e','ê':'e','ë':'e','à':'a','â':'a','ä':'a',
                   'î':'i','ï':'i','ô':'o','ö':'o','ù':'u','û':'u','ü':'u','ç':'c'}
        for acc, sans in accents.items():
            texte = texte.replace(acc, sans)
        mots = re.findall(r'\b\w{4,}\b', texte)
        stop = {'qui','que','quoi','quel','quelle','quels','quelles','comment',
                'pourquoi','quand','ou','est','ce','la','le','les','des','une',
                'un','de','du','dans','pour','avec','sans','sur','par','chez',
                'quest','qu\'est','qu\'est-ce','qu\'est ce que'}
        return [m for m in mots if m not in stop]
    
    def auto_evaluer_concept(self, concept_id, note_utilisateur=None):
        """Auto-évaluation d'un concept"""
        concept = self.concepts.get(concept_id)
        if not concept:
            return
        
        if not hasattr(concept, 'auto_meta'):
            concept.auto_meta = {
                'consultations': 0,
                'notes_utilisateur': [],
                'note_moyenne': 3.0,
                'pertinence_calculee': 1.0,
                'derniere_consultation': None
            }
        
        meta = concept.auto_meta
        meta['consultations'] += 1
        meta['derniere_consultation'] = datetime.now().isoformat()
        
        if note_utilisateur:
            meta['notes_utilisateur'].append(note_utilisateur)
            meta['note_moyenne'] = sum(meta['notes_utilisateur']) / len(meta['notes_utilisateur'])
        
        # Calcul automatique
        anciennete = 1.0
        if meta['derniere_consultation']:
            jours = (datetime.now() - datetime.fromisoformat(meta['derniere_consultation'])).days
            anciennete = max(0.5, 1.0 - (jours * 0.01))
        
        frequence = min(2.0, 1.0 + (meta['consultations'] * 0.1))
        note = meta['note_moyenne'] / 5.0
        
        meta['pertinence_calculee'] = (note * 0.5 + frequence * 0.3 + anciennete * 0.2)
        return meta['pertinence_calculee']
    
    def to_dict(self):
        data = {"concepts": {}, "index": self.index_mots_cles}
        for cid, c in self.concepts.items():
            data["concepts"][cid] = {
                "id": c.id,
                "texte": c.texte,
                "source": c.source,
                "url": c.url,
                "date": c.date,
                "mots_cles": c.mots_cles,
                "vecteur": c.vecteur.tolist() if hasattr(c, 'vecteur') else [],
                "auto_meta": c.auto_meta if hasattr(c, 'auto_meta') else {}
            }
        return data
    
    @classmethod
    def from_dict(cls, data):
        base = cls()
        for cid, c_data in data["concepts"].items():
            concept = Concept("", "")
            concept.id = c_data["id"]
            concept.texte = c_data["texte"]
            concept.source = c_data["source"]
            concept.url = c_data["url"]
            concept.date = c_data["date"]
            concept.mots_cles = c_data["mots_cles"]
            concept.vecteur = np.array(c_data.get("vecteur", []))
            concept.auto_meta = c_data.get("auto_meta", {
                'consultations': 0,
                'notes_utilisateur': [],
                'note_moyenne': 3.0,
                'pertinence_calculee': 1.0,
                'derniere_consultation': None
            })
            base.concepts[cid] = concept
        base.index_mots_cles = data["index"]
        return base


# ========== VARIABLE GLOBALE ==========
_BASE_UNIQUE = None

def get_base():
    global _BASE_UNIQUE
    if _BASE_UNIQUE is None:
        _BASE_UNIQUE = BaseConnaissances()
    return _BASE_UNIQUE


# ========== CLASSE APPRENTISSAGE WEB ==========
class ApprentissageWeb:
    def __init__(self, base):
        self.base = base
        self.en_cours = False
        self.stats = {"total": 0, "dernier": None}
        
        # ===== SOURCES DE CONNAISSANCES ÉTENDUES =====
        self.sources = {
            # Encyclopédies générales
            "wikipedia": {
                "url": "https://fr.wikipedia.org/wiki/",
                "api": "https://fr.wikipedia.org/w/api.php",
                "selecteur": 'div#mw-content-text',
                "poids": 1.0,
                "langue": "fr",
                "actif": True,
                "description": "Encyclopédie libre universelle"
            },
            "wiktionary": {
                "url": "https://fr.wiktionary.org/wiki/",
                "api": "https://fr.wiktionary.org/w/api.php",
                "selecteur": '.mw-parser-output',
                "poids": 0.9,
                "langue": "fr",
                "actif": True,
                "description": "Dictionnaire libre"
            },
            "wikidata": {
                "url": "https://www.wikidata.org/wiki/",
                "api": "https://www.wikidata.org/w/api.php",
                "selecteur": '.wikibase-entityview-main',
                "poids": 0.8,
                "langue": "multi",
                "actif": True,
                "description": "Base de connaissances structurées"
            },
            "wikisource": {
                "url": "https://fr.wikisource.org/wiki/",
                "api": "https://fr.wikisource.org/w/api.php",
                "selecteur": '.mw-parser-output',
                "poids": 0.7,
                "langue": "fr",
                "actif": True,
                "description": "Bibliothèque de textes anciens"
            },
            
            # Dictionnaires et encyclopédies françaises
            "larousse": {
                "url": "https://www.larousse.fr/encyclopedie/",
                "selecteur": '.article-content, .definition',
                "poids": 0.9,
                "langue": "fr",
                "actif": True,
                "description": "Encyclopédie Larousse"
            },
            "academie_francaise": {
                "url": "https://www.dictionnaire-academie.fr/article/",
                "selecteur": '.definition',
                "poids": 0.9,
                "langue": "fr",
                "actif": True,
                "description": "Dictionnaire de l'Académie française"
            },
            "universalis": {
                "url": "https://www.universalis.fr/encyclopedie/",
                "selecteur": '.article-content',
                "poids": 0.8,
                "langue": "fr",
                "actif": False,  # Payant
                "description": "Encyclopædia Universalis"
            },
            
            # Sciences et techniques
            "arxiv": {
                "url": "https://arxiv.org/search/?query=",
                "selecteur": '.arxiv-result',
                "poids": 0.8,
                "langue": "en",
                "actif": True,
                "description": "Prépublications scientifiques"
            },
            "pubmed": {
                "url": "https://pubmed.ncbi.nlm.nih.gov/?term=",
                "selecteur": '.abstract',
                "poids": 0.8,
                "langue": "en",
                "actif": True,
                "description": "Base de données médicales"
            },
            "cairn": {
                "url": "https://www.cairn.info/rechercher.php?q=",
                "selecteur": '.resume',
                "poids": 0.7,
                "langue": "fr",
                "actif": False,  # Accès restreint
                "description": "Revues scientifiques"
            },
            "persee": {
                "url": "https://www.persee.fr/search?q=",
                "selecteur": '.resume',
                "poids": 0.7,
                "langue": "fr",
                "actif": True,
                "description": "Publications scientifiques françaises"
            },
            
            # Histoire et culture
            "francearchives": {
                "url": "https://francearchives.fr/fr/search?q=",
                "selecteur": '.description',
                "poids": 0.8,
                "langue": "fr",
                "actif": True,
                "description": "Archives nationales françaises"
            },
            "britishmuseum": {
                "url": "https://www.britishmuseum.org/collection/search?q=",
                "selecteur": '.collection-object',
                "poids": 0.7,
                "langue": "en",
                "actif": True,
                "description": "Collection du British Museum"
            },
            "metmuseum": {
                "url": "https://www.metmuseum.org/art/collection/search?q=",
                "selecteur": '.artwork',
                "poids": 0.7,
                "langue": "en",
                "actif": True,
                "description": "Collection du Metropolitan Museum"
            },
            
            # Dictionnaires bilingues
            "wordreference": {
                "url": "https://www.wordreference.com/fren/",
                "selecteur": '.WRD',
                "poids": 0.8,
                "langue": "fr-en",
                "actif": True,
                "description": "Dictionnaire bilingue"
            },
            "reverso": {
                "url": "https://dictionnaire.reverso.net/francais-definition/",
                "selecteur": '.deftext',
                "poids": 0.7,
                "langue": "fr",
                "actif": True,
                "description": "Dictionnaire contextuel"
            },
            
            # Encyclopédies spécialisées
            "iep": {
                "url": "https://iep.utm.edu/",
                "selecteur": '.entry-content',
                "poids": 0.8,
                "langue": "en",
                "actif": True,
                "description": "Internet Encyclopedia of Philosophy"
            },
            "sep": {
                "url": "https://plato.stanford.edu/entries/",
                "selecteur": '.entry-content',
                "poids": 0.8,
                "langue": "en",
                "actif": True,
                "description": "Stanford Encyclopedia of Philosophy"
            },
            "britannica": {
                "url": "https://www.britannica.com/search?query=",
                "selecteur": '.content',
                "poids": 0.8,
                "langue": "en",
                "actif": True,
                "description": "Encyclopædia Britannica"
            }
        }
        
        print(f"🌐 Apprentissage lié à base ID: {id(self.base)}")
        print(f"📚 Sources actives: {sum(1 for s in self.sources.values() if s['actif'])}/{len(self.sources)}")
    
    def apprendre_depuis_url(self, url, source_nom="wikipedia", callback=None):
        if self.en_cours:
            return 0, []
        
        self.en_cours = True
        concepts_ajoutes = []
        
        def log(msg, type="info"):
            if callback:
                callback(msg, type)
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return 0, []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            
            selecteur = self.sources.get(source_nom, {}).get('selecteur', 'body')
            contenu = soup.select_one(selecteur) or soup.find('main') or soup.body
            
            paragraphes = []
            for p in contenu.find_all(['p']):
                texte = p.get_text().strip()
                if 50 < len(texte) < 2000:
                    texte = re.sub(r'\[\d+\]', '', texte)
                    texte = re.sub(r'\s+', ' ', texte).strip()
                    paragraphes.append(texte)
            
            vus = set()
            for p in paragraphes:
                if p not in vus and len(p) > 50:
                    vus.add(p)
                    concept = Concept(p, source=source_nom, url=url)
                    self.base.ajouter(concept)
                    concepts_ajoutes.append(concept)
            
            self.stats["total"] += len(concepts_ajoutes)
            return len(concepts_ajoutes), concepts_ajoutes
            
        except Exception as e:
            return 0, []
        finally:
            self.en_cours = False
    
    def rechercher_et_apprendre(self, sujet, callback=None):
        sujet = sujet.lower().strip()
        sujet = re.sub(r'[^\w\s]', ' ', sujet)
        
        # Nettoyer
        mots_interrogatifs = ['qui','que','quoi','quel','quelle','comment',
                              'pourquoi','quand','ou','est','ce']
        for mot in mots_interrogatifs:
            sujet = sujet.replace(f" {mot} ", " ")
        
        sujet = ' '.join(sujet.split()).strip()
        
        if not sujet:
            return 0, []
        
        # Cas spéciaux
        cas_speciaux = {
            'photosynthese': 'Photosynthèse',
            'photosynthèse': 'Photosynthèse',
            'intelligence artificielle': 'Intelligence_artificielle',
            'ia': 'Intelligence_artificielle',
            'intelligence': 'Intelligence',
            'napoleon': 'Napoléon_Ier',
            'napoléon': 'Napoléon_Ier',
            'henri iv': 'Henri_IV_(roi_de_France)',
            'meta apprentissage': 'Métacognition',
            'apprentissage automatique': 'Apprentissage_automatique'
        }
        
        for key, value in cas_speciaux.items():
            if key in sujet:
                url = f"https://fr.wikipedia.org/wiki/{value}"
                return self.apprendre_depuis_url(url, "wikipedia", callback)
        
        # Recherche Wikipedia
        try:
            search_url = "https://fr.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": sujet,
                "format": "json",
                "srlimit": 1
            }
            headers = {'User-Agent': 'CPF-Bot/1.0'}
            response = requests.get(search_url, params=params, headers=headers, timeout=5)
            data = response.json()
            
            if data.get("query", {}).get("search"):
                best_match = data["query"]["search"][0]["title"]
                clean_title = best_match.replace(" ", "_")
                url = f"https://fr.wikipedia.org/wiki/{urllib.parse.quote(clean_title)}"
                return self.apprendre_depuis_url(url, "wikipedia", callback)
        except:
            pass
        
        # Fallback
        url = f"https://fr.wikipedia.org/wiki/{urllib.parse.quote(sujet.capitalize())}"
        return self.apprendre_depuis_url(url, "wikipedia", callback)


# ========== CLASSE MOTEUR RÉPONSES ==========
class MoteurReponses:
    def __init__(self, base):
        self.base = base
    
    def repondre(self, question):
        """Génère une réponse intelligente"""
        resultats = self.base.rechercher(question)
        
        if not resultats:
            return {"trouve": False, "reponse": f"Je ne connais pas encore {question}."}
        
        reponse = f"**{question.capitalize()}**\n\n"
        phrases = []
        sources = set()
        
        for r in resultats[:5]:
            concept = r["concept"]
            sources.add(concept.source)
            
            for phrase in re.split(r'[.!?]+', concept.texte):
                phrase = phrase.strip()
                if len(phrase) < 40:
                    continue
                
                phrase = re.sub(r'\[\d+\]', '', phrase)
                phrase = re.sub(r'\s+', ' ', phrase).strip()
                
                if phrase and phrase[0].islower():
                    phrase = phrase[0].upper() + phrase[1:]
                
                phrase_lower = phrase.lower()
                score = 0
                
                # Mots de la question
                mots_question = self.base._extraire_mots(question)
                for mot in mots_question:
                    if mot in phrase_lower:
                        score += 1
                
                if score > 0:
                    phrases.append((phrase, score))
        
        if phrases:
            phrases.sort(key=lambda x: x[1], reverse=True)
            for phrase, _ in phrases[:3]:
                reponse += f"• {phrase}.\n\n"
            
            if sources:
                reponse += f"📚 **Sources :** {', '.join(list(sources)[:3])}"
            
            return {"trouve": True, "reponse": reponse}
        
        return {"trouve": False, "reponse": f"Je ne connais pas encore {question}."}

    def detecter_intention(self, question):
        """Détecte l'intention de l'utilisateur"""
        question_lower = question.lower()
        
        intentions = {
            'definition': ['qu\'est ce que', 'qu\'est-ce que', 'définition', 'c\'est quoi', 'que signifie'],
            'comparaison': ['différence entre', 'comparaison', 'vs', 'versus', 'comparer'],
            'explication': ['comment', 'pourquoi', 'explique', 'expliquer'],
            'liste': ['liste des', 'quels sont', 'les différents', 'types de'],
            'biographie': ['qui est', 'qui était', 'biographie'],
            'historique': ['histoire de', 'origine de', 'date de']
        }
        
        for intention, mots in intentions.items():
            for mot in mots:
                if mot in question_lower:
                    return intention
        
        return 'generale'

    def suggerer_articles_connexes(self, question, resultats, limite=3):
        """Suggère des articles connexes pertinents basés sur la question"""
        suggestions = []
        
        # 1. ANALYSER LA QUESTION EN PROFONDEUR
        question_lower = question.lower()
        
        # Mots-clés spécifiques à ignorer pour la similarité
        mots_ignores = {'qui','que','quoi','quel','quelle','quels','quelles',
                        'comment','pourquoi','quand','ou','est','ce','dans',
                        'pour','avec','sans','sur','par','chez','vers','chez',
                        'trouve','trouver','situer','situation','localisation',
                        'localiser','ou se trouve','ou est'}
        
        # Extraire les vrais mots-clés de la question
        mots_cles_question = []
        for mot in question_lower.split():
            mot_propre = re.sub(r'[^\w]', '', mot)
            if len(mot_propre) > 3 and mot_propre not in mots_ignores:
                mots_cles_question.append(mot_propre)
        
        # 2. CAS SPÉCIAUX DE LOCALISATION
        if any(mot in question_lower for mot in ['ou se trouve', 'ou est', 'localiser', 'situer']):
            # Extraire le lieu recherché
            lieu = None
            patterns = [
                r'ou se trouve ([\w\s]+)',
                r'ou est ([\w\s]+)',
                r'localiser ([\w\s]+)',
                r'situation de ([\w\s]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, question_lower)
                if match:
                    lieu = match.group(1).strip()
                    break
            
            if lieu:
                # Chercher des concepts géographiques
                mots_lieu = lieu.split()
                for cid, concept in self.base.concepts.items():
                    texte = concept.texte.lower()
                    # Chercher des indices de localisation
                    if any(geo in texte for geo in ['ville', 'pays', 'capitale', 'région', 'situé', 'localisé']):
                        score = 0
                        for mot in mots_lieu:
                            if mot in texte:
                                score += 5
                            if mot in concept.mots_cles:
                                score += 10
                        if score > 0:
                            suggestions.append({
                                'titre': concept.mots_cles[0] if concept.mots_cles else "Lieu",
                                'description': concept.texte[:150] + "...",
                                'score': score,
                                'source': concept.source,
                                'type': 'geographie'
                            })
        
        # 3. SI PAS DE RÉSULTATS GÉOGRAPHIQUES, UTILISER LA SIMILARITÉ SÉMANTIQUE AVANCÉE
        if not suggestions:
            scores = {}
            
            for cid, concept in self.base.concepts.items():
                # Ignorer les concepts déjà dans les résultats
                if any(r['concept'].id == cid for r in resultats):
                    continue
                
                score = 0
                texte = concept.texte.lower()
                mots_concept = set(concept.mots_cles)
                
                # Similarité par mots-clés (poids fort)
                for mot in mots_cles_question:
                    if mot in mots_concept:
                        score += 10
                    elif mot in texte:
                        score += 3
                    
                    # Recherche de mots composés
                    for mot_concept in mots_concept:
                        if mot in mot_concept or mot_concept in mot:
                            score += 5
                
                # Pénaliser les concepts trop génériques
                mots_generiques = ['intelligence', 'apprentissage', 'histoire', 'definition', 'concept']
                if any(g in mots_concept for g in mots_generiques):
                    if not any(mot in mots_cles_question for mot in ['intelligence', 'apprentissage']):
                        score *= 0.3  # Forte pénalisation
                
                # Bonus pour les concepts spécifiques au domaine
                if 'mécanique' in mots_cles_question:
                    mots_mecanique = ['force', 'mouvement', 'physique', 'newton', 'loi', 'masse', 'accélération']
                    if any(m in mots_concept for m in mots_mecanique):
                        score += 15
                    if any(m in texte for m in mots_mecanique):
                        score += 8
                
                if 'new york' in question_lower:
                    mots_ny = ['new york', 'nyc', 'manhattan', 'brooklyn', 'usa', 'amérique', 'city']
                    if any(m in mots_concept or m in texte for m in mots_ny):
                        score += 20
                
                if score > 0:
                    scores[cid] = score
            
            # Trier et prendre les meilleurs
            for cid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limite]:
                concept = self.base.concepts[cid]
                
                # Améliorer la description
                description = concept.texte[:150] + "..."
                
                # Chercher une phrase plus pertinente
                phrases = re.split(r'[.!?]+', concept.texte)
                for p in phrases:
                    p_lower = p.lower()
                    # Si la phrase contient plusieurs mots-clés
                    mots_trouves = sum(1 for mot in mots_cles_question if mot in p_lower)
                    if mots_trouves >= 2 and len(p) > 30:
                        description = p.strip()[:150] + "..."
                        break
                
                suggestions.append({
                    'titre': concept.mots_cles[0] if concept.mots_cles else "Concept",
                    'description': description,
                    'score': score,
                    'source': concept.source,
                    'id': cid
                })
        
        return suggestions[:limite]

# ========== CLASSE NLP SIMPLIFIÉE (sans transformers) ==========
class MoteurNLP:
    def __init__(self):
        self.initialise = True  # Toujours initialisé car on utilise TextBlob
    
    def analyser_sentiment(self, texte):
        try:
            blob = TextBlob(texte)
            return {
                'polarite': blob.sentiment.polarity,
                'subjectivite': blob.sentiment.subjectivity
            }
        except:
            return {'polarite': 0, 'subjectivite': 0}
    
    def resumer_texte(self, texte, max_len=150):
        """Résumé simple basé sur les premières phrases"""
        if len(texte) <= max_len:
            return texte
        
        # Prendre les premières phrases
        phrases = re.split(r'[.!?]+', texte)
        resume = ""
        for p in phrases:
            if len(resume) + len(p) < max_len:
                resume += p + ". "
            else:
                break
        
        return resume.strip() + "..."


# ========== CLASSE APPRENTISSAGE RENFORCÉ ==========
class ApprentissageRenforce:
    def __init__(self, base):
        self.base = base
        self.historique_recherches = []
        self.feedback_explicite = {}
        self.seuils_adaptatifs = {
            'pertinence_min': 0.3,
            'profondeur_recherche': 2
        }
    
    def enregistrer_recherche(self, requete, resultats, temps):
        self.historique_recherches.append({
            'timestamp': datetime.now().isoformat(),
            'requete': requete,
            'nb_resultats': len(resultats),
            'temps': temps
        })
    
    def enregistrer_feedback(self, concept_id, note, requete=None):
        if concept_id not in self.feedback_explicite:
            self.feedback_explicite[concept_id] = []
        
        self.feedback_explicite[concept_id].append({
            'note': note,
            'timestamp': datetime.now().isoformat(),
            'requete': requete
        })
        
        # Mettre à jour l'auto-évaluation
        self.base.auto_evaluer_concept(concept_id, note)
    
    def suggerer_sujets(self, limite=5):
        """Suggère des sujets à apprendre"""
        suggestions = []
        
        # Mots-clés fréquents dans les recherches
        if self.historique_recherches:
            mots_recherches = Counter()
            for r in self.historique_recherches[-20:]:
                mots = self.base._extraire_mots(r['requete'])
                mots_recherches.update(mots)
            
            suggestions.append({
                'type': 'recherches_frequentes',
                'sujets': [m for m, _ in mots_recherches.most_common(limite)]
            })
        
        # Concepts avec faible score mais potentiel
        concepts_faibles = []
        for cid, c in self.base.concepts.items():
            if hasattr(c, 'auto_meta'):
                if c.auto_meta['pertinence_calculee'] < 0.4 and c.auto_meta['consultations'] > 0:
                    concepts_faibles.append({
                        'id': cid,
                        'mots': c.mots_cles[:3],
                        'score': c.auto_meta['pertinence_calculee']
                    })
        
        if concepts_faibles:
            concepts_faibles.sort(key=lambda x: x['score'])
            suggestions.append({
                'type': 'concepts_a_renforcer',
                'concepts': concepts_faibles[:limite]
            })
        
        return suggestions

class ApprentissageProfond:
    """Système d'apprentissage récursif qui approfondit les concepts"""
    
    def __init__(self, base, apprentissage_web):
        self.base = base
        self.apprentissage = apprentissage_web
        self.mots_appris = set()
        self.file_attente = []
        self.en_cours = False
        self.historique_apprentissages = []



    def analyser_texte(self, texte, profondeur=0, max_profondeur=3):
        """Analyse un texte et identifie les mots inconnus (version améliorée)"""
        if profondeur >= max_profondeur:
            return []
        
        mots_inconnus = []
        
        # Nettoyer le texte
        texte_propre = texte.lower()
        texte_propre = re.sub(r'[^\w\s]', ' ', texte_propre)
        
        # Enlever les accents
        accents = {'é':'e','è':'e','ê':'e','ë':'e','à':'a','â':'a','ä':'a',
                   'î':'i','ï':'i','ô':'o','ö':'o','ù':'u','û':'u','ü':'u','ç':'c'}
        for acc, sans in accents.items():
            texte_propre = texte_propre.replace(acc, sans)
        
        # Extraire les mots
        mots = set(re.findall(r'\b\w{4,}\b', texte_propre))
        
        # Mots à ignorer (trop communs)
        mots_ignores = {
            'dans','pour','avec','sans','tout','tous','toute','toutes',
            'une','des','les','ces','mais','donc','est','sont','qui','que',
            'dont','ou','par','sur','aussi','tres','plus','moins','cette',
            'ce','cet','ces','mon','ton','son','mes','tes','ses','notre',
            'votre','leur','nos','vos','leurs','lui','elle','eux','elles',
            'ils','je','tu','il','nous','vous','elles','vers','chez',
            'pendant','depuis','jusque','hormis','sauf','et','ou','donc',
            'or','ni','car','comme','lorsque','quand','si','ainsi','enfin',
            'ensuite','alors','puis','voila','voici','peut','peux','peuvent',
            'faire','etre','avoir','aller','venir','dire','voir','savoir',
            'temps','chose','personne','monde','annee','jour','fois','homme',
            'femme','enfant','famille','partie','nom','lieu','ville','pays'
        }
        
        # Mots importants à toujours apprendre
        mots_importants = {
            'physique','chimie','biologie','mathematique','philosophie',
            'histoire','geographie','litterature','linguistique','economie',
            'sociologie','psychologie','informatique','technologie','ingenierie',
            'mecanique','optique','thermodynamique','electromagnetisme',
            'quantique','relativite','astronomie','geologie','botanique',
            'zoologie','anatomie','physiologie','genetique','evolution',
            'ecologie','climatologie','meteorologie','oceanographie'
        }
        
        for mot in mots:
            if mot in mots_ignores or len(mot) < 4:
                continue
            
            # Vérifier si le mot est connu
            mot_connu = False
            
            # Vérification exacte
            if mot in self.base.index_mots_cles:
                mot_connu = True
            else:
                # Vérification approximative
                for connu in self.base.index_mots_cles.keys():
                    if mot in connu or connu in mot:
                        # Similarité > 80%
                        if len(set(mot) & set(connu)) / max(len(mot), len(connu)) > 0.8:
                            mot_connu = True
                            break
            
            # Vérifier dans l'historique
            if mot in self.mots_appris:
                mot_connu = True
            
            # Marquer comme inconnu si c'est un mot important
            if not mot_connu and (mot in mots_importants or profondeur == 0):
                mots_inconnus.append({
                    'mot': mot,
                    'contexte': texte[:100],
                    'profondeur': profondeur,
                    'important': mot in mots_importants
                })
        
        # Trier par importance
        mots_inconnus.sort(key=lambda x: (not x['important'], x['profondeur']))
        
        return mots_inconnus
    
    def apprendre_mot(self, mot, profondeur=0, callback=None):
        """Apprend la définition d'un mot"""
        if mot in self.mots_appris:
            return 0, []
        
        if callback:
            callback(f"📚 Apprentissage récursif: '{mot}' (profondeur {profondeur})", "apprentissage")
        
        # Rechercher le mot
        n, concepts = self.apprentissage.rechercher_et_apprendre(mot, callback)
        
        if n > 0:
            self.mots_appris.add(mot)
            self.historique_apprentissages.append({
                'mot': mot,
                'profondeur': profondeur,
                'nb_concepts': n,
                'date': datetime.now().isoformat()
            })
            
            # Analyser les définitions apprises
            for concept in concepts:
                sous_mots = self.analyser_texte(concept.texte, profondeur + 1)
                for sous_mot in sous_mots:
                    self.file_attente.append(sous_mot)
            
            return n, concepts
        return 0, []
    
    def apprendre_en_profondeur(self, texte_initial, callback=None, max_profondeur=3):
        """Apprend récursivement tous les concepts d'un texte"""
        self.file_attente = self.analyser_texte(texte_initial, 0, max_profondeur)
        total_appris = 0
        tous_concepts = []
        
        while self.file_attente and not self.en_cours:
            self.en_cours = True
            try:
                # Prendre le prochain mot à apprendre
                item = self.file_attente.pop(0)
                mot = item['mot']
                profondeur = item['profondeur']
                
                if profondeur >= max_profondeur:
                    continue
                
                n, concepts = self.apprendre_mot(mot, profondeur, callback)
                if n > 0:
                    total_appris += n
                    tous_concepts.extend(concepts)
                
                # Petite pause pour ne pas surcharger
                time.sleep(1)
                
            finally:
                self.en_cours = False
        
        return total_appris, tous_concepts
    
    def obtenir_statistiques(self):
        """Retourne les statistiques d'apprentissage profond"""
        return {
            'mots_appris': len(self.mots_appris),
            'total_cycles': len(self.historique_apprentissages),
            'file_attente': len(self.file_attente),
            'dernier_apprentissage': self.historique_apprentissages[-1] if self.historique_apprentissages else None
        }

class SecuriteCPF:
    """Système de chiffrement et d'anonymisation"""
    
    def __init__(self, mot_de_passe=None):
        self.mot_de_passe = mot_de_passe or self._obtenir_mot_de_passe()
        # Générer un sel aléatoire et le sauvegarder
        self.fichier_sel = "cpf_salt.bin"
        self.sel = self._charger_ou_creer_sel()
        self.cle = self._generer_cle()
        self.cipher = Fernet(self.cle)
        self.patterns_pii = self._compiler_patterns_pii()
        
    def _obtenir_mot_de_passe(self):
        """Obtient le mot de passe de l'utilisateur"""
        try:
            import tkinter.simpledialog
            root = tk.Tk()
            root.withdraw()
            mot_de_passe = tkinter.simpledialog.askstring(
                "Chiffrement CPF",
                "Entrez un mot de passe pour chiffrer vos données:",
                show='*'
            )
            root.destroy()
            if mot_de_passe:
                return mot_de_passe.encode()
            else:
                return b"cpf_default_password_change_me"
        except:
            return b"cpf_default_password_change_me"
    
    def _charger_ou_creer_sel(self):
        """Charge ou crée un sel aléatoire"""
        if os.path.exists(self.fichier_sel):
            with open(self.fichier_sel, 'rb') as f:
                return f.read()
        else:
            sel = os.urandom(16)
            with open(self.fichier_sel, 'wb') as f:
                f.write(sel)
            return sel
    
    def _generer_cle(self):
        """Génère une clé de chiffrement à partir du mot de passe"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.sel,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.mot_de_passe))
        return key
    
    def _compiler_patterns_pii(self):
        """Compile les patterns pour détecter les informations personnelles"""
        return {
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'telephone': re.compile(r'\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b'),
            'adresse_ip': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'code_postal': re.compile(r'\b(?:0[1-9]|[1-8]\d|9[0-8])\d{3}\b'),
            'securite_sociale': re.compile(r'\b[1-3]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b'),
            'carte_bancaire': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'nom_complet': re.compile(r'\b(?:M(?:me)?|Mlle)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'),
            'date_naissance': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        }
    
    def anonymiser_texte(self, texte, remplacer_par="[ANONYMISE]"):
        """Anonymise les informations personnelles dans un texte"""
        if not isinstance(texte, str):
            return texte
        texte_anonyme = texte
        for nom, pattern in self.patterns_pii.items():
            texte_anonyme = pattern.sub(remplacer_par, texte_anonyme)
        return texte_anonyme
    
    def chiffrer_donnees(self, donnees):
        """Chiffre des données sérialisables"""
        try:
            # Sérialiser en JSON
            json_data = json.dumps(donnees, ensure_ascii=False).encode('utf-8')
            # Chiffrer
            encrypted = self.cipher.encrypt(json_data)
            return encrypted
        except Exception as e:
            print(f"❌ Erreur chiffrement: {e}")
            return None
    
    def dechiffrer_donnees(self, donnees_chiffrees):
        """Déchiffre des données"""
        try:
            decrypted = self.cipher.decrypt(donnees_chiffrees)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            print(f"❌ Erreur déchiffrement: {e}")
            return None
    
    def sauvegarder_securisee(self, donnees, fichier, anonymiser=True):
        """Sauvegarde avec chiffrement et anonymisation optionnelle"""
        try:
            # Anonymiser si demandé
            if anonymiser:
                donnees = self._anonymiser_donnees(donnees)
            
            # Chiffrer
            encrypted = self.chiffrer_donnees(donnees)
            if encrypted:
                with open(fichier, 'wb') as f:
                    f.write(encrypted)
                return True
        except Exception as e:
            print(f"❌ Erreur sauvegarde sécurisée: {e}")
        return False
    
    def charger_securisee(self, fichier):
        """Charge des données chiffrées"""
        try:
            if not os.path.exists(fichier):
                return None
            with open(fichier, 'rb') as f:
                encrypted = f.read()
            return self.dechiffrer_donnees(encrypted)
        except Exception as e:
            print(f"❌ Erreur chargement sécurisé: {e}")
            return None
    
    def _anonymiser_donnees(self, donnees):
        """Anonymise récursivement toutes les chaînes dans les données"""
        if isinstance(donnees, dict):
            return {k: self._anonymiser_donnees(v) for k, v in donnees.items()}
        elif isinstance(donnees, list):
            return [self._anonymiser_donnees(item) for item in donnees]
        elif isinstance(donnees, str):
            return self.anonymiser_texte(donnees)
        elif hasattr(donnees, '__dict__'):  # Pour les objets personnalisés
            for attr, value in donnees.__dict__.items():
                if isinstance(value, str):
                    setattr(donnees, attr, self.anonymiser_texte(value))
            return donnees
        else:
            return donnees
    
    def generer_rapport_securite(self):
        """Génère un rapport sur la sécurité des données"""
        rapport = {
            'chiffrement': 'AES-256 via Fernet',
            'kdf': 'PBKDF2HMAC avec SHA256',
            'iterations': 100000,
            'sel_taille': len(self.sel),
            'anonymisation_activee': True,
            'patterns_pii': list(self.patterns_pii.keys()),
            'nombre_patterns': len(self.patterns_pii),
            'date_rapport': datetime.now().isoformat()
        }
        return rapport
    
# ========== CLASSE VISUALISATION ==========
class VisualisationConnaissances:
    def __init__(self, base):
        self.base = base
        self.graph = None
    
    def construire_graphe(self, max_noeuds=None):  # max_noeuds optionnel
        """Construit un graphe des connaissances (complet si max_noeuds=None)"""
        G = nx.Graph()
        
        # Prendre tous les concepts si max_noeuds est None
        if max_noeuds is None:
            concepts_liste = list(self.base.concepts.items())
        else:
            concepts_liste = list(self.base.concepts.items())[:max_noeuds]
        
        if not concepts_liste:
            return G
        
        # Ajouter les noeuds
        for cid, concept in concepts_liste:
            label = concept.mots_cles[0] if concept.mots_cles else cid[:4]
            taille = 200  # Taille de base réduite pour permettre plus de noeuds
            if hasattr(concept, 'auto_meta'):
                taille = 200 + (concept.auto_meta['pertinence_calculee'] * 200)
            
            G.add_node(cid[:8], label=label, size=taille, source=concept.source,
                      mots=','.join(concept.mots_cles[:3]))
        
        # Ajouter des liens basés sur les mots-clés partagés
        nodes = list(G.nodes)
        concepts_dict = dict(concepts_liste)
        
        # Pour optimiser avec beaucoup de noeuds
        if len(nodes) > 100:
            # Version optimisée : ne connecter que les concepts avec des mots-clés en commun
            mots_a_concepts = {}
            for i, (cid, concept) in enumerate(concepts_liste):
                for mot in concept.mots_cles[:5]:  # Limiter aux 5 premiers mots-clés
                    if mot not in mots_a_concepts:
                        mots_a_concepts[mot] = []
                    mots_a_concepts[mot].append(cid[:8])
            
            for mot, concepts_mot in mots_a_concepts.items():
                if len(concepts_mot) > 20:  # Ignorer les mots trop communs
                    continue
                for i in range(len(concepts_mot)):
                    for j in range(i+1, len(concepts_mot)):
                        if G.has_edge(concepts_mot[i], concepts_mot[j]):
                            G[concepts_mot[i]][concepts_mot[j]]['weight'] += 1
                        else:
                            G.add_edge(concepts_mot[i], concepts_mot[j], weight=1)
        else:
            # Version simple pour petits graphes
            for i, cid1 in enumerate(nodes):
                for j, cid2 in enumerate(nodes[i+1:], i+1):
                    concept1 = concepts_dict.get(list(concepts_dict.keys())[i])
                    concept2 = concepts_dict.get(list(concepts_dict.keys())[j])
                    
                    if concept1 and concept2:
                        communs = set(concept1.mots_cles) & set(concept2.mots_cles)
                        if communs:
                            G.add_edge(cid1, cid2, weight=len(communs))
        
        self.graph = G
        return G

    def dessiner(self, ax):
        """Dessine le graphe avec adaptation intelligente"""
        if not self.graph or len(self.graph.nodes) == 0:
            ax.text(0.5, 0.5, "Pas assez de données", ha='center', va='center', fontsize=14)
            return
        
        n_nodes = len(self.graph.nodes)
        
        # Adapter l'affichage selon le nombre de nœuds
        if n_nodes > 500:
            node_size = 20
            font_size = 3
            k = 8
            with_labels = False
        elif n_nodes > 200:
            node_size = 40
            font_size = 4
            k = 6
            with_labels = False
        elif n_nodes > 100:
            node_size = 60
            font_size = 5
            k = 4
            with_labels = True
        elif n_nodes > 50:
            node_size = 80
            font_size = 6
            k = 3
            with_labels = True
        else:
            node_size = 150
            font_size = 8
            k = 2
            with_labels = True
        
        # Positionnement optimisé
        pos = nx.spring_layout(self.graph, k=k, iterations=50)
        
        # Dessiner les nœuds
        nx.draw_networkx_nodes(self.graph, pos, node_size=node_size,
                              node_color='lightblue', alpha=0.7, ax=ax)
        
        # Dessiner les arêtes (avec transparence adaptative)
        if self.graph.edges:
            weights = [min(d['weight'], 3) for (u,v,d) in self.graph.edges(data=True)]
            alpha = 0.1 if n_nodes > 200 else 0.2
            nx.draw_networkx_edges(self.graph, pos, width=weights, alpha=alpha, ax=ax)
        
        # Labels (seulement si nécessaire)
        if with_labels:
            labels = {n: self.graph.nodes[n].get('label', n[:4]) for n in self.graph.nodes}
            nx.draw_networkx_labels(self.graph, pos, labels, font_size=font_size, ax=ax)
        
        ax.set_title(f"Graphe des connaissances ({n_nodes} concepts)")
        ax.axis('off')


# ========== CLASSE EXPORT ==========
class ExportConnaissances:
    def __init__(self, base):
        self.base = base
    
    def exporter_pdf(self, fichier):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Base de connaissances CPF", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Total: {self.base.taille()} concepts", ln=1)
        pdf.ln(10)
        
        for i, (cid, concept) in enumerate(list(self.base.concepts.items())[:30]):
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(200, 8, txt=f"Concept {i+1}: {', '.join(concept.mots_cles[:3])}", ln=1)
            pdf.set_font("Arial", '', 8)
            pdf.multi_cell(0, 5, txt=concept.texte[:200] + "...")
            pdf.ln(5)
        
        pdf.output(fichier)
    
    def exporter_csv(self, fichier):
        with open(fichier, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Source', 'Date', 'Mots-clés', 'Texte'])
            
            for cid, concept in self.base.concepts.items():
                writer.writerow([
                    cid,
                    concept.source,
                    concept.date[:10],
                    '|'.join(concept.mots_cles),
                    concept.texte[:500].replace('\n', ' ')
                ])
    
    def exporter_markdown(self, fichier):
        with open(fichier, 'w', encoding='utf-8') as f:
            f.write("# Base de connaissances CPF\n\n")
            f.write(f"*Généré le {datetime.now().strftime('%d/%m/%Y')}*\n\n")
            f.write(f"## Statistiques\n\n")
            f.write(f"- **Total concepts:** {self.base.taille()}\n\n")
            
            for i, (cid, concept) in enumerate(self.base.concepts.items()):
                f.write(f"### {i+1}. {', '.join(concept.mots_cles[:5])}\n\n")
                f.write(f"*Source: {concept.source}*\n\n")
                f.write(f"{concept.texte[:300]}...\n\n")
                if concept.url:
                    f.write(f"[Lien]({concept.url})\n\n")
                f.write("---\n\n")


# ========== INTERFACE PRINCIPALE ==========
class InterfaceCPF:
    def __init__(self, root):
        self.root = root
        self.root.title("CPF - Intelligence Auto-Apprenante")
        self.root.geometry("1400x900")
        
        # Composants
        self.base = get_base()
        self.apprentissage = ApprentissageWeb(self.base)
        self.moteur = MoteurReponses(self.base)
        self.moteur_nlp = MoteurNLP()
        self.apprentissage_renforce = ApprentissageRenforce(self.base)
        self.visualisation = VisualisationConnaissances(self.base)
        self.export = ExportConnaissances(self.base)
        
        # Données
        self.historique_conversations = []
        self.preferences = {
            'theme': 'clair',
            'mode_expert': False,
            'synthese_vocale': False
        }
        
        # Synthèse vocale
        self.speaker = None
        if SPEAKER_AVAILABLE:
            try:
                self.speaker = pyttsx3.init()
                self.speaker.setProperty('rate', 150)
            except:
                pass
        
        # Interface
        self.creer_interface_complete()
        
        # Charger sauvegardes
        self.charger_connaissances()
        self.charger_preferences()
        self.charger_historique()
        
        # Mise à jour périodique
        self.mise_a_jour_periodique()

        # Initialiser l'auto-apprentissage
        self.sujets_appris_auto = set()
        self.derniere_activite = time.time()

        # Démarrer les moteurs d'auto-apprentissage
        self.auto_apprentissage_continu()
        self.planifier_apprentissages()

        # Démarrer l'analyse automatique
        self.analyser_base_connaissances()

        # Démarrer l'apprentissage profond
        self.apprentissage_profond = ApprentissageProfond(self.base, self.apprentissage)

        # Démarrer l'apprentissage au repos
        self.apprentissage_au_repos()

        # ===== SÉCURITÉ =====
        self.securite = SecuriteCPF()
        self.chiffrement_active = True
        
    def creer_interface_complete(self):
        """Crée l'interface avec tous les onglets"""
        
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Sauvegarder", command=self.sauvegarder_connaissances)
        file_menu.add_command(label="Charger", command=self.charger_connaissances_dialog)
        
        # Sous-menu Export
        export_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Exporter", menu=export_menu)
        export_menu.add_command(label="PDF", command=lambda: self.exporter_connaissances('pdf'))
        export_menu.add_command(label="CSV", command=lambda: self.exporter_connaissances('csv'))
        export_menu.add_command(label="Markdown", command=lambda: self.exporter_connaissances('md'))
        
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        
        # Menu Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Thème Clair", command=lambda: self.changer_theme('clair'))
        view_menu.add_command(label="Thème Sombre", command=lambda: self.changer_theme('sombre'))
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Suggestions", command=self.afficher_suggestions)
        tools_menu.add_command(label="Analyse sentiment", command=self.analyser_sentiment)

        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.afficher_documentation)
        help_menu.add_command(label="Raccourcis", command=self.afficher_raccourcis)
        help_menu.add_separator()
        help_menu.add_command(label="À propos", command=self.afficher_a_propos)
        help_menu.add_command(label="Licence", command=self.afficher_licence)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Créer tous les onglets
        self.creer_onglet_chat()
        self.creer_onglet_apprentissage()
        self.creer_onglet_auto_dashboard()
        self.creer_onglet_stats()
        self.creer_onglet_graphe()
        self.creer_onglet_auto()
        self.creer_onglet_apprentissage_profond()        
        self.creer_onglet_analyse()
        self.creer_onglet_historique()
        self.creer_onglet_log()
        
        # Barre de statut
        self.status_bar = ttk.Label(self.root, text="Prêt", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def creer_onglet_chat(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="💬 Chat")
        
        # Zone de chat
        self.chat_area = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=20, font=("Arial", 10))
        self.chat_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_area.config(state=tk.DISABLED)
        
        self.chat_area.tag_configure("user", foreground="blue")
        self.chat_area.tag_configure("bot", foreground="green")
        
        # Saisie
        input_frame = ttk.Frame(tab)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.input_entry = ttk.Entry(input_frame, font=("Arial", 10))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.input_entry.bind("<Return>", lambda e: self.envoyer_message())
        
        ttk.Button(input_frame, text="Envoyer", command=self.envoyer_message).pack(side=tk.RIGHT)
    
    def creer_onglet_apprentissage(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🌐 Apprentissage")
        
        # Recherche
        frame = ttk.LabelFrame(tab, text="Recherche Wikipedia")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.search_entry = ttk.Entry(frame, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", lambda e: self.lancer_recherche())
        
        ttk.Button(frame, text="🔍 Rechercher", command=self.lancer_recherche).pack(side=tk.RIGHT, padx=5)
        
        # Résultats
        self.result_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=15)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def creer_onglet_stats(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Stats")
        
        self.stats_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(tab, text="Rafraîchir", command=self.rafraichir_stats).pack(pady=5)
    
    def creer_onglet_graphe(self):
        """Crée l'onglet graphe avec choix du nombre de nœuds"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🕸️ Graphe")
        
        # Frame de contrôle
        control = ttk.Frame(tab)
        control.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control, text="🔄 Générer", command=self.generer_graphe).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control, text="Nombre de nœuds:").pack(side=tk.LEFT, padx=(20,5))
        self.graph_nodes = tk.StringVar(value="100")
        nodes_combo = ttk.Combobox(control, textvariable=self.graph_nodes, 
                                   values=["50", "100", "200", "500", "1000", "Tous"], 
                                   width=10, state="readonly")
        nodes_combo.pack(side=tk.LEFT, padx=5)
        nodes_combo.bind('<<ComboboxSelected>>', lambda e: self.generer_graphe())
        
        ttk.Label(control, text="Profondeur:").pack(side=tk.LEFT, padx=(20,5))
        self.graph_depth = tk.IntVar(value=2)
        ttk.Spinbox(control, from_=1, to=5, textvariable=self.graph_depth, width=5).pack(side=tk.LEFT)
        
        # Label d'information
        self.graph_info = ttk.Label(control, text=f"Total: {self.base.taille()} concepts")
        self.graph_info.pack(side=tk.RIGHT, padx=10)
        
        # Zone du graphe
        self.graph_frame = ttk.Frame(tab)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.graph_fig = Figure(figsize=(12, 8), dpi=100)
        self.graph_ax = self.graph_fig.add_subplot(111)
        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=self.graph_frame)
        self.graph_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def creer_onglet_auto(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🤖 Auto-apprentissage")
        
        self.auto_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=20)
        self.auto_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(tab, text="Rafraîchir", command=self.rafraichir_auto).pack(pady=5)
    
    def creer_onglet_historique(self):
        """Crée l'onglet d'historique"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📜 Historique")
        
        # Frame pour les contrôles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="🔄 Rafraîchir", command=self.rafraichir_historique).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗑️ Effacer", command=self.effacer_historique).pack(side=tk.LEFT, padx=5)
        
        # Liste avec scrollbar
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                          height=25, font=("Courier", 9))
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.history_listbox.yview)
        
        # Double-clic pour voir la conversation complète
        self.history_listbox.bind('<Double-Button-1>', self.on_history_double_click)
        
        # Charger l'historique
        self.rafraichir_historique()

    def creer_onglet_log(self):
        """Ajoute un onglet de log"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Log")
        
        self.log_area = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=20, font=("Courier", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_area.tag_configure("info", foreground="black")
        self.log_area.tag_configure("succes", foreground="green")
        self.log_area.tag_configure("warning", foreground="orange")
        self.log_area.tag_configure("erreur", foreground="red")
        
        ttk.Button(tab, text="Effacer", command=self.effacer_log).pack(pady=5)
        
        self.ajouter_log("🚀 Système démarré", "succes")

    def creer_onglet_auto_dashboard(self):
        """Dashboard de l'auto-apprentissage"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Auto-Learning")
        
        # Statistiques
        stats_frame = ttk.LabelFrame(tab, text="Statistiques d'auto-apprentissage")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_stats = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, height=5)
        self.auto_stats.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sujets appris automatiquement
        appris_frame = ttk.LabelFrame(tab, text="Sujets appris automatiquement")
        appris_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.sujets_appris_list = tk.Listbox(appris_frame, height=10)
        self.sujets_appris_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Prochains apprentissages
        plan_frame = ttk.LabelFrame(tab, text="Prochains apprentissages planifiés")
        plan_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.plan_text = scrolledtext.ScrolledText(plan_frame, wrap=tk.WORD, height=3)
        self.plan_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bouton de rafraîchissement
        ttk.Button(tab, text="Rafraîchir", command=self.rafraichir_auto_dashboard).pack(pady=5)

    def rafraichir_auto_dashboard(self):
        """Met à jour le dashboard d'auto-apprentissage"""
        if not hasattr(self, 'auto_stats'):
            return
        
        # Statistiques
        self.auto_stats.delete(1.0, tk.END)
        total_auto = len(getattr(self, 'sujets_appris_auto', set()))
        self.auto_stats.insert(tk.END, f"Total sujets appris automatiquement: {total_auto}\n")
        self.auto_stats.insert(tk.END, f"Dernier apprentissage: {getattr(self, 'dernier_apprentissage_auto', 'jamais')}\n")
        
        # Liste des sujets appris
        self.sujets_appris_list.delete(0, tk.END)
        for sujet in sorted(getattr(self, 'sujets_appris_auto', set()))[-20:]:
            self.sujets_appris_list.insert(tk.END, f"• {sujet}")
        
        # Prochains apprentissages
        self.plan_text.delete(1.0, tk.END)
        interets = self.analyser_centres_interet()
        for interet in interets[:5]:
            if interet not in getattr(self, 'sujets_appris_auto', set()):
                self.plan_text.insert(tk.END, f"• {interet}\n")

    def creer_onglet_analyse(self):
        """Onglet d'analyse de la base de connaissances"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔍 Analyse Base")
        
        # Notebook interne
        inner_notebook = ttk.Notebook(tab)
        inner_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Lacunes
        lacunes_tab = ttk.Frame(inner_notebook)
        inner_notebook.add(lacunes_tab, text="Lacunes")
        self.lacunes_text = scrolledtext.ScrolledText(lacunes_tab, wrap=tk.WORD)
        self.lacunes_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Plan
        plan_tab = ttk.Frame(inner_notebook)
        inner_notebook.add(plan_tab, text="Plan d'apprentissage")
        self.plan_analyse_text = scrolledtext.ScrolledText(plan_tab, wrap=tk.WORD)
        self.plan_analyse_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Statistiques avancées
        stats_tab = ttk.Frame(inner_notebook)
        inner_notebook.add(stats_tab, text="Stats avancées")
        self.stats_avancees_text = scrolledtext.ScrolledText(stats_tab, wrap=tk.WORD)
        self.stats_avancees_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(tab, text="🔄 Analyser maintenant", command=self.analyser_maintenant).pack(pady=5)

    def analyser_maintenant(self):
        """Lance une analyse immédiate"""
        self.ajouter_log("🔍 Analyse manuelle de la base...", "info")
        
        def tache_analyse():
            try:
                # Créer une copie des données pour éviter les modifications pendant l'itération
                concepts_copy = dict(self.base.concepts)
                index_copy = dict(self.base.index_mots_cles)
                
                # Utiliser les copies pour l'analyse
                rapport = {
                    'concepts_isoles': self.detecter_concepts_isoles_with_copy(concepts_copy),
                    'mots_cles_orphelins': self.detecter_mots_cles_orphelins_with_copy(index_copy),
                    'sujets_incomplets': self.detecter_sujets_incomplets_with_copy(concepts_copy),
                    'clusters_manquants': self.detecter_clusters_manquants_with_copy(concepts_copy),
                    'relations_faibles': self.detecter_relations_faibles_with_copy(concepts_copy),
                    'hierarchies_manquantes': self.detecter_hierarchies_manquantes_with_copy(concepts_copy)
                }
                
                plan = self.generer_plan_apprentissage(rapport)
                self.root.after(0, lambda: self.afficher_analyse(rapport, plan))
                
            except Exception as e:
                self.ajouter_log(f"❌ Erreur analyse: {e}", "erreur")
        
        thread = threading.Thread(target=tache_analyse, daemon=True)
        thread.start()

    def afficher_analyse(self, rapport, plan):
        """Affiche les résultats d'analyse"""
        
        # Lacunes
        self.lacunes_text.delete(1.0, tk.END)
        self.lacunes_text.insert(tk.END, "🔍 LACUNES DÉTECTÉES\n")
        self.lacunes_text.insert(tk.END, "="*60 + "\n\n")
        
        self.lacunes_text.insert(tk.END, f"📌 Concepts isolés: {len(rapport['concepts_isoles'])}\n")
        for c in rapport['concepts_isoles'][:5]:
            self.lacunes_text.insert(tk.END, f"   • {c['mots']} ({c['connexions']} connexions)\n")
        
        self.lacunes_text.insert(tk.END, f"\n📌 Mots-clés orphelins: {len(rapport['mots_cles_orphelins'])}\n")
        for m in rapport['mots_cles_orphelins'][:5]:
            self.lacunes_text.insert(tk.END, f"   • {m['mot']}\n")
        
        self.lacunes_text.insert(tk.END, f"\n📌 Sujets incomplets: {len(rapport['sujets_incomplets'])}\n")
        for s in rapport['sujets_incomplets'][:5]:
            self.lacunes_text.insert(tk.END, f"   • {s['sujet']} ({s['nb_concepts']} concepts)\n")
        
        # Plan
        self.plan_analyse_text.delete(1.0, tk.END)
        self.plan_analyse_text.insert(tk.END, "📋 PLAN D'APPRENTISSAGE PRIORISÉ\n")
        self.plan_analyse_text.insert(tk.END, "="*60 + "\n\n")
        
        for item in plan[:10]:
            priorite = "🔴" if item['priorite'] == 1 else "🟠" if item['priorite'] == 2 else "🟡"
            self.plan_analyse_text.insert(tk.END, f"{priorite} [Prio {item['priorite']}] {item['sujet']}\n")
            self.plan_analyse_text.insert(tk.END, f"   {item['raison']}\n\n")
        
        # Stats avancées
        self.stats_avancees_text.delete(1.0, tk.END)
        self.stats_avancees_text.insert(tk.END, "📊 STATISTIQUES AVANCÉES\n")
        self.stats_avancees_text.insert(tk.END, "="*60 + "\n\n")
        
        # Densité du graphe
        G = nx.Graph()
        G.add_nodes_from(self.base.concepts.keys())
        
        edges = 0
        for mot, concepts in self.base.index_mots_cles.items():
            for i in range(len(concepts)):
                for j in range(i+1, len(concepts)):
                    edges += 1
        
        if len(G.nodes) > 1:
            densite = (2 * edges) / (len(G.nodes) * (len(G.nodes) - 1))
            self.stats_avancees_text.insert(tk.END, f"Densité du graphe: {densite:.3f}\n")
        
        # Distribution des degrés
        degrees = []
        for cid in G.nodes:
            deg = 0
            for mot in self.base.concepts[cid].mots_cles:
                if mot in self.base.index_mots_cles:
                    deg += len(self.base.index_mots_cles[mot]) - 1
            degrees.append(deg)
        
        if degrees:
            self.stats_avancees_text.insert(tk.END, f"Degré moyen: {sum(degrees)/len(degrees):.1f}\n")
            self.stats_avancees_text.insert(tk.END, f"Degré max: {max(degrees)}\n")

    def creer_onglet_apprentissage_profond(self):
        """Crée un onglet pour visualiser l'apprentissage profond"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔬 Apprentissage profond")
        
        # Statistiques
        stats_frame = ttk.LabelFrame(tab, text="Statistiques")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.profond_stats = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, height=8)
        self.profond_stats.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # File d'attente
        file_frame = ttk.LabelFrame(tab, text="File d'attente d'apprentissage")
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.profond_file = tk.Listbox(file_frame, height=10)
        self.profond_file.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Historique
        hist_frame = ttk.LabelFrame(tab, text="Historique des apprentissages")
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.profond_hist = scrolledtext.ScrolledText(hist_frame, wrap=tk.WORD, height=8)
        self.profond_hist.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Boutons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="🔄 Rafraîchir", 
                   command=self.rafraichir_profond).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Stats détaillées", 
                   command=self.afficher_stats_profond).pack(side=tk.LEFT, padx=5)
        
        # Rafraîchir initial
        self.rafraichir_profond()

    def rafraichir_profond(self):
        """Rafraîchit l'affichage de l'apprentissage profond"""
        if not hasattr(self, 'apprentissage_profond'):
            return
        
        stats = self.apprentissage_profond.obtenir_statistiques()
        
        # Mettre à jour les stats
        self.profond_stats.delete(1.0, tk.END)
        self.profond_stats.insert(tk.END, f"📊 STATISTIQUES D'APPRENTISSAGE PROFOND\n")
        self.profond_stats.insert(tk.END, f"{'='*50}\n\n")
        self.profond_stats.insert(tk.END, f"Mots appris: {stats['mots_appris']}\n")
        self.profond_stats.insert(tk.END, f"Cycles d'apprentissage: {stats['total_cycles']}\n")
        self.profond_stats.insert(tk.END, f"File d'attente: {stats['file_attente']}\n")
        
        if stats['dernier_apprentissage']:
            last = stats['dernier_apprentissage']
            self.profond_stats.insert(tk.END, f"\nDernier apprentissage:\n")
            self.profond_stats.insert(tk.END, f"   Mot: {last['mot']}\n")
            self.profond_stats.insert(tk.END, f"   Profondeur: {last['profondeur']}\n")
            self.profond_stats.insert(tk.END, f"   Concepts: {last['nb_concepts']}\n")
        
        # Mettre à jour la file d'attente
        self.profond_file.delete(0, tk.END)
        for item in self.apprentissage_profond.file_attente[:20]:
            self.profond_file.insert(tk.END, f"• {item['mot']} (prof. {item['profondeur']})")
        
        # Mettre à jour l'historique
        self.profond_hist.delete(1.0, tk.END)
        for item in self.apprentissage_profond.historique_apprentissages[-20:]:
            self.profond_hist.insert(
                tk.END, 
                f"[{item['date'][:16]}] {item['mot']} (prof.{item['profondeur']}) → {item['nb_concepts']} concepts\n"
            )

    def afficher_stats_profond(self):
        """Affiche des statistiques détaillées"""
        if not hasattr(self, 'apprentissage_profond'):
            return
        
        stats = self.apprentissage_profond.obtenir_statistiques()
        
        # Compter par profondeur
        profondeurs = {}
        for item in self.apprentissage_profond.historique_apprentissages:
            p = item['profondeur']
            profondeurs[p] = profondeurs.get(p, 0) + 1
        
        msg = "📊 STATISTIQUES DÉTAILLÉES\n\n"
        msg += f"Mots appris: {stats['mots_appris']}\n"
        msg += f"Cycles totaux: {stats['total_cycles']}\n"
        msg += f"File d'attente: {stats['file_attente']}\n\n"
        
        msg += "Répartition par profondeur:\n"
        for p in sorted(profondeurs.keys()):
            msg += f"   Profondeur {p}: {profondeurs[p]} concepts\n"
        
        messagebox.showinfo("Apprentissage profond", msg)

    def apprentissage_au_repos(self):
        """Apprend automatiquement pendant les périodes d'inactivité"""
        
        def tache_repos():
            while True:
                try:
                    time.sleep(60)  # Vérifier toutes les minutes
                    
                    if self.est_au_repos(120):  # 2 minutes d'inactivité
                        if hasattr(self, 'apprentissage_profond'):
                            if self.apprentissage_profond.file_attente:
                                self.ajouter_log(
                                    f"💤 Repos - Apprentissage de {len(self.apprentissage_profond.file_attente)} mots", 
                                    "apprentissage"
                                )
                                
                                # Apprendre quelques mots
                                for _ in range(3):
                                    if not self.apprentissage_profond.file_attente:
                                        break
                                    
                                    item = self.apprentissage_profond.file_attente.pop(0)
                                    n, _ = self.apprentissage_profond.apprendre_mot(
                                        item['mot'], 
                                        item['profondeur'],
                                        self.ajouter_log
                                    )
                                    
                                    if n > 0:
                                        self.root.after(0, self.rafraichir_profond)
                                        self.root.after(0, self.sauvegarder_connaissances)
                                    
                                    time.sleep(3)
                except:
                    pass
        
        thread = threading.Thread(target=tache_repos, daemon=True)
        thread.start()
    
    # ========== MÉTHODES FONCTIONNELLES ==========
    
    def envoyer_message(self):
        self.derniere_activite = time.time()
        message = self.input_entry.get().strip()
        if not message:
            return
        
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"\n🧑 Vous: {message}\n", "user")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        self.input_entry.delete(0, tk.END)
        
        self.status_bar.config(text="Recherche...")
        
        start = time.time()
        reponse = self.moteur.repondre(message)
        temps = time.time() - start
        
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"🤖 CPF: {reponse['reponse']}\n\n", "bot")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        self.status_bar.config(text="Prêt")

        # Après avoir obtenu la réponse
        intention = self.moteur.detecter_intention(message)
        self.ajouter_log(f"🎯 Intention détectée: {intention}", "info")

        # Récupérer les résultats
        resultats = self.base.rechercher(message) if reponse['trouve'] else []
        suggestions = self.moteur.suggerer_articles_connexes(message, resultats)

        if suggestions:
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.insert(tk.END, "\n💡 **Articles connexes suggérés:**\n", "system")
            
            # Utiliser des boutons au lieu de tags pour plus de fiabilité
#            import tkinter as tk
            
            for i, s in enumerate(suggestions[:3]):
                # Créer un frame pour chaque suggestion
                suggestion_frame = tk.Frame(self.chat_area, bg='#f0f0f0', relief=tk.RAISED, bd=1)
                self.chat_area.window_create(tk.END, window=suggestion_frame)
                
                # Titre cliquable (bouton)
                btn = tk.Button(suggestion_frame, text=f"📚 {s['titre']}", 
                               font=("Arial", 10, "bold"),
                               fg="blue", bg="#e6f3ff",
                               activebackground="#c0e0ff",
                               cursor="hand2",
                               command=lambda sujet=s['titre']: self.rechercher_suggestion(sujet))
                btn.pack(fill=tk.X, padx=2, pady=2)
                
                # Description
                desc_label = tk.Label(suggestion_frame, text=s['description'], 
                                     wraplength=600, justify=tk.LEFT,
                                     bg='#f0f0f0', font=("Arial", 9))
                desc_label.pack(fill=tk.X, padx=5, pady=2)
                
                self.chat_area.insert(tk.END, "\n")
            
            self.chat_area.insert(tk.END, "\n")
            self.chat_area.see(tk.END)
            self.chat_area.config(state=tk.DISABLED)
            
            self.ajouter_log(f"💡 {len(suggestions)} suggestions connexes", "suggestion", 
                            {"sujets": [s['titre'] for s in suggestions]})
    
        # Enregistrer
        self.historique_conversations.append({
            'timestamp': datetime.now().isoformat(),
            'question': message,
            'reponse': reponse['reponse']
        })
        
        self.apprentissage_renforce.enregistrer_recherche(message, [], temps)
        
        if not reponse["trouve"]:
            thread = threading.Thread(target=self.recherche_auto, args=(message,))
            thread.daemon = True
            thread.start()

        # Après avoir affiché la réponse
        if reponse['trouve']:
            # Lancer l'apprentissage récursif en arrière-plan
            thread = threading.Thread(
                target=self.apprentissage_recurseif_thread,
                args=(reponse['reponse'],),
                daemon=True
            )
            thread.start()

    def apprentissage_recurseif_thread(self, texte):
        """Thread pour l'apprentissage récursif"""
        try:
            self.ajouter_log("🔍 Analyse récursive du texte...", "analyse")
            
            # Analyser le texte pour trouver les mots inconnus
            mots_inconnus = self.apprentissage_profond.analyser_texte(texte)
            
            if mots_inconnus:
                self.ajouter_log(f"📚 {len(mots_inconnus)} mots inconnus détectés", "apprentissage")
                
                # Afficher dans le chat
                self.root.after(0, lambda: self.afficher_mots_inconnus(mots_inconnus))
                
                # Apprendre chaque mot inconnu
                for item in mots_inconnus[:5]:  # Limiter à 5 par cycle
                    mot = item['mot']
                    n, concepts = self.apprentissage_profond.apprendre_mot(
                        mot, 
                        profondeur=1,
                        callback=self.ajouter_log
                    )
                    
                    if n > 0:
                        self.root.after(0, lambda m=mot: self.afficher_apprentissage_profond(m))
                        
                        # Analyser récursivement les nouvelles définitions
                        for concept in concepts:
                            sous_mots = self.apprentissage_profond.analyser_texte(
                                concept.texte, 
                                profondeur=2
                            )
                            if sous_mots:
                                self.ajouter_log(
                                    f"🔄 Nouveaux mots dans '{mot}': {len(sous_mots)}", 
                                    "analyse"
                                )
                    
                    time.sleep(2)  # Pause entre les apprentissages
                
                self.sauvegarder_connaissances()
                self.rafraichir_stats()
                
        except Exception as e:
            self.ajouter_log(f"❌ Erreur apprentissage récursif: {e}", "erreur")

    def afficher_mots_inconnus(self, mots_inconnus):
        """Affiche les mots inconnus détectés"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, "\n🔍 **Mots à approfondir:**\n", "system")
        
        for item in mots_inconnus[:5]:
            self.chat_area.insert(
                tk.END, 
                f"   • {item['mot']} (profondeur {item['profondeur']})\n", 
                "system"
            )
        
        self.chat_area.insert(tk.END, "   (Apprentissage en cours...)\n\n", "system")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def afficher_apprentissage_profond(self, mot):
        """Affiche qu'un mot a été appris"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(
            tk.END, 
            f"✅ **Nouveau concept appris:** '{mot}'\n", 
            "succes"
        )
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def recherche_auto(self, question):
        mots = self.base._extraire_mots(question)
        if mots:
            n, concepts = self.apprentissage.rechercher_et_apprendre(mots[0], self.ajouter_log)
            if n > 0:
                self.root.after(0, self.sauvegarder_connaissances)
                self.root.after(0, self.rafraichir_stats)
    
    def lancer_recherche(self):
        sujet = self.search_entry.get().strip()
        if not sujet:
            return
        
        thread = threading.Thread(target=self._recherche_thread, args=(sujet,))
        thread.daemon = True
        thread.start()
    
    def _recherche_thread(self, sujet):
        n, concepts = self.apprentissage.rechercher_et_apprendre(sujet, self.ajouter_log)
        self.root.after(0, self._recherche_terminee, n, concepts)
    
    def _recherche_terminee(self, n, concepts):
        self.result_text.delete(1.0, tk.END)
        for c in concepts[:10]:
            self.result_text.insert(tk.END, f"• {c.texte[:100]}...\n")
        if n > 0:
            self.sauvegarder_connaissances()
            self.rafraichir_stats()
    
    def generer_graphe(self):
        """Génère le graphe avec le nombre de nœuds choisi"""
        self.graph_ax.clear()
        
        if self.base.taille() < 3:
            self.graph_ax.text(0.5, 0.5, "Pas assez de concepts\n(Ajoutez-en via l'onglet Apprentissage)", 
                              ha='center', va='center', fontsize=14)
            self.graph_canvas.draw()
            return
        
        # Déterminer le nombre de nœuds
        nodes_value = self.graph_nodes.get()
        if nodes_value == "Tous":
            max_noeuds = None
            self.ajouter_log(f"🕸️ Génération graphe complet: {self.base.taille()} concepts", "graphe")
        else:
            max_noeuds = int(nodes_value)
            self.ajouter_log(f"🕸️ Génération graphe: {max_noeuds} concepts", "graphe")
        
        try:
            self.visualisation.construire_graphe(max_noeuds=max_noeuds)
            self.visualisation.dessiner(self.graph_ax)
            
            # Mettre à jour l'info
            n_affiches = len(self.visualisation.graph.nodes) if self.visualisation.graph else 0
            self.graph_info.config(text=f"Affiché: {n_affiches} / Total: {self.base.taille()}")
            
        except Exception as e:
            self.graph_ax.text(0.5, 0.5, f"Erreur: {str(e)}", ha='center', va='center')
            self.ajouter_log(f"❌ Erreur graphe: {e}", "erreur")
        
        self.graph_canvas.draw()
    
    def rafraichir_stats(self):
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"📊 STATISTIQUES\n")
        self.stats_text.insert(tk.END, f"{'='*50}\n\n")
        self.stats_text.insert(tk.END, f"Total concepts: {self.base.taille()}\n")
        self.stats_text.insert(tk.END, f"Mots-clés indexés: {len(self.base.index_mots_cles)}\n\n")
        
        sources = {}
        for c in self.base.concepts.values():
            sources[c.source] = sources.get(c.source, 0) + 1
        
        self.stats_text.insert(tk.END, "Concepts par source:\n")
        for src, count in sources.items():
            self.stats_text.insert(tk.END, f"  {src}: {count}\n")
    
    def rafraichir_auto(self):
        self.auto_text.delete(1.0, tk.END)
        self.auto_text.insert(tk.END, f"🤖 AUTO-APPRENTISSAGE\n")
        self.auto_text.insert(tk.END, f"{'='*50}\n\n")
        
        suggestions = self.apprentissage_renforce.suggerer_sujets()
        for s in suggestions:
            self.auto_text.insert(tk.END, f"📌 {s.get('type', 'Suggestion')}\n")
            if 'sujets' in s:
                self.auto_text.insert(tk.END, f"   {', '.join(s['sujets'][:5])}\n")
            elif 'concepts' in s:
                for c in s['concepts'][:3]:
                    self.auto_text.insert(tk.END, f"   {c['mots']} (score: {c['score']:.2f})\n")
            self.auto_text.insert(tk.END, "\n")

    def rafraichir_historique(self):
        """Rafraîchit l'affichage de l'historique"""
        self.history_listbox.delete(0, tk.END)
        
        if not self.historique_conversations:
            self.history_listbox.insert(tk.END, "📭 Aucune conversation dans l'historique")
            return
        
        # Afficher les 100 dernières conversations
        for i, conv in enumerate(self.historique_conversations[-100:]):
            if 'question' in conv:
                # Formater la date
                if 'timestamp' in conv:
                    try:
                        dt = datetime.fromisoformat(conv['timestamp'])
                        horaire = dt.strftime("%H:%M")
                    except:
                        horaire = "??:??"
                else:
                    horaire = "??:??"
                
                # Tronquer la question
                question = conv['question'][:60] + "..." if len(conv['question']) > 60 else conv['question']
                
                # Ajouter à la liste
                display = f"[{horaire}] Q: {question}"
                self.history_listbox.insert(tk.END, display)
                
                # Colorer en bleu
                self.history_listbox.itemconfig(tk.END, {'fg': 'blue', 'bg': '#f0f0f0'})
                
                # Ajouter la réponse si disponible
                if i+1 < len(self.historique_conversations) and 'reponse' in self.historique_conversations[i+1]:
                    rep = self.historique_conversations[i+1]['reponse'][:80].replace('\n', ' ') + "..."
                    self.history_listbox.insert(tk.END, f"      └─ {rep}")
                    self.history_listbox.itemconfig(tk.END, {'fg': 'green'})
        
        self.ajouter_log(f"📜 Historique affiché: {len(self.historique_conversations)} conversations", "succes")

    def effacer_historique(self):
        """Efface tout l'historique des conversations"""
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment effacer tout l'historique ?"):
            self.historique_conversations = []
            self.history_listbox.delete(0, tk.END)
            self.history_listbox.insert(tk.END, "📭 Historique effacé")
            self.sauvegarder_historique()
            self.ajouter_log("🗑️ Historique effacé", "warning")

    def on_history_double_click(self, event):
        """Affiche la conversation complète au double-clic"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        # Trouver l'index réel (approximatif)
        index = selection[0]
        
        # Chercher la conversation correspondante
        conv_index = 0
        for i, item in enumerate(self.historique_conversations):
            if 'question' in item and conv_index >= index:
                conv = item
                break
            if 'question' in item:
                conv_index += 1
        
        if 'conv' in locals():
            dialog = tk.Toplevel(self.root)
            dialog.title("Conversation complète")
            dialog.geometry("600x500")
            
            text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=("Arial", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            if 'timestamp' in conv:
                text.insert(tk.END, f"📅 {conv['timestamp']}\n\n")
            
            text.insert(tk.END, f"🧑 QUESTION:\n{conv['question']}\n\n")
            
            # Chercher la réponse correspondante
            for i, item in enumerate(self.historique_conversations):
                if i > 0 and 'reponse' in item and self.historique_conversations[i-1].get('question') == conv['question']:
                    text.insert(tk.END, f"🤖 RÉPONSE:\n{item['reponse']}\n")
                    break
            
            text.config(state=tk.DISABLED)
            
            ttk.Button(dialog, text="Fermer", command=dialog.destroy).pack(pady=5)
        
    def exporter_connaissances(self, format='pdf'):
        fichier = filedialog.asksaveasfilename(
            defaultextension=f".{format}",
            filetypes=[(f"{format.upper()} files", f"*.{format}")]
        )
        
        if not fichier:
            return
        
        try:
            if format == 'pdf':
                self.export.exporter_pdf(fichier)
            elif format == 'csv':
                self.export.exporter_csv(fichier)
            elif format == 'md':
                self.export.exporter_markdown(fichier)
            
            messagebox.showinfo("Succès", f"Exporté vers {fichier}")
        except Exception as e:
            messagebox.showerror("Erreur", str(e))
    
    def analyser_sentiment(self):
        question = self.input_entry.get().strip()
        if not question:
            messagebox.showinfo("Info", "Entrez une question d'abord")
            return
        
        sentiment = self.moteur_nlp.analyser_sentiment(question)
        messagebox.showinfo(
            "Analyse de sentiment",
            f"Polarité: {sentiment['polarite']:.2f}\n"
            f"Subjectivité: {sentiment['subjectivite']:.2f}"
        )
    
    def afficher_suggestions(self):
        suggestions = self.apprentissage_renforce.suggerer_sujets()
        
        msg = "💡 SUGGESTIONS D'APPRENTISSAGE\n\n"
        for s in suggestions:
            msg += f"• {s.get('type', 'Suggestion')}:\n"
            if 'sujets' in s:
                msg += f"  {', '.join(s['sujets'][:5])}\n"
            msg += "\n"
        
        messagebox.showinfo("Suggestions", msg)
    
    def changer_theme(self, theme):
        themes = {
            'clair': {'bg': 'white', 'fg': 'black', 'chat_bg': '#f0f0f0'},
            'sombre': {'bg': '#2b2b2b', 'fg': 'white', 'chat_bg': '#1e1e1e'}
        }
        
        t = themes.get(theme, themes['clair'])
        self.chat_area.config(bg=t['chat_bg'], fg=t['fg'])
        self.preferences['theme'] = theme
        self.sauvegarder_preferences()
    
    def ajouter_log(self, message, type_log="info", details=None):
        """Ajoute un message au log avec détails"""
        if hasattr(self, 'log_area'):
            self.log_area.config(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Icônes par type
            icones = {
                "info": "ℹ️",
                "succes": "✅",
                "warning": "⚠️",
                "erreur": "❌",
                "apprentissage": "📚",
                "analyse": "🔍",
                "graphe": "🕸️",
                "chat": "💬",
                "suggestion": "💡",
                "historique": "📜",
                "sauvegarde": "💾",
                "chargement": "📂"
            }
            
            icone = icones.get(type_log, "•")
            
            # Format du message
            log_line = f"[{timestamp}] {icone} {message}\n"
            self.log_area.insert(tk.END, log_line, type_log)
            
            # Ajouter les détails
            if details:
                for key, value in details.items():
                    detail_line = f"      └─ {key}: {value}\n"
                    self.log_area.insert(tk.END, detail_line, "info")
            
            self.log_area.see(tk.END)
            self.log_area.config(state=tk.DISABLED)

    def log_activite(self, action, categorie="info", details=None):
        """Log une activité avec catégorie"""
        self.ajouter_log(action, categorie, details)
        self.status_bar.config(text=action[:60])

    def effacer_log(self):
        """Efface le log"""
        if hasattr(self, 'log_area'):
            self.log_area.config(state=tk.NORMAL)
            self.log_area.delete(1.0, tk.END)
            self.log_area.config(state=tk.DISABLED)
            self.ajouter_log("Log effacé", "warning")
    
    def mise_a_jour_periodique(self):
        """Met à jour l'interface périodiquement"""
        try:
            self.status_bar.config(text=f"Prêt - {self.base.taille()} concepts")
        except:
            pass
        self.root.after(5000, self.mise_a_jour_periodique)
    
    # ========== SAUVEGARDE ==========
    
    def sauvegarder_connaissances(self, fichier="cpf_knowledge.encrypted"):
        """Sauvegarde avec chiffrement"""
        try:
            data = {
                "base": self.base.to_dict(),
                "auto_apprentissage": {
                    "historique": self.apprentissage_renforce.historique_recherches[-100:],
                    "feedback": self.apprentissage_renforce.feedback_explicite,
                    "seuils": self.apprentissage_renforce.seuils_adaptatifs
                },
                "profond": self.apprentissage_profond.historique_apprentissages if hasattr(self, 'apprentissage_profond') else [],
                "version": "19.0",
                "date": datetime.now().isoformat()
            }
            
            if self.chiffrement_active:
                # Sauvegarde chiffrée
                self.securite.sauvegarder_securisee(data, fichier)
                self.ajouter_log(f"💾 Sauvegarde chiffrée: {self.base.taille()} concepts", "succes")
            else:
                # Sauvegarde normale (pour compatibilité)
                with open(fichier.replace('.encrypted', '.pkl'), 'wb') as f:
                    pickle.dump(data, f)
                self.ajouter_log(f"💾 Sauvegarde: {self.base.taille()} concepts", "succes")
            
            return True
        except Exception as e:
            self.ajouter_log(f"❌ Erreur sauvegarde: {e}", "erreur")
            return False

    def charger_connaissances(self, fichier="cpf_knowledge.encrypted"):
        """Charge avec déchiffrement"""
        try:
            if os.path.exists(fichier):
                # Chargement chiffré
                data = self.securite.charger_securisee(fichier)
                if data:
                    self._restaurer_donnees(data)
                    return True
            
            # Essayer l'ancien format
            ancien_fichier = fichier.replace('.encrypted', '.pkl')
            if os.path.exists(ancien_fichier):
                with open(ancien_fichier, 'rb') as f:
                    data = pickle.load(f)
                self._restaurer_donnees(data)
                return True
                
        except Exception as e:
            self.ajouter_log(f"❌ Erreur chargement: {e}", "erreur")
        return False

    def _restaurer_donnees(self, data):
        """Restaure les données chargées"""
        global _BASE_UNIQUE
        _BASE_UNIQUE = BaseConnaissances.from_dict(data["base"])
        self.base = _BASE_UNIQUE
        
        if "auto_apprentissage" in data:
            aa = data["auto_apprentissage"]
            self.apprentissage_renforce.historique_recherches = aa.get("historique", [])
            self.apprentissage_renforce.feedback_explicite = aa.get("feedback", {})
            self.apprentissage_renforce.seuils_adaptatifs = aa.get("seuils", 
                self.apprentissage_renforce.seuils_adaptatifs)
        
        if "profond" in data and hasattr(self, 'apprentissage_profond'):
            self.apprentissage_profond.historique_apprentissages = data["profond"]
        
        self.moteur.base = self.base
        self.apprentissage.base = self.base
        self.visualisation.base = self.base
        self.export.base = self.base
    
    def charger_connaissances_dialog(self):
        filename = filedialog.askopenfilename(filetypes=[("Pickle files", "*.pkl")])
        if filename:
            self.charger_connaissances(filename)
            self.rafraichir_stats()
            self.rafraichir_auto()
    
    def sauvegarder_preferences(self, fichier="cpf_prefs.json"):
        try:
            with open(fichier, 'w') as f:
                json.dump(self.preferences, f)
        except:
            pass
    
    def charger_preferences(self, fichier="cpf_prefs.json"):
        try:
            if os.path.exists(fichier):
                with open(fichier, 'r') as f:
                    self.preferences.update(json.load(f))
        except:
            pass
    
    def sauvegarder_historique(self, fichier="cpf_history.json"):
        try:
            with open(fichier, 'w', encoding='utf-8') as f:
                json.dump(self.historique_conversations[-100:], f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def charger_historique(self, fichier="cpf_history.json"):
        """Charge l'historique des conversations et l'affiche"""
        try:
            if os.path.exists(fichier):
                with open(fichier, 'r', encoding='utf-8') as f:
                    self.historique_conversations = json.load(f)
                
                # Mettre à jour l'affichage
                self.history_listbox.delete(0, tk.END)
                for i, conv in enumerate(self.historique_conversations[-50:]):  # Dernières 50
                    # Format: [HH:MM] Question: ...
                    if 'question' in conv:
                        timestamp = conv.get('timestamp', '')[-8:-3] if 'timestamp' in conv else '??:??'
                        question = conv['question'][:60] + "..." if len(conv['question']) > 60 else conv['question']
                        self.history_listbox.insert(tk.END, f"[{timestamp}] Q: {question}")
                        
                        # Stocker l'index de la conversation
                        self.history_listbox.itemconfig(tk.END, {'fg': 'blue'})
                        
                        # Ajouter aussi la réponse si disponible (comme sous-élément)
                        if i+1 < len(self.historique_conversations) and 'reponse' in self.historique_conversations[i+1]:
                            rep = self.historique_conversations[i+1]['reponse'][:60].replace('\n', ' ') + "..."
                            self.history_listbox.insert(tk.END, f"      └─ {rep}")
                            self.history_listbox.itemconfig(tk.END, {'fg': 'green'})
                
                self.ajouter_log(f"📜 Historique chargé: {len(self.historique_conversations)} entrées", "succes")
                return True
        except Exception as e:
            self.ajouter_log(f"❌ Erreur chargement historique: {e}", "erreur")
        return False

    def on_history_double_click(self, event):
        """Affiche la conversation complète au double-clic"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        # Trouver l'index réel dans l'historique
        hist_index = index // 2  # Parce que chaque conversation prend 2 lignes
        
        if hist_index < len(self.historique_conversations):
            conv = self.historique_conversations[hist_index]
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Conversation complète")
            dialog.geometry("600x400")
            
            text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=("Arial", 10))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text.insert(tk.END, f"📅 {conv.get('timestamp', 'Date inconnue')}\n\n")
            text.insert(tk.END, f"🧑 QUESTION:\n{conv['question']}\n\n")
            if 'reponse' in conv:
                text.insert(tk.END, f"🤖 RÉPONSE:\n{conv['reponse']}\n")
            
            text.config(state=tk.DISABLED)

    def auto_apprentissage_continu(self):
        """Moteur d'auto-apprentissage qui tourne en arrière-plan"""
        
        def tache_apprentissage():
            while True:
                try:
                    # Attendre que le système soit au repos (pas de chat actif)
                    time.sleep(30)  # Vérifier toutes les 30 secondes
                    
                    # Vérifier si l'utilisateur est inactif
                    if self.est_au_repos():
                        self.apprendre_sujets_manquants()
                        
                except:
                    pass
        
        thread = threading.Thread(target=tache_apprentissage, daemon=True)
        thread.start()

    def est_au_repos(self, duree_inactivite=60):
        """Détecte si l'utilisateur est inactif"""
        if not hasattr(self, 'derniere_activite'):
            self.derniere_activite = time.time()
            return False
        
        inactivite = time.time() - self.derniere_activite
        return inactivite > duree_inactivite

    def apprendre_sujets_manquants(self):
        """Apprend automatiquement les sujets manquants détectés"""
        
        # Analyser les conversations récentes
        sujets_manquants = self.detecter_sujets_manquants()
        
        if not sujets_manquants:
            return
        
        self.ajouter_log(f"🔍 Auto-apprentissage: {len(sujets_manquants)} sujets détectés", "info")
        
        for sujet in sujets_manquants[:3]:  # Limiter à 3 par cycle
            self.ajouter_log(f"📚 Apprentissage automatique de: {sujet}", "apprentissage")
            
            # Rechercher et apprendre
            n, concepts = self.apprentissage.rechercher_et_apprendre(sujet, self.ajouter_log)
            
            if n > 0:
                self.ajouter_log(f"✅ Auto-apprentissage: {n} concepts sur '{sujet}'", "succes")
                
                # Marquer comme appris
                self.sujets_appris_auto.add(sujet)
                
                # Sauvegarder après chaque apprentissage
                self.sauvegarder_connaissances()
                
                # Notifier l'utilisateur
                self.root.after(0, lambda s=sujet: self.notifier_apprentissage(s))
            
            time.sleep(5)  # Pause entre les recherches

    def detecter_sujets_manquants(self):
        """Détecte les sujets mentionnés mais non connus"""
        sujets_manquants = set()
        
        # Initialiser le registre des sujets appris
        if not hasattr(self, 'sujets_appris_auto'):
            self.sujets_appris_auto = set()
        
        # Analyser les 20 dernières conversations
        for conv in self.historique_conversations[-20:]:
            if 'question' not in conv:
                continue
            
            question = conv['question'].lower()
            reponse = conv.get('reponse', '').lower()
            
            # Chercher des patterns de sujets mentionnés mais non expliqués
            patterns = [
                (r'comme le ([\w\s]+)', "sujet mentionné"),
                (r'tel que ([\w\s]+)', "sujet mentionné"),
                (r'notamment ([\w\s]+)', "sujet mentionné"),
                (r'([\w\s]+) est une technique', "technique non détaillée"),
                (r'([\w\s]+) fait partie de', "concept lié non détaillé"),
            ]
            
            for pattern, raison in patterns:
                matches = re.findall(pattern, reponse)
                for match in matches:
                    sujet = match.strip()
                    if len(sujet) > 4 and sujet not in self.sujets_appris_auto:
                        # Vérifier si on connaît déjà ce sujet
                        resultats = self.base.rechercher(sujet)
                        if len(resultats) < 2:  # Peu ou pas de connaissances
                            sujets_manquants.add(sujet)
        
        # Chercher aussi dans les questions sans réponse
        for conv in self.historique_conversations[-10:]:
            if 'question' in conv and conv.get('trouve') == False:
                mots = self.base._extraire_mots(conv['question'])
                for mot in mots:
                    if len(mot) > 4 and mot not in self.sujets_appris_auto:
                        sujets_manquants.add(mot)
        
        return list(sujets_manquants)

    def notifier_apprentissage(self, sujet):
        """Notifie l'utilisateur d'un nouvel apprentissage"""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"\n🤖 [Auto-apprentissage] J'ai appris de nouveaux concepts sur '{sujet}' !\n", "system")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        self.status_bar.config(text=f"Nouveau: {sujet}")

    def analyser_reponse_pour_apprentissage(self, reponse):
        """Analyse une réponse pour trouver des sujets à approfondir"""
        sujets_a_apprendre = []
        
        # Concepts d'IA/ml à apprendre
        concepts_ia = {
            'machine learning': 'Apprentissage automatique',
            'deep learning': 'Apprentissage profond',
            'réseau de neurones': 'Réseau de neurones artificiels',
            'réseaux de neurones': 'Réseau de neurones artificiels',
            'neural network': 'Réseau de neurones artificiels',
            'apprentissage supervisé': 'Apprentissage supervisé',
            'apprentissage non supervisé': 'Apprentissage non supervisé',
            'apprentissage par renforcement': 'Apprentissage par renforcement',
            'renforcement': 'Apprentissage par renforcement',
        }
        
        reponse_lower = reponse.lower()
        
        for concept, sujet in concepts_ia.items():
            if concept in reponse_lower:
                # Vérifier si on connaît déjà ce sujet
                resultats = self.base.rechercher(sujet)
                if len(resultats) < 3:
                    sujets_a_apprendre.append(sujet)
        
        return sujets_a_apprendre

    def planifier_apprentissages(self):
        """Planifie des apprentissages basés sur les intérêts de l'utilisateur"""
        
        def tache_planification():
            while True:
                try:
                    time.sleep(3600)  # Vérifier toutes les heures
                    
                    # Analyser les centres d'intérêt
                    interets = self.analyser_centres_interet()
                    
                    for interet in interets[:2]:  # Apprendre 2 sujets par heure
                        if interet not in getattr(self, 'sujets_appris_auto', set()):
                            self.ajouter_log(f"🎯 Apprentissage programmé: {interet}", "info")
                            n, concepts = self.apprentissage.rechercher_et_apprendre(interet, self.ajouter_log)
                            
                            if n > 0:
                                self.sujets_appris_auto.add(interet)
                                self.sauvegarder_connaissances()
                                
                except:
                    pass
        
        thread = threading.Thread(target=tache_planification, daemon=True)
        thread.start()

    def analyser_centres_interet(self):
        """Analyse les conversations pour déterminer les centres d'intérêt"""
        mots_interet = Counter()
        
        for conv in self.historique_conversations[-50:]:
            if 'question' in conv:
                mots = self.base._extraire_mots(conv['question'])
                mots_interet.update(mots)
        
        # Retourner les sujets les plus fréquents
        return [mot for mot, _ in mots_interet.most_common(10)]

    def analyser_base_connaissances(self):
        """Analyse approfondie de la base pour détecter les lacunes"""
        
        def tache_analyse():
            while True:
                try:
                    time.sleep(1800)  # Analyser toutes les 30 minutes
                    
                    rapport = {
                        'concepts_isoles': self.detecter_concepts_isoles(),
                        'mots_cles_orphelins': self.detecter_mots_cles_orphelins(),
                        'sujets_populaires_incomplets': self.detecter_sujets_incomplets(),
                        'clusters_manquants': self.detecter_clusters_manquants(),
                        'relations_faibles': self.detecter_relations_faibles(),
                        'hierarchies_manquantes': self.detecter_hierarchies_manquantes()
                    }
                    
                    # Générer plan d'apprentissage
                    plan = self.generer_plan_apprentissage(rapport)
                    
                    # Exécuter les apprentissages prioritaires
                    self.executer_apprentissages_planifies(plan)
                    
                except Exception as e:
                    print(f"Erreur analyse base: {e}")
        
        thread = threading.Thread(target=tache_analyse, daemon=True)
        thread.start()

    def detecter_concepts_isoles(self):
        """Détecte les concepts qui ont peu de connexions avec d'autres"""
        concepts_isoles = []
        
        for cid, concept in self.base.concepts.items():
            # Compter les connexions via mots-clés partagés
            connexions = 0
            for mot in concept.mots_cles[:5]:
                if mot in self.base.index_mots_cles:
                    connexions += len(self.base.index_mots_cles[mot]) - 1
            
            # Si peu de connexions, c'est un concept isolé
            if connexions < 3 and self.base.taille() > 10:
                concepts_isoles.append({
                    'id': cid,
                    'mots': concept.mots_cles[:3],
                    'connexions': connexions,
                    'suggestion': self.suggerer_connexions(concept)
                })
        
        return concepts_isoles[:10]

    def detecter_mots_cles_orphelins(self):
        """Détecte les mots-clés importants qui apparaissent dans peu de concepts"""
        mots_orphelins = []
        
        for mot, concepts in self.base.index_mots_cles.items():
            # Mot-clé qui apparaît dans peu de concepts
            if len(concepts) == 1 and len(mot) > 4:
                # Vérifier si c'est un mot important (pas un mot vide)
                if mot not in ['alors', 'donc', 'mais', 'avec', 'sans']:
                    mots_orphelins.append({
                        'mot': mot,
                        'concept': concepts[0],
                        'frequence': 1
                    })
        
        return mots_orphelins[:10]

    def detecter_sujets_incomplets(self):
        """Détecte les sujets populaires qui manquent de profondeur"""
        sujets_incomplets = []
        
        # Analyser les concepts par sujet
        sujets = {}
        for cid, concept in list(self.base.concepts.items()):
            if concept.mots_cles:
                sujet_principal = concept.mots_cles[0]
                if sujet_principal not in sujets:
                    sujets[sujet_principal] = []
                sujets[sujet_principal].append(cid)
        
        # Vérifier la profondeur de chaque sujet
        for sujet, concepts in list(sujets.items()):
            if len(concepts) < 3 and len(concepts) > 0:
                if self.est_sujet_important(sujet):
                    sujets_incomplets.append({
                        'sujet': sujet,
                        'nb_concepts': len(concepts),
                        'manque': 5 - len(concepts)
                    })
        
        return sujets_incomplets

    def detecter_clusters_manquants(self):
        """Détecte les clusters de concepts qui devraient exister"""
        clusters_manquants = []
        
        # Analyser les paires de mots-clés fréquemment associés
        paires_frequentes = Counter()
        
        for cid, concept in self.base.concepts.items():
            mots = concept.mots_cles[:5]
            for i in range(len(mots)):
                for j in range(i+1, len(mots)):
                    paire = tuple(sorted([mots[i], mots[j]]))
                    paires_frequentes[paire] += 1
        
        # Chercher les paires fréquentes qui n'ont pas de concept dédié
        for (mot1, mot2), freq in paires_frequentes.most_common(20):
            if freq > 2:  # Paire apparaît souvent
                # Vérifier s'il existe un concept qui combine ces mots
                existe = False
                for cid, concept in self.base.concepts.items():
                    if mot1 in concept.mots_cles and mot2 in concept.mots_cles:
                        existe = True
                        break
                
                if not existe:
                    clusters_manquants.append({
                        'mots': [mot1, mot2],
                        'frequence': freq,
                        'suggestion': f"Créer un concept sur {mot1} et {mot2}"
                    })
        
        return clusters_manquants[:10]

    def detecter_relations_faibles(self):
        """Détecte les concepts qui devraient être mieux connectés"""
        relations_faibles = []
        
        # Construire un graphe des relations
        G = nx.Graph()
        for cid, concept in self.base.concepts.items():
            G.add_node(cid)
        
        for mot, concepts in self.base.index_mots_cles.items():
            for i in range(len(concepts)):
                for j in range(i+1, len(concepts)):
                    if G.has_edge(concepts[i], concepts[j]):
                        G[concepts[i]][concepts[j]]['weight'] += 1
                    else:
                        G.add_edge(concepts[i], concepts[j], weight=1)
        
        # Chercher les paires de concepts qui devraient être connectés
        for cid1, concept1 in list(self.base.concepts.items())[:50]:
            for cid2, concept2 in list(self.base.concepts.items())[:50]:
                if cid1 != cid2:
                    # Calculer similarité sémantique
                    communs = set(concept1.mots_cles) & set(concept2.mots_cles)
                    if len(communs) >= 2 and not G.has_edge(cid1, cid2):
                        relations_faibles.append({
                            'concept1': concept1.mots_cles[:2],
                            'concept2': concept2.mots_cles[:2],
                            'communs': list(communs),
                            'force': len(communs)
                        })
        
        return relations_faibles[:10]

    def detecter_hierarchies_manquantes(self):
        """Détecte les relations hiérarchiques manquantes (est-un, fait-partie-de)"""
        hierarchies = []
        
        # Patterns de relations hiérarchiques
        patterns = [
            (r'([\w\s]+) est un ([\w\s]+)', 'est-un'),
            (r'([\w\s]+) sont des ([\w\s]+)', 'est-un'),
            (r'([\w\s]+) fait partie des ([\w\s]+)', 'partie-de'),
            (r'([\w\s]+) est une forme de ([\w\s]+)', 'forme-de'),
            (r'([\w\s]+) est une technique de ([\w\s]+)', 'technique-de')
        ]
        
        for cid, concept in self.base.concepts.items():
            for pattern, rel_type in patterns:
                matches = re.findall(pattern, concept.texte.lower())
                for match in matches:
                    if isinstance(match, tuple):
                        sous_concept, sur_concept = match
                        # Vérifier si les deux concepts existent
                        sous_existe = self.concept_existe(sous_concept)
                        sur_existe = self.concept_existe(sur_concept)
                        
                        if sous_existe and not sur_existe:
                            hierarchies.append({
                                'type': rel_type,
                                'manquant': sur_concept,
                                'source': sous_concept,
                                'evidence': concept.texte[:100]
                            })
        
        return hierarchies[:10]

    def concept_existe(self, nom):
        """Vérifie si un concept existe approximativement"""
        nom = nom.strip().lower()
        for cid, concept in self.base.concepts.items():
            if any(nom in mot for mot in concept.mots_cles):
                return True
        return False

    def est_sujet_important(self, sujet):
        """Détermine si un sujet est important à approfondir"""
        # Critères d'importance
        mots_importants = [
            'intelligence', 'apprentissage', 'réseau', 'neurone', 'donnée',
            'algorithme', 'système', 'théorie', 'méthode', 'technique',
            'philosophie', 'science', 'histoire', 'mathématique', 'physique'
        ]
        
        return any(mot in sujet.lower() for mot in mots_importants)

    def suggerer_connexions(self, concept):
        """Suggère des connexions potentielles pour un concept isolé"""
        suggestions = []
        
        # Chercher des concepts avec des mots-clés similaires
        for mot in concept.mots_cles:
            if mot in self.base.index_mots_cles:
                for cid in self.base.index_mots_cles[mot][:3]:
                    if cid != concept.id:
                        c = self.base.concepts[cid]
                        suggestions.append(c.mots_cles[:2])
        
        return suggestions[:3]

    def generer_plan_apprentissage(self, rapport):
        """Génère un plan d'apprentissage priorisé"""
        plan = []
        
        # Priorité 1: Hiérarchies manquantes
        for h in rapport['hierarchies_manquantes']:
            plan.append({
                'priorite': 1,
                'type': 'hierarchie',
                'sujet': h['manquant'],
                'raison': f"Manque dans la hiérarchie {h['type']} de {h['source']}"
            })
        
        # Priorité 2: Sujets incomplets mais importants
        sujets_incomplets = rapport.get('sujets_incomplets', [])
        if sujets_incomplets:
            for s in sujets_incomplets:
                if isinstance(s, dict) and 'sujet' in s:
                    plan.append({
                        'priorite': 2,
                        'type': 'approfondissement',
                        'sujet': s['sujet'],
                        'raison': f"Seulement {s.get('nb_concepts', 1)} concepts, besoin d'approfondissement"
                    })
        
        # Priorité 3: Clusters manquants
        for c in rapport['clusters_manquants']:
            plan.append({
                'priorite': 3,
                'type': 'cluster',
                'sujet': f"{c['mots'][0]} {c['mots'][1]}",
                'raison': c['suggestion']
            })
        
        # Priorité 4: Mots-clés orphelins
        for m in rapport['mots_cles_orphelins']:
            plan.append({
                'priorite': 4,
                'type': 'developpement',
                'sujet': m['mot'],
                'raison': f"Mot-clé isolé dans un seul concept"
            })
        
        return sorted(plan, key=lambda x: x['priorite'])

    def executer_apprentissages_planifies(self, plan):
        """Exécute les apprentissages prioritaires"""
        
        for item in plan[:3]:  # Top 3 priorités
            sujet = item['sujet']
            
            # Vérifier si déjà appris
            if sujet in getattr(self, 'sujets_appris_auto', set()):
                continue
            
            self.ajouter_log(f"📚 Apprentissage planifié (prio {item['priorite']}): {sujet}", "info")
            self.ajouter_log(f"   Raison: {item['raison']}", "info")
            
            n, concepts = self.apprentissage.rechercher_et_apprendre(sujet, self.ajouter_log)
            
            if n > 0:
                self.sujets_appris_auto.add(sujet)
                self.dernier_apprentissage_auto = datetime.now().strftime("%H:%M")
                self.sauvegarder_connaissances()
                
                self.ajouter_log(f"✅ Apprentissage planifié réussi: {sujet}", "succes")
            
            time.sleep(10)  # Pause entre les apprentissages

    def afficher_documentation(self):
        """Affiche la documentation"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Documentation CPF")
        dialog.geometry("600x500")
        
        text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD, font=("Arial", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        doc = """
    CODAGE PRÉDICTIF FRACTAL (CPF) - DOCUMENTATION
    ===============================================

    DESCRIPTION
    -----------
    Système d'intelligence artificielle auto-apprenante qui construit
    une base de connaissances à partir de sources web.

    FONCTIONNALITÉS
    ---------------
    • Chat intelligent avec détection d'intention
    • Apprentissage automatique depuis Wikipedia
    • Auto-analyse des lacunes de connaissances
    • Suggestions d'articles connexes
    • Graphe interactif des connaissances
    • Export multi-formats (PDF, CSV, Markdown)
    • Synthèse vocale
    • Thèmes personnalisables

    UTILISATION
    -----------
    1. 💬 Chat : Posez des questions normalement
    2. 🌐 Apprentissage : Recherchez des sujets manuellement
    3. 📊 Stats : Visualisez les statistiques
    4. 🕸️ Graphe : Explorez les connexions entre concepts
    5. 🤖 Auto-apprentissage : L'IA apprend toute seule
    6. 📜 Historique : Consultez les conversations passées

    RACCOURCIS
    ----------
    • Entrée : Envoyer un message
    • Ctrl+S : Sauvegarder
    • Ctrl+O : Charger
    • Ctrl+Q : Quitter
    """
        
        text.insert(tk.END, doc)
        text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Fermer", command=dialog.destroy).pack(pady=5)

    def afficher_raccourcis(self):
        """Affiche les raccourcis clavier"""
        messagebox.showinfo(
            "Raccourcis clavier",
            "🔤 RACCOURCIS\n\n"
            "• Entrée : Envoyer un message\n"
            "• Ctrl+S : Sauvegarder la base\n"
            "• Ctrl+O : Charger une base\n"
            "• Ctrl+Q : Quitter\n"
            "• Ctrl+F : Rechercher dans l'historique\n"
            "• F5 : Rafraîchir les stats\n"
            "• F11 : Mode plein écran"
        )

    def afficher_a_propos(self):
        """Affiche la boîte À propos"""
        info = f"""
    
         CODAGE PRÉDICTIF FRACTAL       
               Version 1.0             
    
     • IA auto-apprenante               
     • Base de connaissances dynamique  
     • Analyse sémantique avancée       
     • Graphe interactif                 
     • Multi-sources                     
    
     Concepts: {self.base.taille():6d}              
     Mots-clés: {len(self.base.index_mots_cles):6d} 
     Sources: 4                          
    
     © 2026 - Tous droits réservés       
    
    """
        
        messagebox.showinfo("À propos de CPF", info)

    def afficher_licence(self):
        """Affiche la licence"""
        licence = """
    LICENCE MIT
    ===========

    Copyright (c) 2026 CPF Project

    Permission est accordée, gratuitement, à toute personne obtenant une copie
    de ce logiciel et des fichiers de documentation associés (le "Logiciel"),
    de traiter le Logiciel sans restriction, y compris sans limitation les droits
    d'utiliser, de copier, de modifier, de fusionner, de publier, de distribuer,
    de sous-licencier et/ou de vendre des copies du Logiciel, et de permettre
    aux personnes à qui le Logiciel est fourni de le faire, sous réserve des
    conditions suivantes :

    L'avis de copyright ci-dessus et cet avis de permission doivent être inclus
    dans toutes les copies ou parties substantielles du Logiciel.

    LE LOGICIEL EST FOURNI "TEL QUEL", SANS GARANTIE D'AUCUNE SORTE, EXPLICITE
    OU IMPLICITE, Y COMPRIS MAIS SANS S'Y LIMITER LES GARANTIES DE
    COMMERCIALISATION, D'ADAPTATION À UN USAGE PARTICULIER ET D'ABSENCE DE
    CONTREFAÇON. EN AUCUN CAS LES AUTEURS OU TITULAIRES DU COPYRIGHT NE SERONT
    RESPONSABLES DE TOUTE RÉCLAMATION, DOMMAGE OU AUTRE RESPONSABILITÉ, QUE CE
    SOIT DANS UNE ACTION CONTRACTUELLE, DÉLICTUELLE OU AUTRE, DÉCOULANT DE,
    HORS DE OU EN LIEN AVEC LE LOGICIEL OU L'UTILISATION OU AUTRES ACTIONS DANS
    LE LOGICIEL.
    """
        messagebox.showinfo("Licence", licence)

    def rechercher_suggestion(self, sujet):
        """Recherche un sujet suggéré"""
        self.ajouter_log(f"🔍 Recherche depuis suggestion: {sujet}", "apprentissage")
        
        # Afficher dans le chat
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, f"\n🧑 [Suggestion] Je veux en savoir plus sur: {sujet}\n", "user")
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        # Lancer la recherche
        def recherche():
            n, concepts = self.apprentissage.rechercher_et_apprendre(sujet, self.ajouter_log)
            if n > 0:
                self.root.after(0, lambda: self.afficher_resultat_suggestion(sujet, concepts))
        
        thread = threading.Thread(target=recherche, daemon=True)
        thread.start()

    def afficher_resultat_suggestion(self, sujet, concepts):
        """Affiche le résultat d'une recherche par suggestion"""
        self.chat_area.config(state=tk.NORMAL)
        
        if concepts:
            self.chat_area.insert(tk.END, f"🤖 J'ai appris {len(concepts)} nouveaux concepts sur '{sujet}' !\n\n", "bot")
            
            # Afficher un extrait
            for c in concepts[:2]:
                self.chat_area.insert(tk.END, f"• {c.texte[:150]}...\n\n", "bot")
        else:
            self.chat_area.insert(tk.END, f"🤖 Désolé, je n'ai rien trouvé sur '{sujet}'\n\n", "system")
        
        self.chat_area.see(tk.END)
        self.chat_area.config(state=tk.DISABLED)
        
        # Sauvegarder
        self.sauvegarder_connaissances()
        self.rafraichir_stats()
    
    def quit(self):
        self.sauvegarder_connaissances()
        self.sauvegarder_preferences()
        self.sauvegarder_historique()
        self.root.quit()


# ========== MAIN ==========
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 LANCEMENT DE L'APPLICATION FINALE")
    print("="*60)
    
    try:
        root = tk.Tk()
        app = InterfaceCPF(root)
        
        def on_closing():
            app.quit()
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    print("👋 Programme terminé")