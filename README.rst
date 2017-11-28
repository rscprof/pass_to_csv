export from pass to csv 
=======================

This simple project generate CSV-formatted text that is outputted to stdout
from `pass's <http://passwordstore.org/>` storage.

Usage: pass_to_csv [-h] [-v] -6 General -7 Pass -u substr1 -u substr2 -p prefix1 -p prefix2 >passwords.csv 

In column6 and column7 program writes strings after options -6 and -7. Also if the substr is a part of name then it will
taking as username. If also the directory was prefix1, prefix2 or so on so group name will change on prefix1, prefix2.

This program works only with storage in ~/.password-store directory.



