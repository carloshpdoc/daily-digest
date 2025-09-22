VENV := venv
PYTHON := python3

.PHONY: install run clean

install:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate; \
		$(PYTHON) -m ensurepip --upgrade; \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -r requirements.txt

run:
	. $(VENV)/bin/activate; \
		$(PYTHON) daily_digest.py --date $${DATE}

clean:
	rm -rf $(VENV) __pycache__ *.pyc *.pyo
