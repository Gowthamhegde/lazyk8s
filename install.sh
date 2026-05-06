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

# ── dependencies ──────────────────────────────────────────────────────────────
echo "📦  Installing Python dependencies..."
pip3 install textual --quiet --break-system-packages 2>/dev/null \
  || pip3 install textual --quiet

# ── pick install dir ──────────────────────────────────────────────────────────
# Priority: /usr/local/bin (always in PATH) → sudo fallback → ~/.local/bin
if [ -w /usr/local/bin ]; then
  INSTALL_DIR="/usr/local/bin"
elif command -v sudo &>/dev/null && sudo -n true 2>/dev/null; then
  INSTALL_DIR="/usr/local/bin"
  USE_SUDO=1
else
  INSTALL_DIR="$HOME/.local/bin"
  mkdir -p "$INSTALL_DIR"
fi

# ── download ──────────────────────────────────────────────────────────────────
TMP=$(mktemp)
curl -fsSL "$REPO/lazyk8s" -o "$TMP"
chmod +x "$TMP"

if [ "${USE_SUDO:-0}" = "1" ]; then
  sudo mv "$TMP" "$INSTALL_DIR/lazyk8s"
else
  mv "$TMP" "$INSTALL_DIR/lazyk8s"
fi

# ── configure PATH on all shells ──────────────────────────────────────────────
configure_path() {
  local rc="$1"
  local line='export PATH="$HOME/.local/bin:$PATH"'
  [ -f "$rc" ] || return
  grep -qxF "$line" "$rc" 2>/dev/null || echo "$line" >> "$rc"
}

if [ "$INSTALL_DIR" = "$HOME/.local/bin" ]; then
  configure_path "$HOME/.bashrc"
  configure_path "$HOME/.bash_profile"
  configure_path "$HOME/.zshrc"
  configure_path "$HOME/.profile"

  # fish shell
  FISH_CFG="$HOME/.config/fish/config.fish"
  if [ -f "$FISH_CFG" ]; then
    grep -q "local/bin" "$FISH_CFG" \
      || echo 'fish_add_path $HOME/.local/bin' >> "$FISH_CFG"
  fi

  # make it work RIGHT NOW in this session
  export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "✅  lazyk8s installed to $INSTALL_DIR"
echo ""
echo "   Run: lazyk8s"
