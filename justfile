# List all commands
default:
    @just --list
    
# Strip all outputs from notebooks
clean-notebooks:
    pipx run nbstripout materials/01-reading-data/notebook.ipynb
    pipx run nbstripout materials/02-data-exploration-and-validation/notebook.ipynb
    
# Sync all virtual environments
sync-uv:
    cd materials/01-reading-data && uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt
    cd materials/02-data-exploration-and-validation && uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt
    cd materials/05-shiny-app && uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt