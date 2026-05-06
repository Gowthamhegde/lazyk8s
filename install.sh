#!/usr/bin/env bash
set -e

REPO="https://raw.githubusercontent.com/Gowthamhegde/lazyk8s/main"
INSTALL_DIR="$HOME/.local/bin"
SCRIPT="$INSTALL_DIR/lazyk8s"

echo "⎈  Installing lazyk8s..."

# ── checks ────────────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌  python3 is required."
  echo "    Linux:  sudo apt install python3  OR  sudo dnf install python3"
  echo "    macOS:  brew install python"
  exit 1
fi

if ! command -v kubectl &>/dev/null; then
  echo "❌  kubectl is required: https://kubernetes.io/docs/tasks/tools/"
  exit 1
fi

# ── dependencies ──────────────────────────────────────────────────────────────
echo "📦  Installing Python dependencies..."
pip3 install textual --quiet --break-system-packages 2>/dev/null \
  || pip3 install textual --quiet

# ── install script ────────────────────────────────────────────────────────────
mkdir -p "$INSTALL_DIR"
curl -fsSL "$REPO/lazyk8s" -o "$SCRIPT"
chmod +x "$SCRIPT"

# ── PATH ──────────────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  SHELL_RC="$HOME/.bashrc"
  [[ "$SHELL" == */zsh  ]] && SHELL_RC="$HOME/.zshrc"
  [[ "$SHELL" == */fish ]] && SHELL_RC="$HOME/.config/fish/config.fish"
  echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
  echo "   ➜  Added to PATH in $SHELL_RC — run: source $SHELL_RC"
fi

echo ""
echo "✅  Done! Run: lazyk8s"
