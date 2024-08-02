# ----------------------------------------------------------------
# Added for Posit Worskshop
# ----------------------------------------------------------------

# Secrets
export CONNECT_API_KEY='xxx'
export DATABASE_PASSWORD_PYTHON='xxxxx'
export WSDOT_ACCESS_CODE='xxxx'

# Posit Connect
export CONNECT_SERVER='https://pub.ferryland.posit.team/'

# Database
export DATABASE_HOST='demo01-staging-ferryland-20240702155133310700000001.cjiq6iow80rt.us-east-2.rds.amazonaws.com'
export DATABASE_USER_PYTHON='cadet_py'
export DATABASE_NAME_PYTHON='pyferries'
export DATABASE_SCHEMA='deckhand'
export DATABASE_URI_PYTHON="postgresql://${DATABASE_USER_PYTHON}:${DATABASE_PASSWORD_PYTHON}@${DATABASE_HOST}:5432/${DATABASE_NAME_PYTHON}?options=-csearch_path%3D${DATABASE_SCHEMA}"

# uv
alias uvinit='uv venv && source .venv/bin/activate'
alias uvcompile='uv pip compile requirements.in --quiet --output-file requirements.txt'
alias uvsync='uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt'

# pip
alias pipinit='python -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip wheel setuptools'

# kernels
alias kernelinit='python -m ipykernel install --name $(basename $(pwd)) --display-name $(basename $(pwd)) --user'

# PATH
export PATH="${HOME}/.local/bin:/opt/python/3.12.4/bin:${PATH}"

# Starship
eval "$(starship init bash)"

# Cargo
. "$HOME/.cargo/env"

# Package Manager Configuration
export UV_INDEX_URL='https://packagemanager.posit.co/pypi/latest/simple'
export PIP_INDEX_URL='https://packagemanager.posit.co/pypi/latest/simple'