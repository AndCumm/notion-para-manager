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

# --- AI PROMPT HELPER (AGGIORNATO: FORMATTAZIONE FINALE) ---
with st.expander("🤖 Prompt Finale (Da usare a fine chat)"):
    st.markdown("""
    Dopo aver definito Progetto, Epic e Task in chat, incolla questo comando per ottenere il JSON:
    
    ```text
    Perfetto. Ora prendi la struttura definita sopra (Progetto, Epics e Tasks relativi) e trasformala nel JSON per il mio Deployer.
    
    Regole:
    1. Mantieni rigorosamente la numerazione gerarchica decisa (es. "1.1 Task").
    2. Usa esattamente le Epic che abbiamo definito.
    3. Usa questa struttura JSON esatta:
    
    [
      {
        "title": "Nome Progetto",
        "tasks": [
          { "title": "1.1 Nome Task", "epic": "1. Nome Epic" },
          { "title": "1.2 Nome Task", "epic": "1. Nome Epic" },
          { "title": "2.1 Nome Task", "epic": "2. Altra Epic" }
        ]
      }
    ]
    ```
    """)

# --- INTERFACCIA PRINCIPALE ---
st.subheader("Blueprint Progetto")

# Esempio JSON generico
example_json = [
    {
        "title": "Progetto Esempio",
        "tasks": [
            {"title": "1.1 Primo Task", "epic": "1. Fase Uno"},
            {"title": "2.1 Secondo Task", "epic": "2. Fase Due"}
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
            st.error("❌ JSON non valido. Controlla virgole e parentesi.")
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
