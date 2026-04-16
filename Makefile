PYTHON ?= python

.PHONY: install init run reset-data setup

# Install Python dependencies.
install:
	$(PYTHON) -m pip install -r backend/requirements.txt

# Create empty local data files in backend/data.
init:
	$(PYTHON) scripts/init_data.py

# Run the app locally.
run:
	$(PYTHON) run.py

# Reset local data files back to empty defaults.
reset-data:
	$(PYTHON) scripts/init_data.py

# First-time setup: install deps, initialize empty data, then run the app.
setup:
	$(PYTHON) -m pip install -r backend/requirements.txt
	$(PYTHON) scripts/init_data.py
	$(PYTHON) run.py
