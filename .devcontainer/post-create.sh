#!/bin/bash
set -e

echo "🚀 Setting up Python development environment..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Sync dependencies
echo "📦 Syncing dependencies with uv..."
uv sync

# Set up SSH keys permissions
if [ -d "$HOME/.ssh" ]; then
    echo "🔐 Configuring SSH keys..."
    chmod 700 "$HOME/.ssh"
    chmod 600 "$HOME/.ssh/id_*" 2>/dev/null || true
    chmod 644 "$HOME/.ssh/*.pub" 2>/dev/null || true
    chmod 644 "$HOME/.ssh/known_hosts" 2>/dev/null || true
fi

# Install oh-my-zsh plugins if not already installed
if [ -d "$HOME/.oh-my-zsh" ]; then
    echo "🎨 Setting up zsh plugins..."
    ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

    # Install zsh-autosuggestions
    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
        git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
    fi

    # Install zsh-syntax-highlighting
    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
        git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
    fi

    # Install zsh-history-substring-search
    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-history-substring-search" ]; then
        git clone https://github.com/zsh-users/zsh-history-substring-search.git "$ZSH_CUSTOM/plugins/zsh-history-substring-search"
    fi

    # Install powerlevel10k theme
    if [ ! -d "$ZSH_CUSTOM/themes/powerlevel10k" ]; then
        git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$ZSH_CUSTOM/themes/powerlevel10k"
    fi
fi

# Configure zsh with your custom settings
echo "⚙️  Configuring zsh..."
cat > "$HOME/.zshrc" << 'ZSHRC_EOF'
# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Powerlevel10k theme
ZSH_THEME="powerlevel10k/powerlevel10k"

# Plugins
plugins=(
    git
    sudo
    z
    docker
    python
    npm
    command-not-found
    zsh-autosuggestions
    zsh-history-substring-search
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# Arrow keys for history substring search
bindkey '^[[A' history-substring-search-up
bindkey '^[[B' history-substring-search-down

# Editor
export VISUAL=vim
export EDITOR="$VISUAL"

# Add local bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Project aliases (if setup script exists)
WORKSPACE_FOLDER="${containerWorkspaceFolder:-$(pwd)}"
if [ -f "$WORKSPACE_FOLDER/scripts/setup-aliases.sh" ]; then
    source "$WORKSPACE_FOLDER/scripts/setup-aliases.sh"
fi
ZSHRC_EOF

# Set zsh as default shell
if [ "$SHELL" != "$(which zsh)" ]; then
    echo "🐚 Setting zsh as default shell..."
    sudo chsh -s "$(which zsh)" "$(whoami)" || echo "Note: Shell change may require container restart"
fi

# Configure git (if not already configured)
if [ -z "$(git config --global user.name)" ]; then
    echo "📝 Git not configured. Please run:"
    echo "   git config --global user.name 'Your Name'"
    echo "   git config --global user.email 'your.email@example.com'"
fi

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install || echo "Note: Pre-commit hooks installation skipped"

echo "✅ Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Configure git: git config --global user.name 'Your Name'"
echo "   2. Test SSH: ssh -T git@github.com"
echo "   3. Run tests: uv run pytest"
echo "   4. Start coding! 🎉"
