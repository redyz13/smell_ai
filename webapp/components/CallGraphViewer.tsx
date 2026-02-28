"use client";

import React, { useState, useMemo, useCallback, useRef } from "react";
import ReactFlow, { 
  MiniMap, Controls, Background, MarkerType, useNodesState, useEdgesState 
} from "reactflow";
import "reactflow/dist/style.css";
import { toPng } from "html-to-image";

type CallGraphViewerProps = {
  graphData: {
    nodes: Array<{ 
        id: string; 
        label: string; 
        file?: string;
        is_smelly?: boolean; 
        calls_smelly?: boolean;
        smells?: any[];
    }>;
    edges: Array<{ source: string; target: string }>;
  };
  smellyFunctions: Array<{ function_name: string; smell_name: string; [key: string]: any }>;
};

const CallGraphViewer: React.FC<CallGraphViewerProps> = ({ graphData }) => {
  const reactFlowRef = useRef<HTMLDivElement>(null);
  
  // State per i filtri
  const [showSmelly, setShowSmelly] = useState(true);
  const [showClean, setShowClean] = useState(true);
  const [showDependent, setShowDependent] = useState(true);
  
  // State per il nodo selezionato (Sidebar)
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

  // Generiamo i nodi per React Flow usando i flag `is_smelly` e `calls_smelly` del backend!
  const initialNodes = useMemo(() => {
    return graphData.nodes
      .filter(node => {
        const isSmelly = node.is_smelly;
        const isDependent = node.calls_smelly && !isSmelly;
        const isClean = !isSmelly && !isDependent;

        if (isSmelly && !showSmelly) return false;
        if (isDependent && !showDependent) return false;
        if (isClean && !showClean) return false;
        return true;
      })
      .map((node, index) => {
        const isSmelly = node.is_smelly;
        const isDependent = node.calls_smelly && !isSmelly;
        
        // Logica Colori: CR4
        const bgColor = isSmelly ? "#fee2e2" : (isDependent ? "#ffedd5" : "#dcfce7");
        const borderColor = isSmelly ? "#ef4444" : (isDependent ? "#f97316" : "#22c55e");

        return {
          id: node.id,
          position: { x: (index % 3) * 200, y: Math.floor(index / 3) * 150 }, // Layout basilare a griglia
          data: { 
            label: node.label, 
            file: node.file,
            smells: node.smells || [] // Passiamo gli smells associati direttamente dal backend
          },
          style: {
            background: bgColor,
            border: `2px solid ${borderColor}`,
            borderRadius: "8px",
            padding: "10px",
            fontWeight: "bold",
            color: "#333"
          }
        };
      });
  }, [graphData.nodes, showSmelly, showClean, showDependent]);

  const initialEdges = useMemo(() => {
    return graphData.edges.map((edge, index) => ({
      id: `e${index}-${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      animated: true,
      style: { stroke: selectedNode?.id === edge.source || selectedNode?.id === edge.target ? '#2563eb' : '#9ca3af', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#9ca3af' },
    }));
  }, [graphData.edges, selectedNode]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Aggiorna nodi/archi se cambiano i filtri
  React.useEffect(() => { setNodes(initialNodes); }, [initialNodes, setNodes]);
  React.useEffect(() => { setEdges(initialEdges); }, [initialEdges, setEdges]);

  // Gestione Sidebar: leggiamo gli smells da `node.data.smells`
  const onNodeClick = useCallback((event: React.MouseEvent, node: any) => {
    setSelectedNode(node);
  }, []);

  // Esportazione JSON
  const downloadJSON = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(graphData, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "call_graph.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  // Esportazione Immagine
  const downloadImage = () => {
    if (reactFlowRef.current === null) return;
    toPng(reactFlowRef.current, { backgroundColor: '#ffffff' })
      .then((dataUrl) => {
        const link = document.createElement('a');
        link.download = 'call_graph.png';
        link.href = dataUrl;
        link.click();
      });
  };

  return (
    <div className="flex flex-col md:flex-row gap-4 h-[600px] w-full border rounded-lg bg-gray-50 overflow-hidden">
      
      {/* AREA GRAFO */}
      <div className="flex-grow relative h-full" ref={reactFlowRef}>
        <div className="absolute top-2 left-2 z-10 bg-white p-2 rounded shadow flex flex-col gap-2 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={showSmelly} onChange={(e) => setShowSmelly(e.target.checked)} /> Nodi Smelly (Rosso)</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={showDependent} onChange={(e) => setShowDependent(e.target.checked)} /> Dipendenti (Arancione)</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={showClean} onChange={(e) => setShowClean(e.target.checked)} /> Clean (Verde)</label>
          <hr />
          <button onClick={downloadJSON} className="text-blue-600 text-left hover:underline">📥 Export JSON</button>
          <button onClick={downloadImage} className="text-blue-600 text-left hover:underline">🖼️ Export PNG</button>
        </div>

        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onNodeClick={onNodeClick} fitView>
          <MiniMap nodeStrokeColor={(n) => {
              if (n.style?.background === '#fee2e2') return '#ef4444';
              if (n.style?.background === '#ffedd5') return '#f97316';
              return '#22c55e';
            }} nodeColor={(n) => n.style?.background as string} />
          <Controls />
          <Background color="#aaa" gap={16} />
        </ReactFlow>
      </div>

      {/* SIDEBAR SELEZIONE */}
      <div className="w-full md:w-1/3 bg-white p-4 border-l overflow-y-auto">
        <h3 className="text-lg font-bold mb-4 border-b pb-2">Dettagli Nodo</h3>
        {selectedNode ? (
          <div>
            <p><strong>ID:</strong> {selectedNode.id}</p>
            <p><strong>File:</strong> {selectedNode.data.file || "N/A"}</p>
            
            <div className="mt-4">
              <h4 className="font-semibold text-red-600 mb-2">Smells Rilevati ({selectedNode.data.smells?.length || 0}):</h4>
              {selectedNode.data.smells && selectedNode.data.smells.length > 0 ? (
                <ul className="list-disc pl-5 space-y-2 text-sm">
                  {selectedNode.data.smells.map((s: any, i: number) => (
                    <li key={i}>
                      <span className="font-medium">{s.smell_name}</span> (Linea {s.line})<br/>
                      <span className="text-gray-500">{s.description}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-green-600">Nessuno smell rilevato su questo nodo.</p>
              )}
            </div>
          </div>
        ) : (
          <p className="text-gray-500 italic">Clicca su un nodo nel grafo per visualizzare i dettagli.</p>
        )}
      </div>

    </div>
  );
};

export default CallGraphViewer;