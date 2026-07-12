import socket
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app) 

def process_node(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        code = sock.connect_ex((ip, port))
        
        banner = "Unknown"
        if code == 0:
            try:
                sock.send(b"HEAD / HTTP/1.1\r\n\r\n")
                raw_banner = sock.recv(100)
                if raw_banner:
                    banner = raw_banner.decode('utf-8', errors='ignore').strip().replace('\n', ' ').replace('\r', '')
            except:
                pass
            sock.close()
            return {"port": str(port), "status": "OPEN", "banner": banner}
        sock.close()
        return None
    except:
        return None

@app.route('/api/scan', methods=['POST'])
def handle_scan():
    data = request.json or {}
    target = data.get('target')
    
    if not target:
        return jsonify({"error": "Target destination is required"}), 400
        
    try:
        start_port = int(data.get('start_port', 10))
        end_port = int(data.get('end_port', 100))
    except ValueError:
        return jsonify({"error": "Ports must be valid numbers"}), 400
    
    try:
        resolved_ip = socket.gethostbyname(target)
    except socket.gaierror:
        return jsonify({"error": "Unable to resolve target host"}), 400

    port_vectors = range(start_port, end_port + 1)
    open_ports = []

    with ThreadPoolExecutor(max_workers=64) as pipeline:
        futures = [pipeline.submit(process_node, resolved_ip, port) for port in port_vectors]
        for future in futures:
            result = future.result()
            if result:
                open_ports.append(result)

    return jsonify({
        "target": target,
        "ip": resolved_ip,
        "open_ports": open_ports
    })


from flask_cors import CORS  # 1. Import this

app = Flask(__name__)
CORS(app)  # 2. Add this line right here!

@app.route('/scan', methods=['POST', 'OPTIONS']) # Add OPTIONS to help with CORS
def scan():
    if request.method == 'OPTIONS':
        return '', 200 # Handle pre-flight request
        
    data = request.json
    # ... your existing logic ...
    return jsonify({"status": "Success", "data": "Scan Received"})