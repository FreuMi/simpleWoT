from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    tests_dir = Path(__file__).resolve().parent
    repo_root = tests_dir.parent
    python = repo_root / ".venv" / "bin" / "python"
    python_executable = str(python if python.exists() else Path(sys.executable))

    clients = sorted(tests_dir.glob("test_*/client.py"))
    if not clients:
        print("No test clients found.")
        return 1

    env = os.environ.copy()
    src_path = str(repo_root / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing_pythonpath else f"{src_path}{os.pathsep}{existing_pythonpath}"

    failures = []
    for client in clients:
        test_name = client.parent.relative_to(repo_root)
        result = subprocess.run(
            [python_executable, str(client.relative_to(repo_root))],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        if result.returncode == 0:
            print(f"PASS {test_name}")
            continue

        print(f"FAIL {test_name}")
        failures.append((test_name, result))

    if failures:
        print()
        for test_name, result in failures:
            print(f"--- {test_name} output ---")
            if result.stdout:
                print(result.stdout.rstrip())
            if result.stderr:
                print(result.stderr.rstrip())
            print(f"exit code: {result.returncode}")
            print()

    passed = len(clients) - len(failures)
    print(f"{passed} passed, {len(failures)} failed")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
