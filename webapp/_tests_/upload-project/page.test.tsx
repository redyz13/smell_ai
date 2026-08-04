import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ProjectContext } from "../../context/ProjectContext";
import UploadProjectPage from "../../app/upload-project/page";
import { detectAi, detectStatic } from "../../utils/api";
import { act } from "react";

// Mocking API calls and typing them
jest.mock("../../utils/api", () => ({
  detectAi: jest.fn() as jest.Mock,
  detectStatic: jest.fn() as jest.Mock,
}));

const Wrapper = ({ children }: { children: React.ReactNode }) => (
  <ProjectContext.Provider value={{
    projects: [],
    addProject: jest.fn(),
    updateProject: jest.fn(),
    removeProject: jest.fn(),
  }}>
    {children}
  </ProjectContext.Provider>
);

describe("UploadProjectPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the page correctly", () => {
    render(<UploadProjectPage />, { wrapper: Wrapper });
    expect(screen.getByText(/Upload and Analyze Projects/)).toBeInTheDocument();
    expect(screen.getByText(/Select Analysis Mode:/)).toBeInTheDocument();
  });

  
it("toggles analysis mode between AI and Static", () => {
    render(<UploadProjectPage />, { wrapper: Wrapper });

    const aiButton = screen.getByText("AI-Based");
    const staticButton = screen.getByText("Static Tool");

    // 1. Verifichiamo il nuovo stato iniziale: Static è attivo (blu), AI è inattivo (grigio)
    expect(staticButton).toHaveClass("bg-blue-600");
    expect(aiButton).toHaveClass("bg-gray-200");

    // 2. Clicchiamo su AI e verifichiamo che si attivi (rosso) e Static si disattivi
    fireEvent.click(aiButton);
    expect(aiButton).toHaveClass("bg-red-600");
    expect(staticButton).toHaveClass("bg-gray-200");

    // 3. Clicchiamo di nuovo su Static per tornare allo stato precedente
    fireEvent.click(staticButton);
    expect(staticButton).toHaveClass("bg-blue-600");
    expect(aiButton).toHaveClass("bg-gray-200");
  });

  it("calls addProject when the Add Project button is clicked", async () => {
    const mockAddProject = jest.fn();
    const mockUpdateProject = jest.fn();

    render(<UploadProjectPage />, {
      wrapper: ({ children }) => (
        <ProjectContext.Provider value={{
          projects: [],
          addProject: mockAddProject,
          updateProject: mockUpdateProject,
          removeProject: jest.fn(),
        }}>
          {children}
        </ProjectContext.Provider>
      ),
    });

    const addProjectButton = screen.getByText("Add Project");
    fireEvent.click(addProjectButton);

    await waitFor(() => expect(mockAddProject).toHaveBeenCalledTimes(1));
  });

  it("calls handleSubmitAll and updates project state when submitting projects", async () => {
    const mockUpdateProject = jest.fn();

    // Mock API responses for AI and Static analysis
    (detectAi as jest.Mock).mockResolvedValue({
      smells: [{ function_name: "main", line: 1, smell_name: "Code Smell", description: "Unoptimized code" }],
    });
    (detectStatic as jest.Mock).mockResolvedValue({ smells: [] });

    render(<UploadProjectPage />, {
      wrapper: ({ children }) => (
        <ProjectContext.Provider value={{
          projects: [{ 
            name: "mockproject",
            files: [], 
            data: { 
              files: [],
              message: "", 
              result: null,
              smells: [],
            }, 
            isLoading: false 
          }],
          addProject: jest.fn(),
          updateProject: mockUpdateProject,
          removeProject: jest.fn(),
        }}>
          {children}
        </ProjectContext.Provider>
      ),
    });

    const submitButton = screen.getByText("Upload and Analyze All Projects");
    fireEvent.click(submitButton);

    await waitFor(() => expect(mockUpdateProject).toHaveBeenCalledTimes(2));
  });

  it("preserves webkitRelativePath in the static-analysis payload", async () => {
    const mockUpdateProject = jest.fn();
    const file = new File(["def run(): pass"], "module.py", { type: "text/x-python" });
    Object.defineProperty(file, "webkitRelativePath", {
      value: "sample_project/pkg/module.py",
    });
    Object.defineProperty(file, "text", {
      value: jest.fn().mockResolvedValue("def run(): pass"),
    });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        success: true,
        smells: [],
        graph_data: { nodes: [], edges: [] },
      }),
    }) as jest.Mock;

    render(<UploadProjectPage />, {
      wrapper: ({ children }) => (
        <ProjectContext.Provider value={{
          projects: [{
            name: "sample_project",
            files: [file],
            data: { files: null, message: "", result: null, smells: [] },
            isLoading: false,
          }],
          addProject: jest.fn(),
          updateProject: mockUpdateProject,
          removeProject: jest.fn(),
        }}>
          {children}
        </ProjectContext.Provider>
      ),
    });

    fireEvent.click(screen.getByText("Upload and Analyze All Projects"));

    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));
    const request = (global.fetch as jest.Mock).mock.calls[0][1];
    expect(JSON.parse(request.body)).toEqual({
      files: [{
        filename: "sample_project/pkg/module.py",
        content: "def run(): pass",
      }],
    });
    await waitFor(() => {
      expect(mockUpdateProject).toHaveBeenLastCalledWith(0, expect.objectContaining({
        isLoading: false,
        data: expect.objectContaining({ files: ["sample_project/pkg/module.py"] }),
      }));
    });
  });

  it("disables the submit button when projects are loading", async () => {

    const { rerender } = render(<UploadProjectPage />, {
      wrapper: ({ children }) => (
        <ProjectContext.Provider value={{
          projects: [{
            name: "mockproject",
            files: [],
            data: { files: null, message: "", result: null, smells: [] },
            isLoading: false
          }],
          addProject: jest.fn(),
          updateProject: jest.fn(),
          removeProject: jest.fn(),
        }}>
          {children}
        </ProjectContext.Provider>
      ),
    });

    const submitButton = screen.getByText("Upload and Analyze All Projects");
    expect(submitButton).not.toBeDisabled();

    act(() => {
      render(<UploadProjectPage />, {
        wrapper: ({ children }) => (
          <ProjectContext.Provider value={{
            projects: [{
              name: "mockproject",
              files: [],
              data: { files: null, message: "", result: null, smells: [] },
              isLoading: true 
            }],
            addProject: jest.fn(),
            updateProject: jest.fn(),
            removeProject: jest.fn(),
          }}>
            {children}
          </ProjectContext.Provider>
        ),
      });
    });

    const updatedButton = await screen.findByText("Analyzing Projects...");
    expect(updatedButton).toBeDisabled();
  });



  it("disables the submit button when there are no projects", () => {
    render(<UploadProjectPage />, { wrapper: Wrapper });

    const submitButton = screen.getByText("Upload and Analyze All Projects");
    expect(submitButton).toBeDisabled();
  });
});
