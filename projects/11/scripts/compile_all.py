#! /usr/bin/env python3

import sys
import subprocess


dirs = ["Seven", "ConvertToBin", "Square", "Average", "Pong", "ComplexArrays"]

for d in dirs:
    subprocess.run(["python", "jack_compiler.py", d], stdout=sys.stdout, check=True)

print("Done.")
