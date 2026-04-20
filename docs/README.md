# Docs

Build the HTML documentation locally:

```bash
# Sync development dependencies (includes Sphinx, theme, and extensions)
uv sync --dev

# Build the HTML documentation using the uv-managed environment
uv run sphinx-build -b html docs docs/_build/html
```

Then open `docs/_build/html/index.html` in your browser.

The docs use the [furo](https://github.com/pradyunsg/furo) theme and
[sphinxcontrib-mermaid](https://github.com/mgaitan/sphinxcontrib-mermaid) for
architecture diagrams.
