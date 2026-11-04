// 本地验收用的静态服务器：把 dist 挂到 /aicoding/ 前缀下。
// 为什么需要它：站点 base 是 /aicoding，直接 `serve dist` 挂根目录会让所有带 BASE 的链接 404；
// 而按文件路径检查（不经过 HTTP）发现不了这个问题——必须起一个"带前缀"的服务再上浏览器。
//
// 用法：node scripts/serve-dist.cjs [port]     默认 4322
// 然后：http://127.0.0.1:4322/aicoding/
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "dist");
const PREFIX = "/aicoding";
const PORT = Number(process.argv[2] || 4322);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".webp": "image/webp",
  ".woff2": "font/woff2",
  ".wasm": "application/wasm",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8",
};

http
  .createServer((req, res) => {
    const u = decodeURIComponent(req.url.split("?")[0]);
    // 前缀外的请求按静态文件回退（页面里若引用了根路径资源不至于全 404）
    if (u !== PREFIX && !u.startsWith(PREFIX + "/")) {
      const raw = path.join(ROOT, u);
      return fs.readFile(raw, (e, d) => {
        if (e) {
          res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
          return res.end("outside base: " + u);
        }
        res.writeHead(200, { "Content-Type": MIME[path.extname(raw).toLowerCase()] || "application/octet-stream" });
        res.end(d);
      });
    }
    let p = path.join(ROOT, u.slice(PREFIX.length));
    if (p.endsWith(path.sep) || p === ROOT) p = path.join(p, "index.html");
    fs.readFile(p, (e, d) => {
      if (e) {
        res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
        return res.end("404 " + u);
      }
      res.writeHead(200, { "Content-Type": MIME[path.extname(p).toLowerCase()] || "application/octet-stream" });
      res.end(d);
    });
  })
  .listen(PORT, () => console.log(`serving ${ROOT} at http://127.0.0.1:${PORT}${PREFIX}/`));
