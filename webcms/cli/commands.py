"""
CLI Commands

Management commands for WebCMS.
"""

import click
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@click.group()
def cli():
    """WebCMS Management CLI"""
    pass


@cli.command()
@click.option('--host', default='0.0.0.0', help='Bind host')
@click.option('--port', default=8000, help='Bind port')
@click.option('--debug', is_flag=True, help='Debug mode')
def serve(host, port, debug):
    """Run development server."""
    from webcms.app_factory import create_app
    
    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
def init():
    """Initialize database."""
    from webcms.app_factory import create_app
    
    app = create_app()
    click.echo("Database initialized!")


@cli.command()
@click.argument('username')
@click.password_option()
def create_user(username, password):
    """Create admin user."""
    from webcms.app_factory import create_app
    from webcms.auth.password import PasswordHasher
    
    app = create_app()
    hasher = PasswordHasher()
    
    # Create user logic here
    click.echo(f"User {username} created!")


@cli.command()
def migrate():
    """Run database migrations."""
    from alembic import command
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    click.echo("Migrations complete!")


@cli.command()
@click.argument('name')
def create_plugin(name):
    """Create new plugin scaffold."""
    plugin_dir = Path(f"webcms/plugins/{name}")
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py
    (plugin_dir / "__init__.py").write_text(f'''"""
{name.title()} Plugin
"""

from webcms.plugins import PluginBase, PluginConfig


class Plugin(PluginBase):
    """{name.title()} Plugin Implementation."""
    
    def register(self):
        """Register hooks."""
        pass
    
    def activate(self):
        """Activate plugin."""
        return True
    
    def deactivate(self):
        """Deactivate plugin."""
        pass
''')
    
    # Create plugin.yaml
    (plugin_dir / "plugin.yaml").write_text(f'''name: {name}
version: "1.0.0"
description: "{name.title()} plugin"
author: "Your Name"
requires: []
permissions: []
''')
    
    click.echo(f"Plugin {name} created at {plugin_dir}")


@cli.command()
def shell():
    """Interactive shell."""
    import code
    from webcms.app_factory import create_app
    
    app = create_app()
    
    banner = """
    WebCMS Shell
    ============
    Available: app, db
    """
    
    code.interact(banner=banner, local={
        'app': app,
        'db': app.container.get('db')
    })


if __name__ == '__main__':
    cli()