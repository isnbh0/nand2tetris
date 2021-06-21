#! /usr/bin/env python3

import glob
import os


dirs = ["Seven", "ConvertToBin", "Square", "Average", "Pong", "ComplexArrays"]

for d in dirs:
    for f in glob.glob(os.path.join(d, "*.vm")):
        print(f"Removing {f}.")
        os.remove(f)

    for f in glob.glob(os.path.join(d, "*.xml")):
        print(f"Removing {f}.")
        os.remove(f)

print("Done.")
