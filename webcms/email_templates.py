
"""
Email Template System

Provides customizable email templates with variable substitution
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TemplateType(Enum):
    """Email template types."""
    WELCOME = 'welcome'
    PASSWORD_RESET = 'password_reset'
    PASSWORD_CHANGED = 'password_changed'
    CONTENT_PUBLISHED = 'content_published'
    CONTENT_REVIEW = 'content_review'
    NOTIFICATION = 'notification'
    SYSTEM_ALERT = 'system_alert'
    NEWSLETTER = 'newsletter'


@dataclass
class EmailTemplate:
    """Email template."""
    id: str
    name: str
    template_type: TemplateType
    subject: str
    body_html: str
    body_text: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'template_type': self.template_type.value,
            'subject': self.subject,
            'body_html': self.body_html,
            'body_text': self.body_text,
            'variables': self.variables or [],
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class TemplateEngine:
    """Template rendering engine."""
    
    def __init__(self):
        self.variable_pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
        self.helpers = {
            'uppercase': lambda x: str(x).upper(),
            'lowercase': lambda x: str(x).lower(),
            'capitalize': lambda x: str(x).capitalize(),
            'date': lambda x, fmt='%Y-%m-%d': x.strftime(fmt) if hasattr(x, 'strftime') else str(x),
        }
    
    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Render template with variables.
        
        Args:
            template: Template string
            variables: Variable values
        
        Returns:
            Rendered string
        """
        def replace_var(match):
            var_name = match.group(1)
            
            # Check for helper syntax: var|helper
            if '|' in var_name:
                var_name, helper = var_name.split('|', 1)
                value = variables.get(var_name, '')
                if helper in self.helpers:
                    return self.helpers[helper](value)
                return str(value)
            
            value = variables.get(var_name, '')
            return str(value)
        
        return self.variable_pattern.sub(replace_var, template)
    
    def extract_variables(self, template: str) -> List[str]:
        """Extract variable names from template."""
        return list(set(self.variable_pattern.findall(template)))


class EmailTemplateManager:
    """Manages email templates."""
    
    def __init__(self, db=None):
        self.db = db
        self.engine = TemplateEngine()
        self._templates: Dict[str, EmailTemplate] = {}
        self._ensure_tables()
        self._load_default_templates()
    
    def _ensure_tables(self):
        """Ensure database tables exist."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            if 'email_templates' not in tables:
                self.db.execute("""
                    CREATE TABLE email_templates (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        template_type TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        body_html TEXT NOT NULL,
                        body_text TEXT,
                        variables TEXT,
                        is_active BOOLEAN DEFAULT 1,
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
        except Exception as e:
            print(f"Warning: Could not create email_templates table: {e}")
    
    def _load_default_templates(self):
        """Load default email templates."""
        from datetime import datetime
        
        defaults = [
            EmailTemplate(
                id='welcome_default',
                name='Welcome Email',
                template_type=TemplateType.WELCOME,
                subject='Welcome to {{ site_name }}, {{ username }}!',
                body_html='''
                <html>
                <body>
                    <h1>Welcome, {{ username }}!</h1>
                    <p>Thank you for joining {{ site_name }}.</p>
                    <p>Your account has been created successfully.</p>
                    <p><a href="{{ login_url }}">Login to your account</a></p>
                </body>
                </html>
                ''',
                body_text='Welcome {{ username }}! Thank you for joining {{ site_name }}. Login: {{ login_url }}',
                variables=['username', 'site_name', 'login_url'],
                created_at=datetime.utcnow().isoformat()
            ),
            EmailTemplate(
                id='password_reset_default',
                name='Password Reset',
                template_type=TemplateType.PASSWORD_RESET,
                subject='Password Reset Request',
                body_html='''
                <html>
                <body>
                    <h1>Password Reset</h1>
                    <p>Hello {{ username }},</p>
                    <p>You requested a password reset. Click the link below:</p>
                    <p><a href="{{ reset_url }}">Reset Password</a></p>
                    <p>This link expires in {{ expiry_hours }} hours.</p>
                </body>
                </html>
                ''',
                variables=['username', 'reset_url', 'expiry_hours'],
                created_at=datetime.utcnow().isoformat()
            ),
            EmailTemplate(
                id='content_published_default',
                name='Content Published',
                template_type=TemplateType.CONTENT_PUBLISHED,
                subject='Your content "{{ content_title }}" has been published',
                body_html='''
                <html>
                <body>
                    <h1>Content Published</h1>
                    <p>Hello {{ author_name }},</p>
                    <p>Your content "{{ content_title }}" has been published.</p>
                    <p>View it here: <a href="{{ content_url }}">{{ content_title }}</a></p>
                </body>
                </html>
                ''',
                variables=['author_name', 'content_title', 'content_url'],
                created_at=datetime.utcnow().isoformat()
            ),
        ]
        
        for template in defaults:
            self._templates[template.id] = template
    
    def create_template(self, name: str, template_type: TemplateType,
                       subject: str, body_html: str,
                       body_text: Optional[str] = None) -> EmailTemplate:
        """
        Create new template.
        
        Args:
            name: Template name
            template_type: Type of template
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body
        
        Returns:
            Created template
        """
        import uuid
        from datetime import datetime
        
        # Extract variables
        variables = list(set(
            self.engine.extract_variables(subject) +
            self.engine.extract_variables(body_html) +
            (self.engine.extract_variables(body_text) if body_text else [])
        ))
        
        template = EmailTemplate(
            id=str(uuid.uuid4()),
            name=name,
            template_type=template_type,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            variables=variables,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        self._templates[template.id] = template
        
        # Save to database
        if self.db:
            try:
                self.db.execute(f"""
                    INSERT INTO email_templates 
                    (id, name, template_type, subject, body_html, body_text, 
                     variables, is_active, created_at, updated_at)
                    VALUES (
                        '{template.id}',
                        '{name.replace("'", "''")}',
                        '{template_type.value}',
                        '{subject.replace("'", "''")}',
                        '{body_html.replace("'", "''")}',
                        '{(body_text or '').replace("'", "''")}',
                        '{json.dumps(variables)}',
                        1,
                        '{template.created_at}',
                        '{template.updated_at}'
                    )
                """)
            except Exception as e:
                print(f"Error saving template: {e}")
        
        return template
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get template by ID."""
        return self._templates.get(template_id)
    
    def get_templates(self, template_type: Optional[TemplateType] = None,
                     active_only: bool = True) -> List[EmailTemplate]:
        """Get all templates."""
        templates = list(self._templates.values())
        
        if template_type:
            templates = [t for t in templates if t.template_type == template_type]
        
        if active_only:
            templates = [t for t in templates if t.is_active]
        
        return templates
    
    def render_template(self, template_id: str, 
                       variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Render template with variables.
        
        Args:
            template_id: Template ID
            variables: Variable values
        
        Returns:
            Dictionary with subject, html, text or None
        """
        template = self.get_template(template_id)
        if not template:
            return None
        
        subject = self.engine.render(template.subject, variables)
        html = self.engine.render(template.body_html, variables)
        text = None
        if template.body_text:
            text = self.engine.render(template.body_text, variables)
        
        return {
            'subject': subject,
            'html': html,
            'text': text
        }
    
    def update_template(self, template_id: str, **kwargs) -> Optional[EmailTemplate]:
        """Update template."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        from datetime import datetime
        template.updated_at = datetime.utcnow().isoformat()
        
        return template
    
    def delete_template(self, template_id: str) -> bool:
        """Delete template."""
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    def preview_template(self, template_id: str) -> Optional[Dict[str, str]]:
        """Preview template with sample data."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        # Generate sample data
        sample_data = {var: f'[Sample {var}]' for var in (template.variables or [])}
        sample_data['site_name'] = 'WebCMS'
        sample_data['login_url'] = 'https://example.com/login'
        
        return self.render_template(template_id, sample_data)


# Global instance
template_manager = EmailTemplateManager()


def render_email(template_id: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Render email from template."""
    return template_manager.render_template(template_id, variables)


# Export
__all__ = [
    'TemplateType',
    'EmailTemplate',
    'TemplateEngine',
    'EmailTemplateManager',
    'template_manager',
    'render_email'
]
