#!/usr/bin/env python3
"""Run all pre-deployment checks. Exit 0 = ready to deploy."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def run(label: str, cmd: list[str], cwd: str | None = None) -> bool:
    print(f"\n==> {label}")
    result = subprocess.run(cmd, cwd=cwd or Path(__file__).resolve().parents[1])
    if result.returncode != 0:
        print(f"FAIL: {label}")
        return False
    print(f"PASS: {label}")
    return True


def check_env_for_vps() -> bool:
    env_path = Path(".env.production")
    if not env_path.exists():
        print("FAIL: .env.production not found")
        return False

    text = env_path.read_text(encoding="utf-8")
    warnings: list[str] = []
    if "DOMAIN=:80" in text or "DOMAIN=ingestx.yourdomain.com" in text:
        warnings.append("DOMAIN is still a placeholder — update before public VPS deploy")
    if "CORS_ORIGINS=http://localhost" in text:
        warnings.append("CORS_ORIGINS is localhost — update to your public HTTPS URL")
    if "you@yourdomain.com" in text:
        warnings.append("ACME_EMAIL is a placeholder — set your real email for TLS")

    if warnings:
        print("\nWARNINGS (OK for local prod test, fix before VPS):")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("\nPASS: production domain/CORS settings look configured")
    return True


def smoke_test(base_url: str, stream_token: str, merchant_id: str) -> bool:
    print(f"\n==> Smoke test against {base_url}")
    ok = True

    for path in ("/health", "/ready"):
        try:
            with urllib.request.urlopen(f"{base_url}{path}", timeout=10) as resp:
                body = resp.read().decode()
                print(f"  {path} -> {resp.status} {body[:120]}")
        except Exception as exc:
            print(f"  FAIL {path}: {exc}")
            ok = False

    req = urllib.request.Request(
        f"{base_url}/api/v1/ledger/{merchant_id}/balance",
        headers={"X-Stream-Token": stream_token},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  ledger balance -> {resp.status}")
    except Exception as exc:
        print(f"  FAIL ledger balance: {exc}")
        ok = False

    if ok:
        print("PASS: smoke test")
    else:
        print("FAIL: smoke test (is the stack running?)")
    return ok


def load_env_value(key: str) -> str:
    for line in Path(".env.production").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    py = sys.executable

    checks = [
        run("Validate .env.production", [py, "scripts/validate_production_env.py"]),
        run("Python lint", [py, "-m", "ruff", "check", "app", "workers", "tests"]),
        run("Python tests", [py, "-m", "pytest", "tests/", "-q"]),
    ]

    dashboard_dir = root / "dashboard"
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if dashboard_dir.exists() and npm:
        checks.append(run("Dashboard build", [npm, "run", "build"], cwd=str(dashboard_dir)))
    elif dashboard_dir.exists():
        print("\nSKIP: Dashboard build (npm not in PATH)")

    if not all(checks):
        return 1

    check_env_for_vps()

    base = load_env_value("SMOKE_TEST_URL") or "http://localhost"
    token = load_env_value("WS_AUTH_TOKEN")
    merchant = load_env_value("DEFAULT_MERCHANT_ID") or "merchant_demo"

    if "--smoke" in sys.argv:
        if not smoke_test(base.rstrip("/"), token, merchant):
            return 1

    print("\n" + "=" * 60)
    print("READY: code and config checks passed.")
    print("Deploy with:")
    print("  docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build")
    print("Then verify:")
    print("  python scripts/predeploy.py --smoke")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
