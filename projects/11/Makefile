PROJECT_DIR = "/home/jhchoi/local/src/nand2tetris"
TOOLS_DIR = ${PROJECT_DIR}"/tools"

all: run

clean:
	python scripts/clean.py

compile_all:
	python scripts/compile_all.py

run: compile_all
	${TOOLS_DIR}"/VMEmulator.sh"
