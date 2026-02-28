"use client";

import React from "react";
import { motion } from "framer-motion";
import { useProjectContext } from "../../context/ProjectContext";
import FileInput from "./FileInput";
import CallGraphViewer from "./CallGraphViewer"; // <-- Importiamo il visualizzatore del grafo

type ProjectProps = {
  index: number;
};

const Project: React.FC<ProjectProps> = ({ index }) => {
  const { projects, updateProject, removeProject } = useProjectContext();
  const project = projects[index];

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(
      (file) => file.name.endsWith(".py") && file.name !== "__init__.py"
    );
    if (files.length > 0) {
      const folderName = files[0].webkitRelativePath.split("/")[0];
      updateProject(index, { files, name: folderName });
    }
  };

  return (
    <motion.div
      className="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-200 transition-transform hover:scale-105"
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      <h2 className="text-2xl font-semibold text-blue-700 mb-4">
        {project?.name || `Project ${index + 1}`}
      </h2>

      {/* Componente di Input dei File */}
      <FileInput onChange={handleFolderChange} />

      {/* Lista dei file caricati */}
      {project.files && (
        <motion.ul className="mt-2 text-sm text-gray-600 max-h-32 overflow-y-auto">
          {project.files.map((file) => (
            <motion.li key={file.name} className="hover:text-blue-600">
              📄 {file.name}
            </motion.li>
          ))}
        </motion.ul>
      )}

      {/* Bottone Rimuovi */}
      <motion.button
        onClick={() => removeProject(index)}
        className="w-full bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg font-semibold hover:bg-red-700 mt-4"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        🗑️ Remove Project
      </motion.button>

      {/* Messaggio di stato dell'analisi */}
      {project.data?.message && (
        <p className={`mt-6 text-center font-medium text-lg ${
            project.data.message.includes("Error") || project.data.message.includes("failed") ? "text-red-500"
              : project.data.message.includes("Analyzing") ? "text-blue-500 animate-pulse" : "text-green-600"
          }`}>
          {project.data.message}
        </p>
      )}

      {/* Visualizzazione Call Graph (CR4) */}
      {project.data?.graphData && (
        <motion.div 
          className="mt-8 border-t pt-6"
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }} 
          transition={{ duration: 0.5 }}
        >
          <h3 className="text-xl font-bold text-gray-800 mb-4">Call Graph Visualization</h3>
          <CallGraphViewer 
            graphData={project.data.graphData} 
            smellyFunctions={project.data.smellyFunctions || []} 
          />
        </motion.div>
      )}

    </motion.div>
  );
};

export default Project;