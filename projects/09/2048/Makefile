PROJECT_DIR = "/home/jhchoi/local/src/nand2tetris"
TOOLS_DIR = ${PROJECT_DIR}"/tools"

default: compile

run: compile
	${TOOLS_DIR}"/VMEmulator.sh"

compile:
	pwd
	${TOOLS_DIR}"/JackCompiler.sh" .

clean:
	rm -f *.vm
