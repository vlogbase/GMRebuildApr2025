const { exec } = require('child_process');
const express = require('express');
const path = require('path');

// Print information message
console.log('Starting GloriaMundo Test Workflow');
console.log('--------------------------------------');
console.log('This workflow will run the Flask application');
console.log('The application will be available at the webview URL');
console.log('Press Ctrl+C to stop the workflow');
console.log('--------------------------------------');

// Execute the Flask application command
const flaskApp = exec('python app.py');

// Forward stdout and stderr to the console
flaskApp.stdout.on('data', (data) => {
  console.log(`${data}`);
});

flaskApp.stderr.on('data', (data) => {
  console.error(`${data}`);
});

// Handle process exit
flaskApp.on('close', (code) => {
  console.log(`Flask application exited with code ${code}`);
});

// Create a simple health check server
const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
  res.send('GloriaMundo Test Workflow is running. The Flask app should be available at the webview URL.');
});

app.listen(PORT, () => {
  console.log(`Health check server listening on port ${PORT}`);
});