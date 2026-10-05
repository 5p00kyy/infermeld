PYTHON ?= python3
NODE ?= node

.PHONY: test package preview

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(NODE) --test tests/*.test.mjs

package:
	$(PYTHON) tools/package.py

preview:
	$(PYTHON) -m http.server 8000 --bind 127.0.0.1 --directory site
