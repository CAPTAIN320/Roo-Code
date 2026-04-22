#!/usr/bin/env python3
"""
build_and_install.py
--------------------
Builds the Code Captain VS Code extension and installs it locally.

Usage:
    python3 scripts/build_and_install.py [--editor=code|cursor|code-insiders]

Options:
    --editor=<cmd>   VS Code-compatible editor CLI command (default: code)
    --skip-install   Skip `pnpm install` (faster if deps haven't changed)
"""

import argparse
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(REPO_ROOT, "src")
BIN_DIR = os.path.join(REPO_ROOT, "bin")
PACKAGE_JSON = os.path.join(SRC_DIR, "package.json")


def run(cmd: list[str], cwd: str = REPO_ROOT) -> None:
    """Run a command, streaming output. Exits on failure."""
    print(f"\n▶ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"\n❌ Command failed: {' '.join(cmd)}", file=sys.stderr)
        sys.exit(result.returncode)


def read_package_json() -> dict:
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and install the Code Captain VS Code extension.")
    parser.add_argument("--editor", default="code", help="VS Code CLI command (default: code)")
    parser.add_argument("--skip-install", action="store_true", help="Skip pnpm install step")
    args = parser.parse_args()

    pkg = read_package_json()
    name = pkg["name"]          # e.g. code-captain
    version = pkg["version"]    # e.g. 3.52.1
    publisher = pkg["publisher"] # e.g. local
    extension_id = f"{publisher}.{name}"
    vsix_path = os.path.join(BIN_DIR, "code-captain.vsix")

    print("╔══════════════════════════════════════╗")
    print("║   Code Captain — Build & Install     ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Extension : {extension_id} v{version}")
    print(f"  VSIX      : {vsix_path}")
    print(f"  Editor    : {args.editor}")

    # 1. Install dependencies
    if not args.skip_install:
        print("\n[1/4] Installing dependencies...")
        run(["pnpm", "install"])
    else:
        print("\n[1/4] Skipping pnpm install (--skip-install)")

    # 2. Bundle (--force bypasses turbo cache so asset changes like icons are always picked up)
    print("\n[2/4] Bundling extension...")
    run(["pnpm", "run", "bundle", "--force"])

    # 3. Package into VSIX
    print("\n[3/4] Packaging VSIX...")
    os.makedirs(BIN_DIR, exist_ok=True)
    run(
        ["npx", "vsce", "package", "--no-dependencies", "--out", vsix_path],
        cwd=SRC_DIR,
    )

    if not os.path.exists(vsix_path):
        print(f"\n❌ VSIX not found at {vsix_path}", file=sys.stderr)
        sys.exit(1)

    # 4. Uninstall old version, install new
    print("\n[4/4] Installing into VS Code...")
    try:
        subprocess.run(
            [args.editor, "--uninstall-extension", extension_id],
            cwd=REPO_ROOT,
            check=False,  # OK if not installed yet
        )
    except FileNotFoundError:
        print(f"  ⚠️  '{args.editor}' not found in PATH — skipping uninstall")

    run([args.editor, "--install-extension", vsix_path])

    print("\n✅ Done! Reload VS Code (Cmd+Shift+P → 'Developer: Reload Window') to activate Code Captain.")


if __name__ == "__main__":
    main()
