"use client";

import React, { useRef, useEffect } from "react";
import { useProjectContext } from "../context/ProjectContext";
import { motion } from "framer-motion";
import CallGraphViewer from "./CallGraphViewer"; 

type ProjectProps = {
  index: number;
};

const Project: React.FC<ProjectProps> = ({ index }) => {
  const { projects, updateProject, removeProject } = useProjectContext();
  const project = projects[index];
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (fileInputRef.current) {
      (fileInputRef.current as HTMLInputElement).webkitdirectory = true;
    }
  }, []);

  const handleFolderChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    const files = fileList ? Array.from(fileList) : [];
    const filteredFiles = files.filter(
      (file) => file.name.endsWith(".py") && file.name !== "__init__.py"
    );

    if (filteredFiles.length > 0) {
      const folderName = filteredFiles[0].webkitRelativePath.split("/")[0];
      updateProject(index, {
        files: filteredFiles,
        name: folderName,
        data: null 
      });
    }
  };

  return (
    <motion.div
      className="bg-white rounded-2xl shadow-lg p-6 mb-8 border border-gray-200 transition-transform hover:scale-105"
      whileHover={{ scale: 1.01 }}
    >
      <h2 className="text-2xl font-semibold text-blue-700 mb-4">
        {project?.name || `Project ${index + 1}`}
      </h2>

      {/* File Input */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFolderChange}
        className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg mb-4 cursor-pointer hover:bg-gray-100 transition-all duration-300"
        multiple
        data-testid="file-input"
      />

      {/* Display Files */}
      {project.files && project.files.length > 0 && (
        <motion.ul
          className="mt-2 mb-4 text-sm text-gray-600 max-h-32 overflow-y-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {Array.from(project.files).map((file) => (
            <li key={file.name} className="hover:text-blue-600">
              📄 {file.name}
            </li>
          ))}
        </motion.ul>
      )}

      {/* Solo Bottone Rimuovi Originale */}
      <button
        id="removeButton"
        onClick={() => removeProject(index)}
        className="w-full bg-red-600 text-white py-3 rounded-lg shadow-lg font-semibold hover:bg-red-700 transition-all"
      >
        🗑️ Remove Project
      </button>

      {/* Messaggio di stato che verrà aggiornato dal bottone grande */}
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
        <div className="mt-8 border-t pt-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Call Graph Visualization</h3>
          <CallGraphViewer 
            graphData={project.data.graphData} 
            smellyFunctions={project.data.smellyFunctions} 
          />
        </div>
      )}
    </motion.div>
  );
};

export default Project;