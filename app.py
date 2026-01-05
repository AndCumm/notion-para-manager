import streamlit as st
import json
import time
from notion_lib import NotionManager

# Setup pagina
st.set_page_config(page_title="Notion Deployer", page_icon="🚀")
st.title("🚀 PARA Project Deployer")

# --- FUNZIONI DI CACHING ---
# Cache: Scarica le aree solo una volta ogni 10 minuti o se cambia il token
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
    if token and len(token) > 40: # Check base per non chiamare API a vuoto
        area_options = fetch_areas_cached(token)
    
    # 3. Menu a Tendina (Multiselezione resa come Selectbox singola per coerenza PARA)
    # Se vuoi davvero selezionarne più di una, usa st.multiselect invece di st.selectbox
    if area_options:
        area_target = st.selectbox("Seleziona Area di Appartenenza", options=area_options)
    else:
        # Fallback se non c'è token o errore
        area_target = st.text_input("Nome Area (Manuale)", value="Health and Fitness")
        if token: st.warning("⚠️ Impossibile caricare le aree. Controlla il Token.")

# --- INTERFACCIA PRINCIPALE ---
st.subheader("Blueprint Progetto")

# Esempio JSON pulito (senza Epic hardcodate, come richiesto)
example_json = [
    {
        "title": "Nuovo Progetto",
        "tasks": [
            {"title": "1.1 Ricerca iniziale", "epic": "1. Discovery"},
            {"title": "2.1 Sviluppo MVP", "epic": "2. Build"}
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
                
                # Crea Progetto usando l'Area selezionata dal menu
                proj_id = manager.create_project(p_title, area_name=area_target)
                st.success(f"✅ Progetto creato: **{p_title}** in *{area_target}*")
                
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
            
            # Pulisce la cache per forzare un refresh al prossimo giro (opzionale)
            st.cache_data.clear()

        except json.JSONDecodeError:
            st.error("❌ JSON non valido.")
        except Exception as e:
            st.error(f"❌ Errore: {str(e)}")
