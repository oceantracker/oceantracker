#!/usr/bin/env python3
"""
Generate conda environment.yml files from pyproject.toml dependencies.
"""

import tomllib
from pathlib import Path
import yaml

def load_pyproject():
    """Load pyproject.toml file."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)

def generate_base_environment(pyproject_data, name="oceantracker"):
    """Generate base environment.yml for users."""
    project = pyproject_data["project"]
    
    # Extract Python version requirement
    python_req = project["requires-python"]
    # Convert ">=3.10,<3.12" to ">=3.10,<3.12"
    python_spec = f"python{python_req}"
    
    env = {
        "name": name,
        "channels": ["conda-forge", "defaults"],
        "dependencies": [
            python_spec,
            *project["dependencies"],
            "pip",
            {"pip": ["-e ."]}
        ]
    }
    
    return env

def generate_dev_environment(pyproject_data, name="oceantracker-dev"):
    """Generate development environment.yml."""
    project = pyproject_data["project"]
    
    # Extract Python version requirement
    python_req = project["requires-python"]
    python_spec = f"python{python_req}"
    
    # Combine all optional dependencies
    all_optional_deps = []
    for deps in project.get("optional-dependencies", {}).values():
        all_optional_deps.extend(deps)
    
    # Add some additional dev tools that work better from conda
    conda_dev_tools = [
        "jupyter",
        "jupyterlab", 
        "ipykernel",
        "ipywidgets",
        "git",
        "make"
    ]
    
    env = {
        "name": name,
        "channels": ["conda-forge", "defaults"],
        "dependencies": [
            python_spec,
            *project["dependencies"],
            *all_optional_deps,
            *conda_dev_tools,
            "pip",
            {"pip": ["-e ."]}
        ]
    }
    
    return env

def write_yaml_file(data, filepath):
    """Write environment data to YAML file."""
    with open(filepath, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    print(f"Generated: {filepath}")

def main():
    """Main function to generate environment files."""
    # Load pyproject.toml
    pyproject_data = load_pyproject()
    
    # Generate environment files
    base_env = generate_base_environment(pyproject_data)
    dev_env = generate_dev_environment(pyproject_data)
    
    # Write files
    root_dir = Path(__file__).parent.parent
    write_yaml_file(base_env, root_dir / "environment.yml")
    write_yaml_file(dev_env, root_dir / "environment-dev.yml")

if __name__ == "__main__":
    main()