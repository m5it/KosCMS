#!/usr/bin/env python3
"""Test admin dashboard widget system"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.admin.widgets import get_widget_registry


async def main():
    registry = get_widget_registry()
    widgets = await registry.render_all()
    print(f'Dashboard widgets: {len(widgets)}')
    for widget in widgets:
        print(f'  - {widget["title"]}: {widget["data"]}')


if __name__ == '__main__':
    asyncio.run(main())
