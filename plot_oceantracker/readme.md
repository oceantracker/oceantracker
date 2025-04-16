# Ocean tracker reading and plotting
_________________________________________

To enable future compatibility with using pip install, reading and plotting code has moved within the main ocean tracker folder.
Adjust imports as below.

## Reading  example

old - from read_oceantracker.python import load_output_files

new - from oceantracker.read_output.python import load_output_files

matlab scripts to read output are in dir ''oceantracker.oceantracker.read_output.matlab''

## Plotting example

old - from plot_oceantracker.plot_tracks import plot_tracks

new - from oceantracker.plot.plot_tracks import plot_tracks

