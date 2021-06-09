import argparse
import os
import re
import subprocess
import sys


def test_single_file(file_path):
    subprocess.run(
        ["python", "-c", "import sys; print(sys.executable)"],
        stdout=sys.stdout,
        check=True,
    )

    subprocess.run(
        ["python", "jackanalyzer.py", file_path], stdout=sys.stdout, check=True
    )

    expected_path = re.sub(r"\.jack$", r".xml", file_path)
    result_path = re.sub(r"\.jack$", r"out.xml", file_path)
    subprocess.run(
        ["../../tools/TextComparer.sh", expected_path, result_path],
        stdout=sys.stdout,
        check=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to jack file or directory")

    args = parser.parse_args()

    path = args.path

    if os.path.isdir(path):
        file_paths = [
            os.path.join(path, file)
            for file in os.listdir(path)
            if file.endswith(".jack")
        ]
        for file_path in file_paths:
            print(f"Processing {file_path}...")
            test_single_file(file_path=file_path)
    else:
        test_single_file(file_path=path)
