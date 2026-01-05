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

    def get_all_areas(self):
        payload = {"page_size": 100}
        try:
            url = f"{self.api_url}/databases/{DB_CONFIG['AREAS']}/query"
            res = requests.post(url, headers=self.headers, json=payload)
            if res.status_code != 200:
                return []
            
            areas = []
            for page in res.json()['results']:
                props = page['properties']
                for key, val in props.items():
                    if val['type'] == 'title' and val['title']:
                        title = val['title'][0]['plain_text']
                        areas.append(title)
                        break
            return sorted(areas)
        except:
            return []

    def create_project(self, title, area_names=[], status="Active", description=None):
        if isinstance(area_names, str):
            area_names = [area_names]
            
        props = {
            COLUMNS["PROJECT_TITLE"]: {"title": [{"text": {"content": title}}]},
            "Status": {"select": {"name": status}}
        }

        relation_ids = []
        if area_names:
            url = f"{self.api_url}/databases/{DB_CONFIG['AREAS']}/query"
            res = requests.post(url, headers=self.headers, json={})
            if res.status_code == 200:
                for page in res.json()['results']:
                    p_title = ""
                    for k, v in page['properties'].items():
                        if v['type'] == 'title' and v['title']:
                            p_title = v['title'][0]['plain_text']
                            break
                    if p_title in area_names:
                        relation_ids.append({"id": page['id']})

        if relation_ids:
            props[COLUMNS["RELATION_PROJ_AREA"]] = {"relation": relation_ids}

        payload = {
            "parent": {"database_id": DB_CONFIG["PROJECTS"]},
            "properties": props
        }
        
        if description:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": description}}]
                    }
                }
            ]
        
        res = requests.post(f"{self.api_url}/pages", headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Errore Project: {res.text}")
        
        return res.json()['id']

    def create_task(self, title, epic, project_id, description=None):
        props = {
            COLUMNS["TASK_TITLE"]: {"title": [{"text": {"content": title}}]},
            COLUMNS["RELATION_TASK_PROJ"]: {"relation": [{"id": project_id}]}
        }
        
        if epic:
            props[COLUMNS["EPIC_SELECT"]] = {"select": {"name": epic}}

        payload = {
            "parent": {"database_id": DB_CONFIG["TASKS"]},
            "properties": props
        }

        if description:
            payload["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": description}}]
                    }
                }
            ]

        res = requests.post(f"{self.api_url}/pages", headers=self.headers, json=payload)
        if res.status_code != 200:
            raise Exception(f"Errore Task: {res.text}")
            
        return res.json()['id']
