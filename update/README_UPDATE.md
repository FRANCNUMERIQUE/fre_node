# FRE_NODE — Gestionnaire de mise à jour

Ce dossier contient les scripts responsables de la mise à jour du nœud FRE.

---

## 🟦 1. `update_node.sh`

Fonctions principales :

- Vérifie si une nouvelle version est disponible sur GitHub  
- Sauvegarde la version actuelle (`backup/`)  
- Télécharge la nouvelle version (`git pull --rebase`)  
- Réinstalle les dépendances  
- Teste le démarrage du node avant validation  
- Applique **rollback automatique** si erreur  
- Redémarre fre-node + fre-dashboard

---

## 🟩 2. `install_update.sh`

Installe une tâche cron exécutant `update_node.sh` toutes les 10 minutes :

