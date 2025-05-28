// eslint.config.js
import globals from "globals";
import js from "@eslint/js";

export default [
  js.configs.recommended, // Start with ESLint's recommended rules
  {
    languageOptions: {
      ecmaVersion: 2022, // Allows for the parsing of modern ECMAScript features
      sourceType: "module", // Important: Indicates that the code is in ES6 modules
      globals: {
        ...globals.browser, // Predefined browser global variables
        // Add any custom global variables your project uses here, if any
        bootstrap: "readonly" // Bootstrap 5 global object
        // For now, we primarily need globals.browser
      }
    },
    rules: {
      // You can add custom rules here later if needed,
      // For now, we are focused on fixing parsing errors.
      // Example:
      // "no-unused-vars": "warn",
      // "no-undef": "error" // This is good for catching undefined variable uses
    }
  }
];