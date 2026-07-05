"""
Template System Tests
"""

import pytest
from pathlib import Path

from webcms.templates.engine import TemplateEngine
from webcms.templates.theme import ThemeManager


def test_jinja_filters():
    """Test custom Jinja2 filters."""
    engine = TemplateEngine(["."])
    
    # Date format filter
    template = engine.env.from_string("{{ date|date_format('%Y') }}")
    result = template.render(date="2023-06-15")
    assert result == "2023"
    
    # Truncate filter
    template = engine.env.from_string("{{ text|truncate(10) }}")
    result = template.render(text="This is a very long text")
    assert result.endswith("...")


def test_markdown_filter():
    """Test markdown to HTML conversion."""
    engine = TemplateEngine(["."])
    
    template = engine.env.from_string("{{ text|markdown }}")
    result = template.render(text="# Heading")
    
    assert "<h1>Heading</h1>" in result


def test_theme_discovery(tmp_path):
    """Test theme discovery."""
    # Create mock theme
    themes_dir = tmp_path / "themes"
    theme_dir = themes_dir / "test-theme"
    theme_dir.mkdir(parents=True)
    
    # Create theme.yaml
    (theme_dir / "theme.yaml").write_text("""
name: test-theme
version: "1.0.0"
description: Test theme
author: Test
""")
    
    # Create templates dir
    (theme_dir / "templates").mkdir()
    
    manager = ThemeManager(themes_dir)
    
    theme = manager.get_theme("test-theme")
    assert theme is not None
    assert theme.name == "test-theme"
    assert theme.version == "1.0.0"


def test_theme_render():
    """Test theme rendering."""
    pass  # Would test full template rendering