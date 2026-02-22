import os
import tempfile
import pandas as pd
from components.inspector import Inspector
from components.call_graph_builder import CallGraphBuilder

def detect_static(code_snippet: str) -> dict:
    temp_file_path = None
    try:
        # Creazione file con codifica UTF-8 per evitare errori di decodifica
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8") as temp_file:
            temp_file.write(code_snippet)
            temp_file_path = temp_file.name

        # 1. Analisi Smell (Rossi)
        inspector = Inspector(output_path="output")
        smells_df = inspector.inspect(temp_file_path)
        smells = smells_df.to_dict('records') if not smells_df.empty else []

        # 2. Estrazione Grafo Completo (Tutti i nodi, anche i verdi)
        builder = CallGraphBuilder()
        builder.analyze_file(temp_file_path)
        graph_data = builder.get_graph_data()

        # Restituiamo tutto nella chiave "response" per non rompere il Gateway
        return {
            "success": True,
            "response": {
                "smells": smells,
                "callgraph": graph_data
            }
        }
    except Exception as e:
        return {"success": False, "response": str(e)}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)