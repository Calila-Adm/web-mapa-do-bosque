# Makefile for WBR Streamlit BigQuery Project

# Define the Python interpreter
PYTHON = python3

# Define the directories
SRC_DIR = src
TEST_DIR = tests

# Define the requirements file
REQUIREMENTS = requirements.txt

# Define the default target
.DEFAULT_GOAL := help

# Help command
help:
	@echo "Makefile commands:"
	@echo "  install      - Install the required Python packages"
	@echo "  run          - Run the Streamlit application"
	@echo "  test         - Run the tests"
	@echo "  clean        - Remove __pycache__ directories and .pyc files"

# Install required packages
install:
	$(PYTHON) -m pip install -r $(REQUIREMENTS)

# Run the Streamlit application
run:
	streamlit run $(SRC_DIR)/main.py

# Run the tests
test:
	pytest -q

# Clean up the project
clean:
	find . -type d -name '__pycache__' -exec rm -r {} +
	find . -type f -name '*.pyc' -exec rm -f {} +