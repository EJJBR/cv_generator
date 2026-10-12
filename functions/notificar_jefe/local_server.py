"""
functions/notificar_jefe/local_server.py
Emulador local de AWS Lambda Function URL.
Permite ejecutar el handler FaaS como un microservicio serverless HTTP independiente en el puerto 8001
usando únicamente la librería estándar de Python (sin dependencias adicionales).
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Agregar carpeta functions al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lambda_function import lambda_handler

PORT = int(os.environ.get("SERVERLESS_PORT", "8001"))


class LambdaEmulatorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            event = json.loads(post_data.decode("utf-8"))
        except Exception:
            event = {}

        # Invocar la función Lambda de AWS
        resultado = lambda_handler(event, None)

        status_code = resultado.get("statusCode", 200)
        body = resultado.get("body", {})

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "service": "Serverless-Lambda-Emulator"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Log limpio en consola
        sys.stdout.write(f"[Serverless FaaS Emulator :8001] {args[0]} - {args[1]}\n")


def run():
    server = HTTPServer(("0.0.0.0", PORT), LambdaEmulatorHandler)
    print(f"⚡ Emulador AWS Lambda Function URL activo en http://localhost:{PORT}")
    print("   Listo para recibir eventos 'expediente_enviado_jefe'...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEmulador Serverless detenido.")
        server.server_close()


if __name__ == "__main__":
    run()
