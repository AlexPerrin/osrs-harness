import json
import os
import subprocess
import sys
import tempfile
import unittest

BRIDGE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp", "devtools_bridge.py")


class Front(unittest.TestCase):
    def run_front(self, backend_reply):
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "backend")
            with open(fake, "w") as f:
                f.write("#!/bin/sh\n" + (f"echo '{backend_reply}'\n" if backend_reply else "echo 'no client' >&2\n"))
            os.chmod(fake, 0o755)
            reqs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "x", "arguments": {}}}]
            p = subprocess.run([sys.executable, BRIDGE, "test", fake], input="\n".join(json.dumps(r) for r in reqs),
                               capture_output=True, text=True, env={**os.environ, "HOME": d})
            return [json.loads(line) for line in p.stdout.splitlines()]

    def test_a_session_connects_without_a_client(self):
        out = self.run_front(None)
        self.assertEqual([o["id"] for o in out], [1, 2, 3])                     # the notification gets no answer
        self.assertEqual(out[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertTrue(out[1]["result"]["tools"])                               # the snapshot answers the list
        self.assertIn("no client", out[2]["error"]["message"])

    def test_a_running_client_answers_calls(self):
        out = self.run_front('{"jsonrpc":"2.0","id":1,"result":{"content":[{"type":"text","text":"ok"}]}}')
        self.assertEqual(out[2], {"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "ok"}]}})


if __name__ == "__main__":
    unittest.main()
