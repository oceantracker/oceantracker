# Minimal makefile for Sphinx documentation

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?= --keep-going
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile clean clean-all build-params convert-notebooks linkcheck

# Clean build directory
clean:
	rm -rf $(BUILDDIR)

# Clean everything including generated parameter docs
clean-all: clean
	rm -rf documentation/api_ref/*.rst
	rm -rf getting_started/how_to/*.rst
	rm -rf getting_started/how_to/*_files

# Build parameter reference documentation
build-params:
	python build_parameter_ref.py

# Convert Jupyter notebooks to RST
convert-notebooks:
	@echo "Converting Jupyter notebooks to RST..."
	@cd ../tutorials_how_to && \
	for notebook in *.ipynb; do \
		if [ -f "$$notebook" ]; then \
			echo "Converting $$notebook..."; \
			jupyter nbconvert "$$notebook" --to rst; \
			base_name=$${notebook%.ipynb}; \
			if [ -f "$${base_name}.rst" ]; then \
				mv "$${base_name}.rst" ../docs/getting_started/how_to; \
			fi; \
			if [ -d "$${base_name}_files" ]; then \
				mv "$${base_name}_files" ../docs/getting_started/how_to; \
			fi; \
		fi; \
	done

# Build documentation with all preprocessing steps
build: clean clean-all build-params convert-notebooks html
	@echo "Documentation build complete!"

# Check for broken links
linkcheck:
	@$(SPHINXBUILD) -b linkcheck "$(SOURCEDIR)" "$(BUILDDIR)/linkcheck" $(SPHINXOPTS) $(O)
	@echo
	@echo "Link check complete; look for any errors in $(BUILDDIR)/linkcheck/output.txt."

# Build API documentation
# apidoc:
# 	sphinx-apidoc -o api ../oceantracker --force --separate --module-first

# Quick build without regenerating everything
quick: html
	@echo "Quick build complete!"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option. $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)