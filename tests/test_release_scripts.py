"""Exercise the real BAT updater against a local release server."""
import hashlib
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows BAT scripts")
@pytest.mark.parametrize("failure", [None, "size", "checksum"])
@pytest.mark.parametrize("installed", [False, True])
@pytest.mark.parametrize("binary_checksum", [False, True])
def test_bat_update(tmp_path, failure, installed, binary_checksum):
    root = Path(__file__).resolve().parents[1]
    folder = tmp_path / "User's folder ! тест"
    folder.mkdir()
    old = b"MZ" + b"old" * 1024
    new = b"MZ" + b"new" * 1024
    app = folder / "YouTube_Downloader.exe"
    if installed:
        app.write_bytes(old)
    checksum = hashlib.sha256(new if failure != "checksum" else old).hexdigest()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            address = f"http://127.0.0.1:{self.server.server_port}"
            if self.path == "/release":
                payload = json.dumps({
                    "tag_name": "test-release",
                    "assets": [
                        {"name": "YouTube_Downloader.exe", "size": len(new) + (failure == "size"),
                         "browser_download_url": address + "/app"},
                        {"name": "SHA256SUMS.txt", "browser_download_url": address + "/hash"},
                    ],
                }).encode()
            elif self.path == "/app":
                payload = new
            elif self.path == "/hash":
                payload = f"{checksum}  YouTube_Downloader.exe\n".encode()
            else:
                self.send_error(404)
                return
            self.send_response(200)
            content_type = "application/json" if self.path == "/release" else "text/plain"
            if self.path == "/hash" and binary_checksum:
                content_type = "application/octet-stream"
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        script = (root / "Обновить(приложение).bat").read_text(encoding="utf-8")
        script = script.replace(
            "https://api.github.com/repos/%GITHUB_OWNER%/%GITHUB_REPO%/releases/latest",
            f"http://127.0.0.1:{server.server_port}/release",
        ).replace('start "" "%APP_PATH%"', 'echo Test: launch skipped')
        script = script.replace('} catch {exit 1}', '} catch {Write-Host $_; exit 1}')
        updater = folder / "updater.bat"
        updater.write_bytes(script.replace("\n", "\r\n").encode("utf-8"))
        result = subprocess.run(["cmd.exe", "/d", "/c", str(updater)], input=b"\n",
                                capture_output=True, timeout=90)
        assert result.returncode == (1 if failure else 0), result.stdout.decode("utf-8", errors="replace") + result.stderr.decode("utf-8", errors="replace")
        if failure and not installed:
            assert not app.exists()
        else:
            assert app.read_bytes() == (old if failure else new)
        if not failure and installed:
            assert (folder / "YouTube_Downloader.exe.backup").read_bytes() == old
        if not installed:
            assert not (folder / "YouTube_Downloader.exe.backup").exists()
        if not failure:
            message = b'Application updated successfully!' if installed else b'Application installed successfully!'
            assert message in result.stdout
    finally:
        server.shutdown()
        server.server_close()
