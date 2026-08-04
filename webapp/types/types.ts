export type ContextSmell = {
  function_name: string;
  line: number;
  smell_name: string;
  description: string;
  additional_info: string;
};

export type DetectResponse = {
    success: boolean;
    smells: ContextSmell[];
}

export type GenerateReportResponse = {
    report_data: Record<string, any>;
}

export type ChartData = { 
  smell_name: string;
  filename: string 
};

export type CallGraphNode = {
  id: string;
  label: string;
  file?: string;
  is_smelly?: boolean;
  calls_smelly?: boolean;
  smells?: ContextSmell[];
};

export type CallGraphEdge = {
  source: string;
  target: string;
};

export type CallGraphData = {
  nodes: CallGraphNode[];
  edges: CallGraphEdge[];
};

export type ProjectData = {
  files: string[] | null;
  message: string;
  result: string | null;
  smells: ContextSmell[] | null;
  graphData?: CallGraphData | null;
  smellyFunctions?: ContextSmell[];
};

export type ProjectType = {
  name: string;
  files: File[] | null;
  data: ProjectData;
  isLoading: boolean;
};

export type ProjectContextType = {
  projects: ProjectType[];
  addProject: () => void;
  updateProject: (index: number, project: Partial<ProjectType>) => void;
  removeProject: (index: number) => void;
};
