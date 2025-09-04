#!/usr/bin/env python3
"""
Simple HTTP server to serve SnackPDF static files for demonstration
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/' or self.path == '':
            self.path = '/snackpdf/templates/index.html'
        elif self.path == '/pricing':
            self.path = '/snackpdf/templates/pricing.html'
        elif self.path.startswith('/static/'):
            # Serve static files from snackpdf/static/
            self.path = '/snackpdf' + self.path
        
        return super().do_GET()

if __name__ == "__main__":
    PORT = 8000
    
    # Change to project root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 SnackPDF Demo Server running at http://localhost:{PORT}")
        print(f"📁 Serving from: {os.getcwd()}")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")