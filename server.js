/* Minimal zero-dependency static file server for WrenchLink.
   Used by Railway / any Node host. Serves the current directory. */
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const PORT = process.env.PORT || 8080;

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.ico': 'image/x-icon',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.woff2': 'font/woff2',
  '.woff': 'font/woff',
  '.txt': 'text/plain; charset=utf-8',
  '.map': 'application/json',
};

function safePath(urlPath) {
  let p = decodeURIComponent(urlPath.split('?')[0].split('#')[0]);
  if (p === '/' || p === '') p = '/index.html';
  // prevent path traversal
  const resolved = path.normalize(path.join(ROOT, p));
  if (!resolved.startsWith(ROOT)) return null;
  return resolved;
}

const server = http.createServer((req, res) => {
  let fp = safePath(req.url);
  if (!fp) { res.writeHead(403); res.end('Forbidden'); return; }

  fs.stat(fp, (err, st) => {
    // allow extensionless routes to resolve to .html
    if ((err || !st.isFile()) && !path.extname(fp)) {
      fp = fp + '.html';
    }
    fs.readFile(fp, (e, data) => {
      if (e) {
        // SPA-style fallback to index for unknown routes
        fs.readFile(path.join(ROOT, 'index.html'), (e2, idx) => {
          if (e2) { res.writeHead(404, { 'Content-Type': 'text/plain' }); res.end('404 Not Found'); }
          else { res.writeHead(200, { 'Content-Type': TYPES['.html'] }); res.end(idx); }
        });
        return;
      }
      const type = TYPES[path.extname(fp).toLowerCase()] || 'application/octet-stream';
      res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'public, max-age=300' });
      res.end(data);
    });
  });
});

server.listen(PORT, () => console.log('WrenchLink running on port ' + PORT));
