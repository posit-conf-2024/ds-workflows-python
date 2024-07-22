# wsdot

A Python package for interacting with the Washington State Department of Transportation's (WSDOT) traffic API: https://wsdot.wa.gov/traffic/api/.

## Package Development 101

### What are Python Packages?

- Python packages are collections of functions that you can re-use across multiple projects
- Packages can include Python code, and/or code from other languages like Rust or C++.
- Most commonly, packages are published to PyPI

### Python Packaging Tools

- There is a rich ecosystem of tools for developing Python packages
- My favourite tool is Poetry (https://python-poetry.org)
- We don’t have time to dive deep into building Python packages today, I would recommend this book as a starting point: https://py-pkgs.org

### Anatomy of a Python Package

```bash
.
├── ferrygodmother
│  ├── __init__.py
│  ├── client.py
│  └── data
│     ├── __init__.py
│     └── weather.py
├── poetry.lock
├── pyproject.toml
├── README.md
└── tests
   └── test_weather.py
```

### Deploying Python Packages

Posit Package Manager is a tool to host R and Python packages in your organization. With Posit Package Manager you can host in-house Python Packages that you only want to make available within your organization.

- https://posit.co/products/enterprise/package-manager/
- Uploading packages to Posit Package Manager: https://docs.posit.co/rspm/admin/getting-started/configuration/#quickstart-local-python
- Git backed deployment to Posit Package Manager: https://docs.posit.co/rspm/admin/getting-started/configuration/#quickstart-git-python

![Screenshot of Posit Package Manager](imgs/screenshot-of-ppm.png)