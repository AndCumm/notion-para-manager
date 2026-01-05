# notion_lib.py
import requests
import json
import time
from config import DB_CONFIG, COLUMNS

class NotionManager:
    def __init__(self, token):
        self.headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.api_url = "https://api.notion.com/v1"

    def _find_page_id(self, db_id, property_name, value):
        """Helper generico per trovare una pagina dato un titolo"""
        payload = {
            "filter": {
                "property": property_name,
                "title": { "equals": value }
            }
        }
        res = requests.post(f"{self.api_url}/databases/{db_id}/query", headers=self.headers, json=payload)
        data = res.json()
        if data.get('results'):
            return data['results'][0]['id']
        return None

    def create_project(self, title, area_names=[], status="Active"):
        """Crea il progetto e lo collega a una o più Aree"""
        # Assicuriamoci che sia sempre una lista
        if isinstance(area_names, str):
            area_names = [area_names]
            
        props = {
            COLUMNS["PROJECT_TITLE"]: { "title": [{ "text": { "content": title } }] },
            "Status": { "select": { "name": status } }
        }

        # Gestione Multi-Area
        relation_ids = []
        if area_names:
            for name in area_names:
                if not name: continue
                # Cerco l'ID per ogni nome nella lista
                found_id = self._find_page_id(DB_CONFIG["AREAS"], "Area Name", name)
                if found_id:
                    relation_ids.append({ "id": found_id })
                else:
                    print(f"⚠️ Area '{name}' non trovata.")

        # Se abbiamo trovato almeno un'area valida, aggiungiamo la relazione
        if relation_ids:
            props[COLUMNS["RELATION_PROJ_AREA"]] = { "relation": relation_ids }

        payload = {
            "parent": { "database_id": DB_CONFIG["PROJECTS"] },
            "properties": props
        }
        
        res = requests.post(f"{self.api_url}/pages", headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Errore creazione Progetto: {res.text}")
        
        return res.json()['id']


    def create_task(self, title, epic, project_id):
        """Crea un task collegato al progetto e con l'Epic settata"""
        props = {
            COLUMNS["TASK_TITLE"]: { "title": [{ "text": { "content": title } }] },
            COLUMNS["RELATION_TASK_PROJ"]: { "relation": [{ "id": project_id }] }
        }

        # Gestione Epic (Solo se specificata)
        if epic:
            props[COLUMNS["EPIC_SELECT"]] = { "select": { "name": epic } }

        payload = {
            "parent": { "database_id": DB_CONFIG["TASKS"] },
            "properties": props
        }

        res = requests.post(f"{self.api_url}/pages", headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Errore Task '{title}': {res.text}")
        
        return True
    
    def get_all_areas(self):
        """Scarica la lista delle Aree (Titoli) dal database"""
        payload = { 
            "page_size": 100,
            # Opzionale: filtra solo le aree attive se vuoi
            # "filter": { "property": "Status", "status": { "equals": "Active" } } 
        }
        
        try:
            res = requests.post(f"{self.api_url}/databases/{DB_CONFIG['AREAS']}/query", headers=self.headers, json=payload)
            if res.status_code != 200:
                return []
            
            areas = []
            for page in res.json()['results']:
                props = page['properties']
                # Estrazione dinamica del titolo (qualsiasi nome abbia la colonna)
                for key, val in props.items():
                    if val['type'] == 'title' and val['title']:
                        title = val['title'][0]['plain_text']
                        areas.append(title)
                        break
            
            return sorted(areas) # Ordine alfabetico
        except:
            return []
