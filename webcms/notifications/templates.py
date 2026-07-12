"""
Email template system with Jinja2-like syntax.
"""

import re
from typing import Dict


class TemplateEngine:
    """Simple template engine for notifications."""

    def __init__(self):
        self._templates: Dict[str, str] = {}

    def register(self, name: str, template: str):
        """Register a template."""
        self._templates[name] = template

    def render(self, name: str, context: Dict) -> str:
        """Render template with context variables."""
        template = self._templates.get(name)
        if not template:
            return f"[Template {name} not found]"

        result = template
        for key, value in context.items():
            result = result.replace(f"{{{{ {key} }}}}", str(value))

        # Simple conditionals
        result = re.sub(r"{% if (\w+) %}(.*?){% endif %}",
                        lambda m: m.group(2) if context.get(m.group(1)) else "",
                        result, flags=re.DOTALL)

        return result

    def register_defaults(self):
        """Register default email templates."""
        self.register("welcome", """
<h1>Welcome {{ username }}!</h1>
<p>Thank you for joining WebCMS.</p>
""")
        self.register("password_reset", """
<h1>Password Reset</h1>
<p>Click <a href="{{ reset_url }}">here</a> to reset your password.</p>
""")
        self.register("workflow_review", """
<h1>Review Requested</h1>
<p>{{ requester }} requested your review on {{ content_type }} "{{ title }}".</p>
""")
        self.register("daily_digest", """
<h1>Your Daily Digest</h1>
<ul>
  {% if pending_reviews %}<li>{{ pending_reviews }} pending reviews</li>{% endif %}
  {% if new_comments %}<li>{{ new_comments }} new comments</li>{% endif %}
  {% if published_posts %}<li>{{ published_posts }} posts published</li>{% endif %}
</ul>
""")
