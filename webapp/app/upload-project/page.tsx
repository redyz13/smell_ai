"use client";
import { useState } from "react";
import Header from "../../components/HeaderComponent";
import Footer from "../../components/FooterComponent";
import Project from "../../components/ProjectComponent"; // <-- Usa ProjectComponent che contiene il Call Graph
import { useProjectContext } from "../../context/ProjectContext";
import { motion } from "framer-motion";
import AnalysisModeToggle from "../../components/AnalysisModeToggle";
import Button from "../../components/Button"; 
import { toast } from "react-toastify";

const UploadProjectPage = () => {
  const { projects, addProject, updateProject } = useProjectContext();
  const [analysisMode, setAnalysisMode] = useState<"AI" | "Static">("Static"); // Mettiamo Static come predefinito per il test

  // Gestione dell'invio di tutta la cartella
  const handleSubmitAll = async () => {
    // 1. Mettiamo tutti i progetti in stato di caricamento visivo
    projects.forEach((_, index) => {
      updateProject(index, {
        isLoading: true,
        data: { 
          message: "Uploading and analyzing the project...",
          result: null,
          smells: [],
          graphData: null // Resettiamo l'eventuale grafo precedente
        },
      });
    });

    try {
      // 2. Analizziamo un progetto per volta
      for (let index = 0; index < projects.length; index++) {
        const project = projects[index];

        // Se non ci sono file, passa al prossimo progetto
        if (!project.files || project.files.length === 0) {
          updateProject(index, {
            isLoading: false,
            data: { message: "Error, no valid files to analyze." },
          });
          continue;
        }

        // Estrapoliamo solo i file .py per l'analisi (ignorando gli altri e __init__.py)
        const pythonFiles = Array.from(project.files).filter(
            (file) => file.name.endsWith(".py") && file.name !== "__init__.py"
        );

        if (pythonFiles.length === 0) {
           updateProject(index, {
            isLoading: false,
            data: { message: "No Python files found in this folder." },
          });
          continue;
        }

        // Prepariamo l'array di file da inviare in un'unica soluzione al server!
        const filesPayload = await Promise.all(
          pythonFiles.map(async (file) => ({
            filename: file.name,
            content: await file.text()
          }))
        );

        // Seleziona l'endpoint
        const endpoint = analysisMode === "Static" 
            ? "http://localhost:8000/api/detect_smell_static"
            : "http://localhost:8000/api/detect_smell_ai";

        // Chiamata API per il progetto corrente
        try {
            const response = await fetch(endpoint, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ files: filesPayload }),
            });

            if (!response.ok) throw new Error("Server responded with an error");

            const data = await response.json();

            // 3. AGGIORNIAMO IL PROGETTO SALVANDO IL GRAPH DATA!
            updateProject(index, {
              isLoading: false,
              data: {
                message: data.success ? "Project successfully analyzed!" : "Analysis failed.",
                result: JSON.stringify(data.smells || data.response, null, 2),
                graphData: data.graph_data || null, // <-- QUESTO FARA' APPARIRE IL GRAFO!
                smellyFunctions: Array.isArray(data.smells) 
                    ? data.smells 
                    : (Array.isArray(data.response) ? data.response : []), 
              },
            });

            if (!data.success) {
                toast.error(`Analysis failed for project ${index + 1}`);
            }

        } catch (fetchError) {
             console.error("Fetch error:", fetchError);
             updateProject(index, {
                isLoading: false,
                data: { message: "Error contacting the analysis server." },
              });
             toast.error(`Connection error on project ${index + 1}`);
        }
      }

    } catch (error) {
      console.error("Global analysis error:", error);
      toast.error("Critical error during project analysis");
      projects.forEach((_, index) => {
        updateProject(index, { isLoading: false });
      });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-blue-100 to-gray-200">
      <Header />

      <main className="flex-grow py-16 bg-gradient-to-b from-purple-50 via-indigo-100 to-gray-50">
        <div className="max-w-4xl mx-auto p-8 bg-white shadow-2xl rounded-3xl border border-gray-200">
          <motion.h1
            className="text-5xl font-extrabold text-blue-700 mb-8 text-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            Upload and Analyze Projects
          </motion.h1>

          <AnalysisModeToggle analysisMode={analysisMode} setAnalysisMode={setAnalysisMode} />

          <Button
            onClick={addProject}
            className="w-full bg-green-600 text-white px-6 py-3 rounded-xl shadow-xl font-semibold hover:bg-green-700 transition-all duration-300 mb-6"
            disabled={false}
          >
            Add Project
          </Button>

          <div className="space-y-6">
            {projects.map((_, index) => (
              <Project key={index} index={index} />
            ))}
          </div>

          <Button
            onClick={handleSubmitAll}
            className="w-full px-6 py-3 rounded-xl shadow-lg bg-blue-600 text-white hover:bg-blue-700 transition-all duration-300 mb-6"
            disabled={projects.some((project) => project.isLoading) || projects.length === 0}
          >
          {projects.some((project) => project.isLoading)
            ? "Analyzing Projects..."
            : "Upload and Analyze All Projects"}
        </Button>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default UploadProjectPage;