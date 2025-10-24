#!/usr/bin/env python3
"""
Простой webhook сервер для демонстрации Git автоматизации
Показывает как Git события могут запускать автоматические процессы
"""

import tempfile
import subprocess
import os
import json
import hashlib
import hmac
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# Конфигурация
PORT = 8080

class WebhookHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode('utf-8'))
            success = self._process_webhook(payload)
            
            # Отправляем ответ только если соединение еще живо
            try:
                if success:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "success"}')
                    print("✅ Отправлен ответ 200 - деплой успешен")
                else:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "deployment_failed"}')
                    print("❌ Отправлен ответ 500 - деплой провален")
            except BrokenPipeError:
                print("⚠️  GitHub отключился, но деплой выполнен")
                    
        except json.JSONDecodeError:
            print("❌ Ошибка парсинга JSON")
            try:
                self.send_response(400)
                self.end_headers()
            except:
                pass
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            try:
                self.send_response(500)
                self.end_headers()
            except:
                pass

    def do_GET(self):
        """Простая страница статуса"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevOps Webhook Demo</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #4d90cd; text-align: center; }}
                .info {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 DevOps Webhook Demo Server</h1>
                <div class="info">
                    <p><strong>Статус:</strong> Сервер активен и ожидает webhook события от GitHub</p>
                    <p><strong>Время запуска:</strong> {time}</p>
                    <p><strong>Порт:</strong> {port}</p>
                </div>
                <p>Этот сервер демонстрирует как Git события могут автоматически запускать процессы.</p>
                <p>Каждый push, pull request или release будет логироваться в консоли сервера.</p>
            </div>
        </body>
        </html>
        """.format(time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), port=PORT)

        self.wfile.write(html.encode('utf-8'))

    def _process_webhook(self, payload):
        """Обработка webhook события"""

        # Получаем информацию о событии
        event_type = self.headers.get('X-GitHub-Event', 'unknown')
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n🔔 Получено webhook событие:")
        print(f"   Время: {timestamp}")
        print(f"   Тип события: {event_type}")
        print(f"   Репозиторий: {repo_name}")

        # Обрабатываем разные типы событий
        if event_type == 'push':
            res =  self._handle_push_event(payload)
            return res
        elif event_type == 'pull_request':
            self._handle_pr_event(payload)
        elif event_type == 'release':
            self._handle_release_event(payload)

        elif enent_type == 'create':
            print(f"Создан {payload.get('ref_type')}: {payload.get('ref')}")
            return True
        else:
            print(f"   ℹ️  Событие '{event_type}' - базовое логирование")

    
    def _handle_push_event(self, payload):
        commits = payload.get('commits', [])
        branch = payload.get('ref', '').replace('refs/heads/', '')
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        clone_url = payload.get('repository', {}).get('clone_url', 'unknown')

        print(f"   📝 Push в ветку: {branch}")
        print(f"   👤 Автор: {pusher}")
        print(f"   📊 Коммитов: {len(commits)}")

        print(f"   🚀 ЗАПУСКАЕМ АВТОМАТИЗАЦИЮ:")
        print(f"      - Запуск тестов для ветки {branch}")
        print(f"      - Проверка качества кода")

        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"Временная директория: {tmpdir}")

            try:
                subprocess.run(
                    ["git", "clone", clone_url, tmpdir],
                    check=True
                )

                subprocess.run(
                    ["git", "checkout", branch],
                    cwd=tmpdir,
                    check=True
                )

                # ПРОПУСТИТЬ SUBMODULES - используем локальные файлы
                print(f"      - Пропускаем submodules (используем локальные файлы)...")

                print(f"      - Запуск тестов...")
                result = subprocess.run(
                    ["./devops/test.sh"],
                    cwd=tmpdir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"      ✅ Тесты прошли успешно!")
                print(f"         {result.stdout.strip()}")

                print(f"      - Запуск деплоя...")
                subprocess.run(
                    ["./devops/deploy.sh"],
                    cwd=tmpdir,
                    check=True
                )
                print(f"      ✅ Деплой завершен успешно!")
                return True

            except subprocess.CalledProcessError as e:
                print(f"      ❌ Ошибка деплоя!")
                print(f"         {e.stdout if e.stdout else 'Нет вывода'}")
                if e.stderr:
                    print(f"         Ошибка: {e.stderr}")
                return False
            except Exception as e:
                print(f"      ❌ Неожиданная ошибка: {e}")
                return False

    def _handle_pr_event(self, payload):
        """Обработка Pull Request события"""
        action = payload.get('action', '')
        pr_number = payload.get('pull_request', {}).get('number', '')
        title = payload.get('pull_request', {}).get('title', '')

        print(f"   🔀 Pull Request #{pr_number}: {action}")
        print(f"   📋 Заголовок: {title}")

    def _handle_release_event(self, payload):
        """Обработка Release события"""
        action = payload.get('action', '')
        tag_name = payload.get('release', {}).get('tag_name', '')

        print(f"   🏷️  Release {tag_name}: {action}")

def main():
    """Запуск webhook сервера"""

    print(f"🚀 Запуск DevOps Webhook Demo Server")
    print(f"📡 Порт: {PORT}")
    print(f"🌐 URL: http://0.0.0.0:{PORT}")
    print(f"🔧 Webhook URL: http://0.0.0.0:{PORT}/webhook")
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n👀 Ожидание webhook событий от GitHub...")
    print(f"💡 Для остановки: Ctrl+C\n")

    try:
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Сервер остановлен")

if __name__ == '__main__':
    main()
