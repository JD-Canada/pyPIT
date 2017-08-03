The header to each file should look like the following:
 0,0,"Start Time = 10-02-15 09:41:29"
Antenna, Tag number, Time

The footer should look like:
0,0,"End Time = 10-02-15 09:41:29"

or,

0,0,0 if TIRIS was not shut down correctly





File 151018A.txt had a bunch of gibirish for the tag number over about 50 or so entries, I got rid of these lines and kept the good ones.

File 151018B.txt was all gibirish, and so I got rid of it from this list.

File 151019A.txt also had gibirish, which was removed

File 151020A.txt had numerous start and end times printed at the end. They were all within a few minutes of each other, so I kept the last one.

File 15014A.txt had a "Start Time = XXX" instead of time for the enrtry right before the first entry for fish 9084. This was causing problems during data treatment (trying to substract from a string). So I got rid of it and replaced it by the time value 42291.504686000 (reasonably close to the next time registry).

File 151016B.txt was removed because it was only 4 minutes long and at the end of the day, pretty sure this was mistakenly started.

File 151004A.txt: the last entry of the script was 42281.000000 and I replaced it with 42281.6405270778 (just a bit larger than the preceeding value). Otherwise I was getting a negative residency time.

File 151017A.txt: the last entry was 42294.669, which I replaced by 42294.6695463559, otherwise the last time was lower than the previous registered time and was giving a negative residency time