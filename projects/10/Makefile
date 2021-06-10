all: test clean

clean:
	python scripts/clean.py

test:
	python test_analyzer.py ExpressionLessSquare
	@echo
	python test_analyzer.py ArrayTest
	@echo
	python test_analyzer.py Square
	@echo

