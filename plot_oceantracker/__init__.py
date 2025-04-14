
from os import path
with open(path.join(path.dirname(__file__), 'readme.md')) as f:
    for line in f:
        print(line.strip())  # .strip() removes the newline character

raise ModuleNotFoundError(f'Module {path.basename(__file__)} has moved, see above for new module location')