"""Host-side runtime prompt guard, used only by real unittest setup/teardown."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parent
STAND = KIT.parent / "paypilot-stand"


def docker(*args, input_bytes=None):
    result = subprocess.run(["docker", "compose", *args], cwd=STAND,
                            input=input_bytes, capture_output=True, check=True)
    return result.stdout


def read_base():
    return base64.b64decode(docker("exec", "-T", "stand", "python", "-c",
        "import base64;from app.agent.prompt import BASE_FILE;"
        "print(base64.b64encode(BASE_FILE.read_bytes()).decode())").strip())


def write_base(content):
    docker("exec", "-T", "stand", "python", "-c",
           "import sys;from app.agent.prompt import BASE_FILE;"
           "BASE_FILE.write_bytes(sys.stdin.buffer.read())", input_bytes=content)


def model_configuration():
    raw = docker("exec", "-T", "stand", "python", "-c",
        "import json,os,sys;print(json.dumps({'provider':os.getenv('LLM_PROVIDER'),"
        "'configured_model':os.getenv('LLM_MODEL') or None,'python':sys.version.split()[0]}))")
    result = json.loads(raw)
    # No API call: identify the provider's configured default from its source.
    if not result["configured_model"] and result["provider"] == "anthropic":
        result["default_model_source"] = docker("exec", "-T", "stand", "python", "-c",
            "from pathlib import Path;import re;"
            "s=Path('/stand/app/agent/providers/anthropic_provider.py').read_text();"
            "print(re.findall(r'claude-[a-zA-Z0-9-]+',s))").decode().strip()
    return result


class PromptGuard:
    def __init__(self):
        self.original = read_base()
        self.sha256 = hashlib.sha256(self.original).hexdigest()

    def append(self, line):
        if not line or "\n" in line or "\r" in line:
            raise ValueError("The experiment requires one nonempty line")
        write_base(self.original.rstrip() + b"\n\n" + line.encode("utf-8") + b"\n")

    def restore(self):
        write_base(self.original)
        if read_base() != self.original:
            raise RuntimeError("Runtime base prompt was not restored byte for byte")
