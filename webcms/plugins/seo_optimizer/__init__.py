"""
SEO Optimizer Plugin

Adds SEO meta tags and sitemap generation.
"""

from webcms.plugins import PluginBase, PluginConfig


class Plugin(PluginBase):
    """SEO Optimizer Plugin."""
    
    def __init__(self, config: PluginConfig):
        super().__init__(config)
        self.default_settings = {
            "site_title": "",
            "site_description": "",
            "enable_sitemap": True,
            "enable_robots": True
        }
    
    def register(self):
        """Register hooks."""
        self.register_hook("pre_render", self.inject_meta_tags)
        self.register_hook("post_save", self.update_sitemap)
    
    def activate(self):
        """Activate plugin."""
        return True
    
    def deactivate(self):
        """Deactivate plugin."""
        pass
    
    def inject_meta_tags(self, context, **kwargs):
        """Inject SEO meta tags into page context."""
        if isinstance(context, dict) and "page" in context:
            page = context["page"]
            
            # Generate meta description if not set
            if not page.get("meta_description"):
                content = page.get("content", "")
                # Strip HTML and truncate
                desc = content[:160].replace("<", "").replace(">", "")
                page["meta_description"] = desc
            
            # Open Graph tags
            page["og_title"] = page.get("meta_title") or page.get("title")
            page["og_description"] = page.get("meta_description")
        
        return context
    
    def update_sitemap(self, entity, **kwargs):
        """Regenerate sitemap on content change."""
        # Trigger sitemap regeneration
        pass
    
    def generate_sitemap(self):
        """Generate XML sitemap."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
</urlset>"""
    
    def generate_robots_txt(self):
        """Generate robots.txt."""
        return """User-agent: *
Allow: /
Sitemap: /sitemap.xml
"""