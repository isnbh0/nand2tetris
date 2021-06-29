REPO_DIR = "/home/jhchoi/local/src/nand2tetris"
TOOLS_DIR = ${REPO_DIR}"/tools"
PROJECTS_DIR = ${REPO_DIR}"/projects"

default: compile

run: compile
	${TOOLS_DIR}"/VMEmulator.sh"

compile:
	pwd
	python ${PROJECTS_DIR}"/11/jack_compiler.py" .

clean:
	rm -f *.vm
