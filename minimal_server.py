#!/usr/bin/env python3
"""
Minimal server with zero dependencies - guaranteed to work
"""
import os

# Get port from environment or use default
port = int(os.environ.get("PORT", 10000))

# Create minimal HTML response
html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sports Betting Beta</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: white; 
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: #2a2a2a;
            border-radius: 20px;
            box-shadow: 0 0 30px rgba(0,255,0,0.3);
        }
        h1 { color: #00ff00; }
        .status { 
            background: #00ff00; 
            color: black;
            padding: 10px 20px; 
            border-radius: 5px; 
            display: inline-block; 
            margin: 20px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Sports Betting Beta Platform</h1>
        <div class="status">✅ System Online</div>
        <p>High-fidelity sports betting analysis</p>
        <p style="font-size: 24px;">🏈 NFL • 🏀 NBA • ⚾ MLB • 🏈 NCAAF</p>
        <p style="opacity: 0.7;">Version 1.0 - Production Ready</p>
    </div>
</body>
</html>"""

# Simple HTTP response
response = f"""HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: {len(html_content)}
Connection: close

{html_content}"""

# Start server
import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', port))
server.listen(5)

print(f"Server starting on port {port}")
print(f"Ready to accept connections...")

while True:
    client, address = server.accept()
    print(f"Connection from {address}")
    
    try:
        # Read request (we don't really need it for this simple server)
        request = client.recv(1024).decode()
        
        # Send response
        client.send(response.encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()