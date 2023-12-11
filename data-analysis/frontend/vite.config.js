// vite.config.js
export default {
    server: {
      port: 3000,
      setHeaders(res) {
        res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
        res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
      },
    },
  };
  