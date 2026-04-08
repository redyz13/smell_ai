import { ProjectType } from '@/types/types';
import 'cypress-file-upload';

Cypress.config('defaultCommandTimeout', 10000);

declare global {
    namespace Cypress {
        interface CustomWindow extends Window {
            __REACT_CONTEXT__?: {
                projects: ProjectType[];
                addProject: () => void;
                updateProject: (index: number, project: Partial<ProjectType>) => void;
                removeProject: (index: number) => void;
            };
        }
    }
}

describe('Report Generator Page (E2E)', () => {
    it('should display header, footer, and essential components', () => {
        cy.visit('http://localhost:3000/reports');
        cy.get('header').should('exist');
        cy.get('footer').should('exist');
        cy.contains('Total Projects Available').should('exist');
        cy.get('button').contains('Generate Report').should('exist');
    });

    it('should display an alert when no projects are available', () => {
        cy.visit('http://localhost:3000/reports');
        cy.get('button').contains('Generate Report').click();
        cy.on('window:alert', (text: any) => {
            expect(text).to.equal('No projects available. Please add projects before generating reports.');
        });
        cy.get('#chart-div').should('not.exist');
    });

    it('should generate a report and display chart, allow to download it as pdf', () => {
        cy.visit('http://localhost:3000/reports');
        cy.window().should('have.property', '__REACT_CONTEXT__').and('not.be.undefined');
    
        cy.window().then((win: Cypress.CustomWindow) => {
            const context = win.__REACT_CONTEXT__;
            if (context) {
                context.addProject();
                context.updateProject(0, {
                    name: "model_training_and_evaluation",
                    files: [],
                    data: {
                        files: ["model.py", "dataset_preparation.py"],
                        message: "Projects successfully analyzed!",
                        result: null,
                        smells: [{
                            "function_name": "function",
                            "line": 5,
                            "smell_name": "Unnecessary DataFrame Operation",
                            "description": "Avoid unnecessary operations on DataFrames.",
                            "additional_info": "Consider simplifying the operation.",
                        }],
                    },
                });
            }
        });

        cy.contains('Total Projects Available: 1', { timeout: 15000 }).should('exist');
        cy.intercept('POST', '**/api/generate_report*').as('generateReport');
        cy.contains('Generate Report').click();
        cy.wait('@generateReport', { timeout: 15000 }).its('response.statusCode').should('eq', 200);
        cy.get('#chart-div', { timeout: 10000 }).should('exist');
        cy.contains('Smell Occurrences for All Projects').should('exist');
        cy.contains('Download Report as PDF').click();
    });

    it('should handle API error gracefully', () => {
        cy.visit('http://localhost:3000/reports');
        cy.window().should('have.property', '__REACT_CONTEXT__').and('not.be.undefined');
        cy.window().then((win: Cypress.CustomWindow) => {
            const context = win.__REACT_CONTEXT__;
            if (context) {
                context.addProject();
                context.updateProject(0, {
                    name: "model_training_and_evaluation",
                    files: [],
                    data: {
                        files: ["model.py"],
                        message: "Projects successfully analyzed!",
                        result: null,
                        smells: [{
                            "function_name": "function",
                            "line": 5,
                            "smell_name": "Unnecessary DataFrame Operation",
                            "description": "Avoid unnecessary operations on DataFrames.",
                            "additional_info": "Consider simplifying the operation.",
                        }],
                    },
                });
            }
        });

        cy.contains('Total Projects Available: 1', { timeout: 15000 }).should('exist');
        cy.intercept('POST', '**/api/generate_report*', { statusCode: 500, body: { error: 'Internal Server Error' } }).as('apiFailure');
        cy.contains('Generate Report').click();
        cy.wait('@apiFailure', { timeout: 10000 });
        cy.get('#chart-div').should('not.exist');
        cy.contains(/error/i, { timeout: 10000 }).should('be.visible');
    });

    it('should handle empty smell data gracefully', () => {
        cy.visit('http://localhost:3000/reports');
        cy.window().should('have.property', '__REACT_CONTEXT__').and('not.be.undefined');
        cy.window().then((win: Cypress.CustomWindow) => {
            const context = win.__REACT_CONTEXT__;
            if (context) {
                context.addProject();
                context.updateProject(0, {
                    name: "Project with no smell Data",
                    files: [],
                    data: {
                        files: [],
                        message: "empty project",
                        result: null,
                        smells: null, 
                    },
                });
            }
        });

        cy.contains('Generate Report').click();
        cy.get('#chart-div').should('not.exist');
        cy.contains('No smell data to display.').should('exist');
    });
});