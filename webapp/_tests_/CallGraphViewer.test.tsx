import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { toPng } from "html-to-image";
import CallGraphViewer from "../components/CallGraphViewer";
import type { CallGraphData } from "../types/types";

jest.mock("html-to-image", () => ({
  toPng: jest.fn(),
}));

jest.mock("reactflow", () => {
  const ReactModule = jest.requireActual("react") as typeof React;

  return {
    __esModule: true,
    default: ({ nodes, edges, onNodeClick, children }: any) => (
      <div data-testid="react-flow">
        {nodes.map((node: any) => (
          <button
            key={node.id}
            type="button"
            style={node.style}
            data-testid={`node-${node.id}`}
            data-selected={String(Boolean(node.selected))}
            onClick={(event) => onNodeClick(event, node)}
          >
            {node.data.label}
          </button>
        ))}
        {edges.map((edge: any) => (
          <span
            key={edge.id}
            data-testid={`edge-${edge.id}`}
            data-stroke={edge.style?.stroke}
          />
        ))}
        {children}
      </div>
    ),
    MiniMap: () => <div data-testid="minimap" />,
    Controls: () => <div data-testid="controls" />,
    Background: () => <div data-testid="background" />,
    MarkerType: { ArrowClosed: "arrow-closed" },
    useNodesState: (initialNodes: any[]) => {
      const [nodes, setNodes] = ReactModule.useState(initialNodes);
      return [nodes, setNodes, jest.fn()];
    },
    useEdgesState: (initialEdges: any[]) => {
      const [edges, setEdges] = ReactModule.useState(initialEdges);
      return [edges, setEdges, jest.fn()];
    },
  };
});

const graphData: CallGraphData = {
  nodes: [
    {
      id: "module.py:smelly_function",
      label: "smelly_function",
      file: "module.py",
      is_smelly: true,
      calls_smelly: false,
      smells: [{
        function_name: "smelly_function",
        line: 12,
        smell_name: "long_method",
        description: "Method is too long",
        additional_info: "",
      }],
    },
    {
      id: "main.py:caller",
      label: "caller",
      file: "main.py",
      is_smelly: false,
      calls_smelly: true,
      smells: [],
    },
    {
      id: "clean.py:helper",
      label: "helper",
      file: "clean.py",
      is_smelly: false,
      calls_smelly: false,
      smells: [],
    },
  ],
  edges: [
    { source: "main.py:caller", target: "module.py:smelly_function" },
  ],
};

describe("CallGraphViewer", () => {
  let anchorClick: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    anchorClick = jest
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    (toPng as jest.Mock).mockResolvedValue("data:image/png;base64,test");
  });

  afterEach(() => {
    anchorClick.mockRestore();
  });

  it("uses the CR4 colors for smelly, dependent and clean nodes", () => {
    render(<CallGraphViewer graphData={graphData} />);

    expect(screen.getByTestId("node-module.py:smelly_function")).toHaveStyle({
      background: "#fee2e2",
      border: "2px solid #ef4444",
    });
    expect(screen.getByTestId("node-main.py:caller")).toHaveStyle({
      background: "#ffedd5",
      border: "2px solid #f97316",
    });
    expect(screen.getByTestId("node-clean.py:helper")).toHaveStyle({
      background: "#dcfce7",
      border: "2px solid #22c55e",
    });
  });

  it("filters node categories and removes edges with hidden endpoints", async () => {
    render(<CallGraphViewer graphData={graphData} />);

    fireEvent.click(screen.getByRole("checkbox", { name: /Nodi Smelly/ }));

    await waitFor(() => {
      expect(screen.queryByTestId("node-module.py:smelly_function")).not.toBeInTheDocument();
      expect(screen.queryByTestId(/edge-/)).not.toBeInTheDocument();
    });
    expect(screen.getByTestId("node-main.py:caller")).toBeInTheDocument();
    expect(screen.getByTestId("node-clean.py:helper")).toBeInTheDocument();
  });

  it("highlights the selected node and connected edge and fills the sidebar", async () => {
    render(<CallGraphViewer graphData={graphData} />);

    fireEvent.click(screen.getByTestId("node-module.py:smelly_function"));

    await waitFor(() => {
      expect(screen.getByTestId("node-module.py:smelly_function")).toHaveAttribute(
        "data-selected",
        "true",
      );
      expect(screen.getByTestId(/edge-/)).toHaveAttribute("data-stroke", "#2563eb");
    });
    expect(screen.getByText("ID:").parentElement).toHaveTextContent("module.py:smelly_function");
    expect(screen.getByText("File:").parentElement).toHaveTextContent("module.py");
    expect(screen.getByText("long_method")).toBeInTheDocument();
    expect(screen.getByText("Method is too long")).toBeInTheDocument();
  });

  it("exports the graph as JSON and PNG", async () => {
    render(<CallGraphViewer graphData={graphData} />);

    fireEvent.click(screen.getByRole("button", { name: /Export JSON/ }));
    expect(anchorClick).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: /Export PNG/ }));
    await waitFor(() => {
      expect(toPng).toHaveBeenCalledTimes(1);
      expect(anchorClick).toHaveBeenCalledTimes(2);
    });
  });
});
