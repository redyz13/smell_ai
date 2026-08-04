import 'cypress-file-upload';
Cypress.config('defaultCommandTimeout', 10000);

describe('Upload Project Page', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3000/upload-project');
  });

  it('should load the upload-project page correctly', () => {
    cy.contains('Upload and Analyze Projects');
  });

  it('should allow the user to select an analysis mode', () => {
    cy.contains('AI-Based').click();
    cy.contains('Static Tool').click();
  });

  it('should allow the user to cancel the upload', () => {
    cy.contains('Static Tool').click();
    cy.contains('Add Project').click();
    const file1 = "model_training_and_evaluation/model.py"

    cy.fixture(file1, 'utf8').then((fileContent) => {
      cy.get('[data-testid="file-input"]').attachFile({
        fileContent,
        fileName: "model.py",
        mimeType: 'text/x-python',
      });
    });

    cy.get('#removeButton').click();
  });

  it('should allow the user to add a project and view analysis result', () => {
    cy.contains('Static Tool').click();

    const file1 = 'model_training_and_evaluation/model.py';
    const file2 = 'model_training_and_evaluation/dataset_preparation.py';

    cy.intercept('POST', '**/api/detect_smell_*').as('analyzeCall');
    cy.contains('Add Project').click();

    cy.fixture(file1, 'utf8').then((fileContent1) => {
      cy.fixture(file2, 'utf8').then((fileContent2) => {
        cy.get('[data-testid="file-input"]').attachFile([
          { fileContent: fileContent1, fileName: "model.py", mimeType: 'text/x-python' },
          { fileContent: fileContent2, fileName: "dataset_preparation.py", mimeType: 'text/x-python' },
        ]);
      });
    });

    cy.contains('Upload and Analyze All Projects').click();
    cy.wait('@analyzeCall', { timeout: 30000 }).its('response.statusCode').should('eq', 200);
    cy.contains('Upload and Analyze All Projects').should('not.be.disabled');
  });

  it('should display and interact with the Call Graph visualization', () => {
    cy.contains('Static Tool').click();

    cy.intercept('POST', '**/api/detect_smell_*', {
      statusCode: 200,
      body: {
        success: true,
        smells: [
          {
            function_name: "clean_data",
            line: 13,
            smell_name: "empty_column_misinitialization",
            description: "Column initialized incorrectly",
            additional_info: "",
          }
        ],
        graph_data: {
          nodes: [
            {
              id: "data_processor.py:clean_data",
              label: "clean_data",
              is_smelly: true,
              calls_smelly: false,
              file: "data_processor.py",
              smells: [{
                function_name: "clean_data",
                line: 13,
                smell_name: "empty_column_misinitialization",
                description: "Column initialized incorrectly",
                additional_info: "",
              }],
            },
            { id: "main.py:start", label: "start", is_smelly: false, calls_smelly: true, file: "main.py", smells: [] },
            { id: "helpers.py:normalize", label: "normalize", is_smelly: false, calls_smelly: false, file: "helpers.py", smells: [] }
          ],
          edges: [
            { source: "main.py:start", target: "data_processor.py:clean_data" }
          ]
        }
      }
    }).as('analyzeCallGraph');

    cy.contains('Add Project').click();
    const file1 = 'model_training_and_evaluation/model.py';
    
    cy.fixture(file1, 'utf8').then((fileContent) => {
      cy.get('[data-testid="file-input"]').attachFile({
        fileContent, fileName: "model.py", mimeType: 'text/x-python'
      });
    });

    cy.contains('Upload and Analyze All Projects').click();
    cy.wait('@analyzeCallGraph', { timeout: 30000 });

    cy.contains('Call Graph Visualization').should('be.visible');
    cy.get('.react-flow').should('be.visible'); 
    cy.contains('View Analysis Results').click();
    cy.get('pre').should('contain.text', 'clean_data');

    cy.contains('Nodi Smelly (Rosso)').should('be.visible');
    cy.contains('Dipendenti (Arancione)').should('be.visible');
    cy.contains('Clean (Verde)').should('be.visible');

    cy.contains('.react-flow__node', 'clean_data')
      .should('have.css', 'background-color', 'rgb(254, 226, 226)');
    cy.contains('.react-flow__node', 'start')
      .should('have.css', 'background-color', 'rgb(255, 237, 213)');
    cy.contains('.react-flow__node', 'normalize')
      .should('have.css', 'background-color', 'rgb(220, 252, 231)');

    cy.contains('label', 'Nodi Smelly (Rosso)').find('input').uncheck();
    cy.contains('.react-flow__node', 'clean_data').should('not.exist');
    cy.contains('label', 'Nodi Smelly (Rosso)').find('input').check();

    cy.contains('.react-flow__node', 'clean_data').click({ force: true })
      .should('have.css', 'box-shadow')
      .and('contain', 'rgb(37, 99, 235)');
    
    cy.contains('Dettagli Nodo').should('be.visible');
    cy.contains('data_processor.py:clean_data').should('be.visible');
    cy.contains('data_processor.py').should('be.visible');
    cy.contains('empty_column_misinitialization').should('be.visible');
    cy.contains('Column initialized incorrectly').should('be.visible');

    cy.contains('Export JSON').should('be.visible');
    cy.contains('Export PNG').should('be.visible');
  });

  // The external AI service is explicitly outside the ISTA test scope.
  it.skip('should allow the user to add a project and view analysis result (ai)', () => {
    cy.contains('AI-Based').click();

    const file1 = 'model_training_and_evaluation/model.py';
    const file2 = 'model_training_and_evaluation/dataset_preparation.py';

    cy.intercept('POST', '**/api/detect_smell_*').as('analyzeCall');
    cy.contains('Add Project').click();

    cy.fixture(file1, 'utf8').then((fileContent1) => {
      cy.fixture(file2, 'utf8').then((fileContent2) => {
        cy.get('[data-testid="file-input"]').attachFile([
          { fileContent: fileContent1, fileName: "model.py", mimeType: 'text/x-python' },
          { fileContent: fileContent2, fileName: "dataset_preparation.py", mimeType: 'text/x-python' },
        ]);
      });
    });

    cy.contains('Upload and Analyze All Projects').click();
    cy.wait('@analyzeCall', { timeout: 30000 });
  });

  it('should handle API failure gracefully', () => {
    cy.contains('Static Tool').click();
    
    cy.intercept('POST', '**/api/detect_smell_*', {
      statusCode: 500,
      body: { error: 'Internal Server Error' },
    }).as('apiFailure');

    cy.contains('Add Project').click();

    const validFile = {
      fileName: 'valid.py',
      fileContent: new Blob(['print("hello world")'], { type: 'text/x-python' }),
      mimeType: 'text/x-python',
    };

    cy.get('[data-testid="file-input"]').attachFile(validFile);
    cy.contains('Upload and Analyze All Projects').click();

    cy.wait('@apiFailure').its('response.statusCode').should('eq', 500);
    cy.contains(/error|failed/i, { timeout: 10000 }).should('be.visible');
  });
});
