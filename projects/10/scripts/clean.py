#! /usr/bin/env python3

import glob
import os


# dirs = [d for d in os.listdir(os.getcwd()) if os.path.isdir(d) and re.match(r"[A-Z]", d)]
dirs = ["ExpressionLessSquare", "ArrayTest", "Square"]

for d in dirs:
    for f in glob.glob(os.path.join(d, "*out.xml")):
        print(f"Removing {f}.")
        os.remove(f)

print("Done.")

