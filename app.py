# app.py
import streamlit as st
import json
import time
from notion_lib import NotionManager

# Setup pagina
st.set_page_config(page_title="Notion Deployer", page_icon="🚀")
st.title("🚀 PARA Project Deployer")

# Sidebar per le credenziali
with st.sidebar:
    st.header("Configurazione")
    token = st.text_input("Notion Token", type="password", help="Incolla qui il secret_...")
    area_target = st.text_input("Nome Area (Opzionale)", value="Health and Fitness")

# Input dati progetto
st.subheader("Blueprint Progetto")

# Esempio di struttura JSON per aiutare l'utente
example_json = [
    {
        "title": "Nuovo Progetto Esempio",
        "tasks": [
            {"title": "1.1 Setup Iniziale", "epic": "1. Connectivity"},
            {"title": "2.1 Database", "epic": "2. Backend"}
        ]
    }
]

json_input = st.text_area(
    "Incolla qui il JSON del progetto", 
    height=300, 
    value=json.dumps(example_json, indent=2)
)

# Bottone Azione
if st.button("Lancia Deploy", type="primary"):
    if not token:
        st.error("❌ Manca il Token!")
    else:
        try:
            # 1. Parsing JSON
            data = json.loads(json_input)
            manager = NotionManager(token)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            total_ops = len(data) + sum(len(p.get('tasks', [])) for p in data)
            current_op = 0

            # 2. Loop Progetti
            for project in data:
                p_title = project['title']
                status_text.text(f"🏗️ Creazione Progetto: {p_title}...")
                
                # Crea Progetto
                proj_id = manager.create_project(p_title, area_name=area_target)
                st.success(f"✅ Progetto creato: **{p_title}**")
                
                current_op += 1
                progress_bar.progress(current_op / total_ops)

                # 3. Loop Tasks
                tasks = project.get('tasks', [])
                for task in tasks:
                    t_title = task['title']
                    t_epic = task.get('epic', None)
                    
                    # Crea Task
                    manager.create_task(t_title, t_epic, proj_id)
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;🔹 Task: {t_title} [{t_epic}]")
                    
                    current_op += 1
                    progress_bar.progress(current_op / total_ops)
                    time.sleep(0.1) # Rispetto API rate limit

            status_text.text("✨ Deploy Completato!")
            st.balloons()

        except json.JSONDecodeError:
            st.error("❌ Il JSON non è valido. Controlla le virgole e le parentesi.")
        except Exception as e:
            st.error(f"❌ Errore durante il deploy: {str(e)}")
