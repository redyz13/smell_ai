import os
import sys
import tempfile
import ast
import pandas as pd

# ==========================================
# GESTIONE PATH E IMPORTAZIONI
# ==========================================

# 1. Calcoliamo la root del progetto per trovare la cartella 'call_graph'
# Saliamo di 5 livelli da 'webapp/services/staticanalysis/app/utils' alla root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../"))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Importiamo i moduli del Call Graph dalla root
try:
    from call_graph.call_graph_extractor import CallGraphExtractor
    from call_graph.call_graph_builder import CallGraphBuilder
except ModuleNotFoundError:
    # Fallback d'emergenza
    from call_graph_extractor import CallGraphExtractor
    from call_graph_builder import CallGraphBuilder

# 3. Importiamo le dipendenze interne dell'app
try:
    from webapp.services.staticanalysis.app.schemas.responses import Smell
except ModuleNotFoundError:
    try:
        from app.schemas.responses import Smell
    except ModuleNotFoundError:
        from schemas.responses import Smell

from components.inspector import Inspector

# ==========================================
# INIZIALIZZAZIONE
# ==========================================

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

inspector = Inspector(output_path=OUTPUT_DIR)

# ==========================================
# LOGICA DI ANALISI STATICA E CALL GRAPH
# ==========================================

def detect_static(files: list) -> dict:
    """
    Analizza una lista di file Python, estrae gli smell e genera il Call Graph.
    """
    smells_list = []
    smells_by_node_id = {}
    fragments = []

    try:
        extractor = CallGraphExtractor()

        for file_data in files:
            filename = file_data.get("filename", "snippet.py")
            code_content = file_data.get("content", "")

            temp_file_path = None
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as temp_file:
                temp_file.write(code_content)
                temp_file_path = temp_file.name

            try:
                # 1. Ispezione Code Smells
                smells_df: pd.DataFrame = inspector.inspect(temp_file_path)

                if not smells_df.empty:
                    for _, row in smells_df.iterrows():
                        func_name = row["function_name"]
                        smell = Smell(
                            function_name=func_name,
                            line=row["line"],
                            smell_name=row["smell_name"],
                            description=row["description"],
                            additional_info=row["additional_info"],
                        )
                        smells_list.append(smell)

                        # Mappiamo lo smell al nodo del grafo
                        node_id = f"{filename}:{func_name}"
                        if node_id not in smells_by_node_id:
                            smells_by_node_id[node_id] = []
                        
                        smell_dict = smell.model_dump() if hasattr(smell, 'model_dump') else smell.dict()
                        smells_by_node_id[node_id].append(smell_dict)
            except Exception as inspect_err:
                print(f"Errore ispezione file {filename}: {inspect_err}")
            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except OSError:
                        pass

            try:
                # 2. Generazione frammento AST per il Call Graph
                tree = ast.parse(code_content)
                fragment = extractor.extract(tree, filename)
                fragments.append(fragment)
            except Exception as ast_err:
                print(f"Errore parsing AST per {filename}: {ast_err}")

        # 3. Unione di tutti i frammenti nel Call Graph Globale
        builder = CallGraphBuilder()
        graph_data = builder.build(
            fragments=fragments,
            project_root=".",
            smells_by_node_id=smells_by_node_id
        )

        return {
            "success": True,
            "response": smells_list if smells_list else "Static analysis returned no data",
            "graph_data": graph_data
        }

    except Exception as e:
        return {"success": False, "response": str(e), "graph_data": None}