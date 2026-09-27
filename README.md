# Hexlock Trade Group

Static multilingual landing page. Run locally with `npm run dev` (Python 3 required); no application server, database, or third-party JavaScript is used.

The `_headers` file uses the static-host headers format supported by Cloudflare Pages and Netlify. For other hosts, configure equivalent response headers there; the HTML also carries a CSP fallback, but frame protection and the other security headers require HTTP response headers. Serve the site over HTTPS in production for HSTS to take effect.