const { spawn } = require('child_process');

const port = process.env.PORT || 3000;
console.log(`Starting Expo on port ${port}`);

const child = spawn('npx', ['expo', 'start', '--port', port, '--host', '0.0.0.0'], {
  stdio: 'inherit',
  env: { ...process.env, PORT: port }
});

child.on('error', (error) => {
  console.error('Error starting Expo:', error);
});

child.on('exit', (code) => {
  console.log(`Expo exited with code ${code}`);
});