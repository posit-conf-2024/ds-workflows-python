# Virtual Environments and UV

Learn how to use virtual environments with `python -m venv .venv` and `uv` for faster package installation and virtual environment creation.

## Background

Every content that you publish to Posit Connect should have its own virtual environment. This will allow us to define the minimum required dependencies that Connect will need to re-run this notebook. We have already define the dependencies in the `requirements.in` file.
cat requirements.in

## Virtual environments with venv

Create and activate a virtual environment with the following commands:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Update pip and "friends"
python -m pip install --upgrade pip wheel setuptools

# Install all of the requirements
python -m pip install -r requirements.in

# Capture all of the dependencies, including the transitive dependencies.
python -m pip freeze > requirements.txt
```

Why do I use a `requirements.in` and a `requirements.txt`?

- `requirements.in` is for humans. I create and maintain this file by hand. I use it to define the top level dependencies I want to bring into my project.
- `requirements.txt` is for machines. I use this file to capture all of the dependencies, including the transitive dependencies. Posit Connect will use this file to install the dependencies.

## Virtual environments with uv

In 2024 an exciting new project called `uv` was released: https://github.com/astral-sh/uv.

> An extremely fast Python package installer and resolver, written in Rust. Designed as a drop-in replacement for common pip and pip-tools workflows.

Install `uv`:

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows.
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

I have started to adapt `uv` in my projects to replace pip because it is much faster, and has some features that are important to me (like syncing the `requirements.in` and `requirements.txt` files).

First, deactivate and delete your existing virtual environment:

```bash
deactivate
rm -rf .venv
rm requirements.txt
```

Then, recreate it using `uv`:

```bash
# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Capture all of the dependencies, including the transitive dependencies.
uv pip compile requirements.in --output-file requirements.txt

# Install all of the requirements
pip sync requirements.txt
```

In my daily workflow I use these two aliases everyday!

```bash
alias uvinit='uv venv && source .venv/bin/activate'
alias uvsync='uv pip compile requirements.in --quiet --output-file requirements.txt && uv pip sync requirements.txt'
```

For more information on how I use `uv` check out this blog post: <https://samedwardes.com/blog/2024-04-21-python-uv-workflow/>.