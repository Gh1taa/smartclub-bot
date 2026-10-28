# Projets du semestre : Predict & Prevent et Campus Copilot

Statut : projets prévus pour le semestre, en préparation.

## Predict & Prevent (volet Donnée)
Projet de maintenance prédictive par IoT : instrumenter un équipement de test pour anticiper les pannes.
Trois parties : hardware (ESP32 avec des capteurs de vibration, de température et de courant), data et IA
(collecte, filtrage et détection d'anomalies), logiciel (dashboard pour visualiser et suivre les mesures).
Chaîne de mesure : capteurs → acquisition par ESP32 → modèle de détection d'anomalies → dashboard.
Matériel : ESP32 DevKit, accéléromètre MPU6050 ou ADXL345, capteur de température MAX30205, capteur de courant ACS712.

## Campus Copilot (volet IA)
Assistant conversationnel RAG qui répond aux questions du campus à partir d'un ensemble de documents
(emploi du temps, règlement, actualités). Les documents sont indexés et vectorisés avec ChromaDB ; l'assistant
récupère les passages pertinents et répond uniquement à partir de ces documents.
Deux pôles : le pôle Base de connaissance (centraliser, structurer et indexer les documents) et le pôle
Interface utilisateur (concevoir l'interface de dialogue).
Outils : open source (ChromaDB), hébergement de test via le GitHub Student Developer Pack, API d'un modèle de langage pour les tests.
