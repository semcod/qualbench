#!/usr/bin/env python3
"""Simple HTTP server for QualBench landing page."""

import http.server
import socketserver
import os

# Constants
DEFAULT_PORT = 8080

PORT = DEFAULT_PORT

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_GET(self) -> None:
        # Serve index.html as root
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

if __name__ == '__main__':
    os.chdir('/home/tom/github/semcod/qualbench/www')
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving QualBench landing page at http://localhost:{PORT}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
