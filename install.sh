#!/usr/bin/env bash
set -e

REPO="https://raw.githubusercontent.com/Gowthamhegde/lazyk8s/main"

echo "⎈  Installing lazyk8s..."

# ── checks ────────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌  python3 is required."
  echo "    Linux:  sudo apt install python3"
  echo "    macOS:  brew install python"
  exit 1
fi

if ! command -v kubectl &>/dev/null; then
  echo "❌  kubectl is required: https://kubernetes.io/docs/tasks/tools/"
  exit 1
fi

# ── detect WSL ────────────────────────────────────────────────────────────────
IS_WSL=0
grep -qiE "microsoft|wsl" /proc/version 2>/dev/null && IS_WSL=1 && echo "🪟  WSL detected"

# ── dependencies ──────────────────────────────────────────────────────────────
echo "📦  Installing Python dependencies..."
pip3 install textual --quiet --break-system-packages 2>/dev/null \
  || pip3 install textual --quiet

# ── install to /usr/local/bin (always in PATH on every OS/WSL) ───────────────
TMP=$(mktemp)
curl -fsSL "$REPO/lazyk8s" -o "$TMP"
chmod +x "$TMP"

if [ -w /usr/local/bin ]; then
  mv "$TMP" /usr/local/bin/lazyk8s
else
  echo "🔑  Need sudo to install to /usr/local/bin (always in PATH)..."
  sudo mv "$TMP" /usr/local/bin/lazyk8s
fi

echo ""
echo "✅  lazyk8s installed!"
echo ""
echo "   Run now: lazyk8s"
