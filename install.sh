#!/usr/bin/env bash
set -e

REPO="https://raw.githubusercontent.com/Gowthamhegde/lazyk8s/main"
INSTALL_DIR="$HOME/.local/bin"
SCRIPT="$INSTALL_DIR/lazyk8s"

echo "⎈  Installing lazyk8s..."

# 1. Check python3
if ! command -v python3 &>/dev/null; then
  echo "❌  python3 is required. Install it first."
  exit 1
fi

# 2. Check kubectl
if ! command -v kubectl &>/dev/null; then
  echo "❌  kubectl is required. Install it first: https://kubernetes.io/docs/tasks/tools/"
  exit 1
fi

# 3. Install textual
echo "📦  Installing dependencies..."
pip3 install textual --quiet --break-system-packages 2>/dev/null || pip3 install textual --quiet

# 4. Download script
mkdir -p "$INSTALL_DIR"
curl -fsSL "$REPO/lazyk8s" -o "$SCRIPT"
chmod +x "$SCRIPT"

# 5. Add to PATH if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  SHELL_RC="$HOME/.bashrc"
  [[ "$SHELL" == */zsh ]] && SHELL_RC="$HOME/.zshrc"
  echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
  echo "✅  Added $INSTALL_DIR to PATH in $SHELL_RC"
  echo "   Run: source $SHELL_RC"
fi

echo ""
echo "✅  lazyk8s installed! Run: lazyk8s"
