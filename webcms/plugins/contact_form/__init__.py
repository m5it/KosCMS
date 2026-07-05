"""
Contact Form Plugin

Sample plugin demonstrating the plugin API.
"""

from webcms.plugins import PluginBase, PluginConfig
from webcms.plugins.hooks import HookType


class Plugin(PluginBase):
    """Contact Form Plugin."""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.submissions = []
    
    def register(self):
        """Register hooks."""
        self.register_hook(HookType.PRE_RENDER, self.add_form_shortcode)
        self.register_hook("admin_menu", self.add_admin_menu)
    
    def activate(self):
        """Activate plugin."""
        print(f"Activating {self.config.name}")
        return True
    
    def deactivate(self):
        """Deactivate plugin."""
        print(f"Deactivating {self.config.name}")
    
    def add_form_shortcode(self, content, **kwargs):
        """Add contact form shortcode handler."""
        if "[contact_form]" in content:
            form_html = self._render_form()
            return content.replace("[contact_form]", form_html)
        return content
    
    def _render_form(self):
        """Render contact form HTML."""
        return """
        <form class="contact-form" action="/contact/submit" method="post">
            <div class="form-group">
                <label>Name</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" required>
            </div>
            <div class="form-group">
                <label>Message</label>
                <textarea name="message" rows="5" required></textarea>
            </div>
            <button type="submit">Send Message</button>
        </form>
        """
    
    def add_admin_menu(self, menu, **kwargs):
        """Add admin menu item."""
        menu.append({
            "label": "Contact Form",
            "url": "/admin/contact-form",
            "icon": "mail"
        })
        return menu
    
    def get_admin_routes(self):
        """Get admin routes."""
        return [
            {
                "path": "/admin/contact-form",
                "handler": self.admin_dashboard,
                "methods": ["GET"]
            },
            {
                "path": "/admin/contact-form/settings",
                "handler": self.admin_settings,
                "methods": ["GET", "POST"]
            }
        ]
    
    def admin_dashboard(self, request):
        """Admin dashboard view."""
        return {
            "template": "admin/contact_form/dashboard.html",
            "data": {
                "submissions": self.submissions,
                "count": len(self.submissions)
            }
        }
    
    def admin_settings(self, request):
        """Admin settings view."""
        return {
            "template": "admin/contact_form/settings.html",
            "data": {}
        }