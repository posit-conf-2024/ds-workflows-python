# List all commands
default:
    @just --list

# Clean uv
clean-uv:
    uv cache clean
    rm -rf materials/01-reading-data/.venv
    rm -rf materials/02-data-exploration-and-validation/.venv
    rm -rf materials/03-model-training/.venv
    rm -rf materials/04-model-monitoring/.venv
    rm -rf materials/05-shiny-app/.venv

# Set up virtual envs for all projects
bootstrap-uv:
    cd materials/01-reading-data && uv venv && uv pip sync requirements.txt
    cd materials/02-data-exploration-and-validation && uv venv && uv pip sync requirements.txt
    cd materials/03-model-training && uv venv && uv pip sync requirements.txt
    cd materials/04-model-monitoring && uv venv && uv pip sync requirements.txt
    cd materials/05-shiny-app && uv venv && uv pip sync requirements.txt

# Run clean-uv and bootstrap-uv
uv:
    just clean-uv
    just bootstrap-uv

# Strip all outputs from notebooks
clean-notebooks:
    uvx nbstripout materials/01-reading-data/notebook.ipynb
    uvx nbstripout materials/02-data-exploration-and-validation/notebook.ipynb
    uvx nbstripout materials/03-model-training/notebook.ipynb
    uvx nbstripout materials/04-model-monitoring/notebook.ipynb

# Remove all intermediary files (e.g. .venv, html outputs)
clean-files:
    rm -rf materials/01-reading-data/.cache materials/01-reading-data/.venv
    rm -rf materials/02-data-exploration-and-validation/.venv \
        materials/02-data-exploration-and-validation/email-preview \
        materials/02-data-exploration-and-validation/notebook_files \
        materials/02-data-exploration-and-validation/.output_metadata.json
    rm -rf materials/03-model-training/.venv
    rm -rf materials/04-model-monitoring/.venv
    rm -rf materials/05-shiny-app/.venv

# Sync all virtual environments
sync-uv:
    cd materials/01-reading-data && uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt
    cd materials/02-data-exploration-and-validation && uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt
    cd materials/05-shiny-app && uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt