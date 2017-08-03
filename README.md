# pyPIT
Treats raw PIT (passive integrated transponder) data to extract maximum distances of ascent and time to attempt of PIT tagged fish ascending a flume. It has been coded in a way to allow the user to handle application specific exceptions (e.g. fish "hiding" in undetectable zones). 

Here is what it outputs for each attempt:

maximum distances of ascent,
time to maximum distance,
attempt duration,
attempt number,
time from start of trial to first attempt,
time between successive attempts,
and a number of other useful attempt related data

It also populates the database with data related to each individual fish (species, fork length, weight, etc.) and trial related data (temp, flow rate, etc.).

Code is based on pandas, a high level database manipulation package for Python. So it runs extremely fast.

If you are interested in using this code to treat your PIT data of fish ascending/descending a flume, let me know and I will help you out.

