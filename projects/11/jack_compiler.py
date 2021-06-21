import argparse
import os

from compiler.engine.vm_compilation_engine import VMCompilationEngine


"""top-level driver that sets up and invokes the other modules"""


def compile_single_file(file_path) -> str:
    """
    Returns the path that the compiled file was saved to.
    """

    engine = VMCompilationEngine(file_path=file_path)
    try:
        engine.compileClass()
    except Exception as e:
        raise (e)
    return engine.out_path_


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument("path", help="path to jack file")

    args = parser.parse_args()
    path = args.path

    if os.path.isdir(path):
        for file in (f for f in os.listdir(path) if f.endswith(".jack")):
            print(f"Compiling {os.path.join(path, file)}...", end=" ")
            out_path = compile_single_file(file_path=os.path.join(path, file))
            print(f"Saved to {out_path}.")
    else:
        out_path = compile_single_file(file_path=path)
        print(f"Saved to {out_path}.")
