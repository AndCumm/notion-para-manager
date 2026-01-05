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

# --- AI PROMPT HELPER (Novità!) ---
with st.expander("🤖 Genera JSON con AI (Copia questo Prompt)"):
    st.markdown("""
    Copia questo testo e invialo a Gemini/ChatGPT per generare il JSON:
    
    ```text
    Devo inserire un nuovo progetto nel mio sistema Notion.
    Il progetto è: [DESCRIVI QUI LA TUA IDEA]
    
    Le Epic disponibili sono:
    1. Connectivity, 2. Backend, 3. Bridge, 4. SPoV, 
    5. Insights, 6. Engineering, 7. Security.
    
    Generami il codice JSON valido da incollare nel tool, usando questa struttura:
    [
      {
        "title": "Nome Progetto",
        "tasks": [
          { "title": "1.1 Nome Task", "epic": "1. Connectivity" },
          { "title": "7.1 Nome Task", "epic": "7. Security" }
        ]
      }
    ]
    ```
    """)

# --- INTERFACCIA PRINCIPALE ---
st.subheader("Blueprint Progetto")

# Esempio JSON "Parlante"
example_json = [
    {
        "title": "🛠️ Refactoring Home Network",
        "tasks": [
            {"title": "1.1 Configurazione VLAN IoT", "epic": "1. Connectivity"},
            {"title": "6.1 Setup Monitoring Grafana", "epic": "6. Engineering"},
            {"title": "7.1 Rotazione password Wifi", "epic": "7. Security"}
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
                status_text.text(f"🏗️ Creazione Progetto: {p_title}...")
                
                # Crea Progetto (supporta lista aree)
                proj_id = manager.create_project(p_title, area_names=area_targets)
                st.success(f"✅ Progetto creato: **{p_title}** -> {area_targets}")
                
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
                    time.sleep(0.1) 

            status_text.text("✨ Deploy Completato!")
            st.balloons()
            st.cache_data.clear()

        except json.JSONDecodeError:
            st.error("❌ JSON non valido.")
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
