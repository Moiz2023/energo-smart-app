const { spawn } = require('child_process');

console.log('Starting Expo Metro bundler and proxy server...');

// Start Expo on port 8081
const expo = spawn('npx', ['expo', 'start', '--host', '0.0.0.0'], {
  stdio: 'pipe',
  env: { ...process.env }
});

expo.stdout.on('data', (data) => {
  console.log(`[EXPO] ${data.toString().trim()}`);
});

expo.stderr.on('data', (data) => {
  console.error(`[EXPO] ${data.toString().trim()}`);
});

// Wait a bit for Expo to start, then start proxy
setTimeout(() => {
  console.log('Starting proxy server on port 3000...');
  const proxy = spawn('node', ['proxy-server.js'], {
    stdio: 'pipe',
    env: { ...process.env }
  });

  proxy.stdout.on('data', (data) => {
    console.log(`[PROXY] ${data.toString().trim()}`);
  });

  proxy.stderr.on('data', (data) => {
    console.error(`[PROXY] ${data.toString().trim()}`);
  });

  proxy.on('error', (error) => {
    console.error('[PROXY] Error:', error);
  });
}, 5000);

expo.on('error', (error) => {
  console.error('[EXPO] Error:', error);
});

expo.on('exit', (code) => {
  console.log(`[EXPO] Exited with code ${code}`);
  process.exit(code);
});