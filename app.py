import socket
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
# Enable CORS for all routes so your frontend can talk to the backend
CORS(app) 

def process_node(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5) # Slightly longer timeout for stability
        code = sock.connect_ex((ip, port))
        
        if code == 0:
            banner = "Open"
            # Attempt a basic banner grab
            try:
                sock.send(b"HEAD / HTTP/1.1\r\n\r\n")
                raw_banner = sock.recv(100)
                if raw_banner:
                    banner = raw_banner.decode('utf-8', errors='ignore').split('\n')[0]
            except:
                pass
            sock.close()
            return {"port": port, "status": "OPEN", "banner": banner}
        sock.close()
    except:
        pass
    return None

@app.route('/scan', methods=['POST']) # Ensure this matches your frontend fetch()
def handle_scan():
    data = request.json or {}
    target = data.get('target')
    
    if not target:
        return jsonify({"error": "Target required"}), 400
        
    try:
        start_port = int(data.get('start_port', 10))
        end_port = int(data.get('end_port', 100))
        resolved_ip = socket.gethostbyname(target)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    open_ports = []
    # Threading for speed
    with ThreadPoolExecutor(max_workers=64) as pipeline:
        futures = [pipeline.submit(process_node, resolved_ip, port) for port in range(start_port, end_port + 1)]
        for future in futures:
            result = future.result()
            if result:
                open_ports.append(result)

    return jsonify({
        "target": target,
        "ip": resolved_ip,
        "open_ports": open_ports
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)