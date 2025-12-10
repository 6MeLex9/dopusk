"""
Простой сервер для Web/WASM версии
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import webbrowser


def run_server(port=8000):
    """Запуск локального сервера"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

    url = f"http://localhost:{port}"
    print(f"🚀 Сервер запущен на {url}")
    print("📂 Открываю браузер...")

    # Открываем браузер
    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")


if __name__ == "__main__":
    run_server()