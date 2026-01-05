import requests
import json
from config import DB_CONFIG, COLUMNS

class NotionManager:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.api_url = "https://api.notion.com/v1"

    def _find_page_id(self, database_id, property_name, value):
        payload = {
            "filter": {
                "property": property_name,
                "title": { "equals": value } if property_name == "Name" or property_name == "Task Name" or property_name == "Project Name" else { "equals": value } # Adattamento generico per Text/Title
            }
        }
        # Special case per Title che varia spesso, usiamo query generica se serve, 
        # ma per le Aree (che sono il caso d'uso qui) di solito è "Name" o simile.
        # Per sicurezza sulle Aree usiamo un approccio più semplice nel create_project
        
        # Riscriviamo _find_page_id per essere specifico per le Aree (select/title/text)
        # Ma per le Aree usiamo la logica di get_all_areas per i nomi. 
        # Qui serve per trovare l'ID dato il nome.
        
        query = {
            "filter": {
                "property": "Area Name", # Assumiamo che la colonna si chiami così o simile, adattare se serve
                "rich_text": { "equals": value } # O title, o select
            }
        }
        # Nota: La ricerca esatta in Notion dipende dal tipo di proprietà.
        # Per semplicità, nel create_project usiamo una ricerca ottimizzata.
        return None

    def get_all_areas(self):
        """Scarica la lista delle Aree (Titoli) dal database"""
        payload = { "page_size": 100 }
        try:
            res = requests.post(f"{self.api_url}/databases/{DB_CONFIG['AREAS']}/query", headers=self.headers, json=payload)
            if res.status_code != 200: return []
            
            areas = []
            for page in res.json()['results']:
                props = page['properties']
                # Cerca la proprietà Title
                for key, val in props.items():
                    if val['type'] == 'title' and val['title']:
                        title = val['title'][0]['plain_text']
                        areas.append(title)
                        break
            return sorted(areas)
        except:
            return []

    def create_project(self, title, area_names=[], status="Active", description=None):
        """Crea il progetto, lo collega alle Aree e scrive la descrizione"""
        if isinstance(area_names, str): area_names = [area_names]
            
        props = {
            COLUMNS["PROJECT_TITLE"]: { "title": [{ "text": { "content": title } }] },
            "Status": { "select": { "name": status } } # Assicurati che la colonna Status esista
        }

        # Gestione Relazione Aree (Cerca ID basandosi sul Nome)
        # Nota: Per robustezza, facciamo una query per ogni area per trovare il suo ID
        relation_ids = []
        if area_names:
            for name in area_names:
                # Query al DB Areas per trovare la pagina con quel titolo
                payload_search = {
                    "filter": { "property": "Name", "title": { "equals": name } } # Assumiamo la colonna titolo si chiami "Name" in Areas
                }
                # Se la colonna titolo delle aree ha un nome diverso (es. "Area"), cambia "Name" qui sotto:
                # Tentativo generico: scarichiamo tutto e filtriamo in python se la query fallisce, 
                # ma per ora proviamo query diretta su titolo.
                
                # FIX: Usiamo una logica più robusta per trovare l'ID dell'area dato il nome
                # Scarichiamo e filtriamo (meno efficiente ma sicuro se non sappiamo il nome colonna)
                # O meglio: facciamo affidamento che get_all_areas ritorni i titoli esatti.
                
                # Facciamo una ricerca POST
                res = requests.post(f"{self.api_url}/databases/{DB_CONFIG['AREAS']}/query", headers=self.headers, json={})
                if res.status_code == 200:
                    for page in res.json()['results']:
                        # Estrai titolo
                        p_title = ""
                        for k, v in page['properties'].items():
                            if v['type'] == 'title' and v['title']:
                                p_title = v['title'][0]['plain_text']
                                break
                        if p_title == name:
                            relation_ids.append({ "id": page['id'] })
                            break

        if relation_ids:
            props[COLUMNS["RELATION_PROJ_AREA"]] = { "relation": relation_ids }

        payload = {
            "parent": { "database_id": DB_CONFIG["PROJECTS"] },
            "properties": props
        }
        
        # AGGIUNTA DESCRIZIONE (Body Content)
        if description:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{ "type": "text", "text": { "content": description } }]
                    }
                }
            ]
        
        res = requests.post(f"{self.api_url}/pages", headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Errore Project: {res.text}")
        
        return res.json()['id']

    def create_task(self, title, epic, project_id, description=None):
        """Crea il task collegato al progetto con descrizione"""
        props = {
            COLUMNS["TASK_TITLE"]: { "title": [{ "text": { "content": title } }] },
            COLUMNS["RELATION_TASK_PROJ"]: { "relation": [{ "id": project_id }] }
        }
        
        if epic:
            props[COLUMNS["EPIC_SELECT"]] = { "select": { "name": epic } }

        payload = {
            "parent": { "database_id": DB_CONFIG["TASKS"] },
            "properties": props
        }

        # AGGIUNTA DESCRIZIONE (Body Content)
        if description:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{ "type": "text", "text": { "content": description } }]
                    }
                }
            ]

        res = requests.post(f"{self.api_url}/pages", headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Errore Task: {res.text}")
            
        return res.json()['id']
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
