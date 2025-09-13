const http = require('http');
const { createProxyMiddleware } = require('http-proxy-middleware');

const port = 3000;
const targetPort = 8081;

console.log(`Starting proxy server on port ${port}, forwarding to ${targetPort}`);

// Create proxy middleware
const proxy = createProxyMiddleware({
  target: `http://localhost:${targetPort}`,
  changeOrigin: true,
  ws: true, // Enable WebSocket proxying for hot reload
  logLevel: 'info'
});

// Create server
const server = http.createServer(proxy);

// Listen on port 3000
server.listen(port, '0.0.0.0', () => {
  console.log(`Proxy server running on http://0.0.0.0:${port}`);
  console.log(`Forwarding requests to http://localhost:${targetPort}`);
});

server.on('error', (error) => {
  console.error('Proxy server error:', error);
});

// Handle WebSocket upgrades for hot reload
server.on('upgrade', proxy.upgrade);