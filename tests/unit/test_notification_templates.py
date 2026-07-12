#!/usr/bin/env python3
"""Unit tests for notification templates."""

from webcms.notifications.templates import TemplateEngine


def test_template_render():
    engine = TemplateEngine()
    engine.register("greeting", "Hello {{ name }}!")
    result = engine.render("greeting", {"name": "Alice"})
    assert result == "Hello Alice!"


def test_template_conditional():
    engine = TemplateEngine()
    engine.register("alert", "{% if urgent %}URGENT{% endif %}")
    assert engine.render("alert", {"urgent": True}) == "URGENT"
    assert engine.render("alert", {"urgent": False}) == ""


def test_default_templates():
    engine = TemplateEngine()
    engine.register_defaults()
    html = engine.render("welcome", {"username": "Bob"})
    assert "Welcome Bob" in html
