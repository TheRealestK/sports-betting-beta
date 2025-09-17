#!/usr/bin/env python3
"""
Ultra Simple HTTP Server - No dependencies
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sports Betting Beta</title>
                <style>
                    body { 
                        font-family: -apple-system, sans-serif; 
                        background: #2c3e50;
                        color: white; 
                        padding: 40px;
                        text-align: center;
                    }
                    h1 { color: #3498db; }
                    .status { 
                        background: #27ae60; 
                        padding: 10px 20px; 
                        border-radius: 5px; 
                        display: inline-block; 
                        margin: 20px;
                    }
                </style>
            </head>
            <body>
                <h1>🎯 Sports Betting Beta Platform</h1>
                <div class="status">✅ System Online</div>
                <p>High-fidelity sports betting analysis platform</p>
                <p>NFL • NBA • MLB • NCAAF</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            status = {
                "status": "online",
                "version": "1.0",
                "sports": ["NFL", "NBA", "MLB", "NCAAF"]
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Override to control logging"""
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"Starting server on port {port}")
    httpd.serve_forever()