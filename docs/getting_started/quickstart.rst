Beginners guide
===================

Before you start, take a look at the :doc:`about </overview/about>`,:doc:`features </documentation/features>`, and :doc:`gallery </overview/gallery>` section to make sure that this is the right tool for the job.
If you are unfamiliar with the topic of Lagrangian particle tracker, it is probably a good idea to take a look at `this paper <https://doi.org/10.31223/X5WM6Z>`_ first.
Here we give a brief overview of the approach and the model.
You'll also find some studies mentioned that applied our model.

When you would like to use our model you will need to know a bit of python. 
For a refresher take a look at a `python tutorial <https://docs.python.org/3/tutorial/>`_.

Assuming that you already installed python, the next step is to install oceantracker.
The easiest way is to simply use pythons integrated package manager `pip <https://pip.pypa.io/en/stable/getting-started/>`_.
However, we highly recommend using some sort of virtual environment tool.
The most common ones seem to be `conda <https://docs.conda.io/en/latest/>`_ or even better `mamba <https://mamba.readthedocs.io/en/latest/index.html>`_.
This will prevent all sorts of problems further down the line, making sure that you are not running into dependency conflicts between your projects and makes your study easier to reproduce.
For more details on how to install OceanTracker, see :doc:`installation </getting_started/installing>`.

Once you have successfully installed OceanTracker, we recommend to go through the :doc:`tutorials </getting_started/how_to>` to make yourself familiar with the model.

As is usually the case when programming, there are many ways of getting it wrong and only one to get it right.
We recommend for new users to take one of the tutorial models and slowly modify them, running the model after each modification while keeping an eye on the screen outputs and warnings, tweaking the model iteratively until it fits your application.
The first step being generally to swap the demo hindcasts for your own.
Make sure you understand your hindcasts to know what to expect from oceantrackers model output.
Open it separately using e.g. either the `xarray <https://docs.xarray.dev/en/stable/getting-started-guide/quick-overview.html>`_ or the netCDF4 package to examine the variables and to plot some maps.
Next, you'd need to find appropriate release locations for your model.
After that you are generally on your own. Good luck!

Feel free to reach out if you need help, and if you want to do us a favor, report bugs so we can smooth out the edges.