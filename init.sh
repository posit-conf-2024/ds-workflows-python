#!/bin/bash

# Clone this repo
# git clone https://github.com/posit-conf-2024/ds-workflows-python.git
# cd ds-workflows-python

# Add required stuff to your .bashrc
echo "" >> ~/.bashrc && echo "" >> ~/.bashrc
cat assets/templates/.bashrc >> ~/.bashrc
echo "" >> ~/.bashrc && echo "" >> ~/.bashrc

# Install starship for a better terminal
wget --no-verbose --directory-prefix '/tmp' https://github.com/starship/starship/releases/download/v1.20.1/starship-x86_64-unknown-linux-musl.tar.gz \
    && tar --directory ~/.local/bin -zxf /tmp/starship-x86_64-unknown-linux-musl.tar.gz \
    && mkdir -p ~/.config \
    && cp assets/templates/starship.toml ~/.config/starship.toml

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Copy project manager extension config
mkdir -p ~/.vscode-server/User/globalStorage/alefragnani.project-manager
cp assets/templates/projects.json ~/.vscode-server/User/globalStorage/alefragnani.project-manager/projects.json

# Copy VS Code Settings
mkdir -p ~/.vscode-server/User/
cp assets/templates/vscode-settings.json ~/.vscode-server/User/settings.json

echo "Setup complete!"