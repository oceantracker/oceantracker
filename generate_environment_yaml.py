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

def resolve_optional_dependencies(optional_deps, group_name, visited=None):
    """
    Recursively resolve optional dependencies, handling references to other groups.
    
    Args:
        optional_deps: Dict of all optional dependencies from pyproject.toml
        group_name: Name of the group to resolve
        visited: Set of already visited groups (to prevent circular references)
    
    Returns:
        List of resolved dependency strings
    """
    if visited is None:
        visited = set()
    
    if group_name in visited:
        return []
    
    visited.add(group_name)
    resolved = []
    
    for dep in optional_deps.get(group_name, []):
        # Check if this dependency is a reference to another optional group
        if dep in optional_deps:
            # Recursively resolve the referenced group
            resolved.extend(resolve_optional_dependencies(optional_deps, dep, visited))
        else:
            # It's an actual package dependency
            resolved.append(dep)
    
    return resolved

def generate_base_environment(pyproject_data, name="oceantracker"):
    """Generate base environment.yml for users."""
    project = pyproject_data["project"]
    
    # Extract Python version requirement
    python_req = project["requires-python"]
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
    
    # Get all optional dependencies
    optional_deps = project.get("optional-dependencies", {})
    
    # Resolve all optional dependencies (this handles nested references)
    all_optional_deps = []
    for group_name in optional_deps.keys():
        all_optional_deps.extend(resolve_optional_dependencies(optional_deps, group_name))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_optional_deps = []
    for dep in all_optional_deps:
        if dep not in seen:
            seen.add(dep)
            unique_optional_deps.append(dep)
    
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
            *unique_optional_deps,
            *conda_dev_tools,
            "pip",
            {"pip": ["-e .[dev]"]}
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