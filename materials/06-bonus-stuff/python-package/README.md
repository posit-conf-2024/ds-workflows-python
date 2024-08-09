# ferryland

A Python package for interacting with the Washington State Department of Transportation's (WSDOT) traffic API: https://wsdot.wa.gov/traffic/api/.

## Usage

```python
from datetime import date

from ferryland.ferryland import VesselsAPI


vessels_api = VesselsAPI()

vessel_accommodations = vessels_api.vessel_accommodations()
print(vessel_accommodations)

vessel_history = vessels_api.vessel_history(
    vessel_name="Spokane",
    date_start=date(2024, 1, 1),
    date_end=date(2024, 1, 7)
)
print(vessel_history)

vessel_verbose = vessels_api.vessel_verbose()
print(vessel_verbose)
```

## Package Development 101

### What are Python Packages?

- Python packages are collections of functions and other objects that you can re-use across multiple projects
- Packages can include Python code, and/or code from other languages like Rust or C++.
- Most commonly, packages are published to PyPI. In our example project we publish this package to our internal Posit Package Manager instance.

### Python Packaging Tools

- There is a rich ecosystem of tools for developing Python packages
- My favourite tool is Poetry (https://python-poetry.org)
- We don’t have time to dive deep into building Python packages today, I would recommend this book as a starting point: https://py-pkgs.org

### Deploying Python Packages to Posit Package Manager

Posit Package Manager is a tool to host R and Python packages in your organization. With Posit Package Manager you can host in-house Python Packages that you only want to make available within your organization.

- https://posit.co/products/enterprise/package-manager/
- Uploading packages to Posit Package Manager: https://docs.posit.co/rspm/admin/getting-started/configuration/#quickstart-local-python
- Git backed deployment to Posit Package Manager: https://docs.posit.co/rspm/admin/getting-started/configuration/#quickstart-git-python

![Screenshot of Posit Package Manager](imgs/screenshot-of-ppm.png)
