# Writes oceantracker/_build_info.py stamping the release/build date into the package.
# Run before "python -m build" (done by "make build" and the publish workflow).
# The generated file is git-ignored; installs from source show a dev build instead.
from datetime import datetime, timezone
from os import path

build_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')

file_name = path.join(path.dirname(__file__), 'oceantracker', '_build_info.py')
with open(file_name, 'w') as f:
    f.write('# auto-generated at package build time by generate_build_info.py, do not edit or commit\n')
    f.write(f"build_date = '{build_date}'\n")

print(f'wrote {file_name}: build_date = {build_date}')
