import argparse
import os

from jackanalyzer import JackTokenizer


def tokenize_single_file(file_path):
    jt = JackTokenizer(file_path=file_path)

    out_path = file_path.replace(".jack", "T_out.xml")
    with open(out_path, "w") as f:
        f.write("<tokens>\n")
        while True:
            f.write(f"{jt}\n")
            if jt.hasMoreTokens:
                jt.advance()
            else:
                break
        f.write("</tokens>\n")
    print(f"Saved to {out_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to jack file")

    args = parser.parse_args()

    path = args.path

    if os.path.isdir(path):
        pass
    else:
        tokenize_single_file(file_path=path)
