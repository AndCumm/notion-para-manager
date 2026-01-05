import streamlit as st
import json
import time
from notion_lib import NotionManager

# Setup pagina
st.set_page_config(page_title="Notion Deployer", page_icon="🚀")
st.title("🚀 PARA Project Deployer")

# --- FUNZIONI DI CACHING ---
@st.cache_data(ttl=600)
def fetch_areas_cached(token):
    if not token: return []
    try:
        manager = NotionManager(token)
        return manager.get_all_areas()
    except:
        return []

# --- SIDEBAR & CONFIGURAZIONE ---
with st.sidebar:
    st.header("Configurazione")
    
    # 1. Input Token
    token = st.text_input("Notion Token", type="password", help="secret_...")
    
    # 2. Fetch Aree Dinamico
    area_options = []
    if token and len(token) > 40: 
        area_options = fetch_areas_cached(token)
    
    # 3. Menu a Tendina MULTIPLO
    if area_options:
        area_targets = st.multiselect("Seleziona Aree di Appartenenza", options=area_options)
    else:
        # Fallback manuale
        manual_area = st.text_input("Nome Area (Manuale)")
        area_targets = [manual_area] if manual_area else []

# --- AI PROMPT HELPER (AGGIORNATO CON DESCRIZIONE) ---
with st.expander("🤖 Prompt Finale (Da usare a fine chat)"):
    st.markdown("""
    Dopo aver definito Progetto, Descrizioni, Epic e Task in chat, incolla questo comando per ottenere il JSON:
    
    ```text
    Perfetto. Ora prendi la struttura definita sopra e trasformala nel JSON per il mio Deployer.
    
    Regole:
    1. Includi una descrizione sintetica per il Progetto e per ogni Task se ne abbiamo discusso.
    2. Mantieni la numerazione gerarchica (es. "1.1 Task").
    3. Usa questa struttura JSON esatta:
    
    [
      {
        "title": "Nome Progetto",
        "description": "Obiettivo finale del progetto...",
        "tasks": [
          { 
            "title": "1.1 Nome Task", 
            "epic": "1. Nome Epic",
            "description": "Dettagli operativi del task..."
          }
        ]
      }
    ]
    ```
    """)

# --- INTERFACCIA PRINCIPALE ---
st.subheader("Blueprint Progetto")

# Esempio JSON Completo
example_json = [
    {
        "title": "Esempio Progetto",
        "description": "Descrizione di alto livello del progetto che apparirà dentro la pagina Notion.",
        "tasks": [
            {
                "title": "1.1 Task Iniziale", 
                "epic": "1. Fase Uno",
                "description": "Dettagli su cosa fare esattamente in questo task."
            }
        ]
    }
]

json_input = st.text_area(
    "Incolla qui il JSON", 
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
                p_desc = project.get('description', None) # Prende la descrizione
                
                status_text.text(f"🏗️ Creazione Progetto: {p_title}...")
                
                # Crea Progetto passando descrizione e aree
                proj_id = manager.create_project(p_title, area_names=area_targets, description=p_desc)
                st.success(f"✅ Progetto: **{p_title}**")
                
                current_op += 1
                progress_bar.progress(current_op / total_ops)

                # 3. Loop Tasks
                tasks = project.get('tasks', [])
                for task in tasks:
                    t_title = task['title']
                    t_epic = task.get('epic', None)
                    t_desc = task.get('description', None) # Prende la descrizione task
                    
                    # Crea Task con descrizione
                    manager.create_task(t_title, t_epic, proj_id, description=t_desc)
                    st.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;🔹 Task: {t_title}")
                    
                    current_op += 1
                    progress_bar.progress(current_op / total_ops)
                    time.sleep(0.1) 

            status_text.text("✨ Deploy Completato!")
            st.balloons()
            st.cache_data.clear()

        except json.JSONDecodeError:
            st.error("❌ JSON non valido. Controlla virgole e parentesi.")
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
