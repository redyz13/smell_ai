import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    specPattern: [
      "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",    // End-to-End tests
      "cypress/integration/**/*.cy.{js,jsx,ts,tsx}" // Integration tests
    ],
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
    // --- AGGIUNTE PER OTTIMIZZARE LA MEMORIA ---
    // Forza la Garbage Collection tra un test e l'altro per prevenire crash
    experimentalMemoryManagement: true,
    // Evita di conservare gli snapshot della UI nella RAM
    numTestsKeptInMemory: 0,
  },

  component: {
    devServer: {
      framework: "next",
      bundler: "webpack",
    },
  },
});