.PHONY: validate test release

validate:
	python scripts/validate_data.py

test:
	python -m unittest discover -s tests -v

release: validate test
	python scripts/generate_spreadsheet.py
