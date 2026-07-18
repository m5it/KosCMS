
"""
Setup script for WebCMS Admin Panel
"""

from setuptools import setup, find_packages

with open('README_ADMIN_PANEL.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='webcms-admin',
    version='1.3.29',
    description='WebCMS Admin Panel - A comprehensive CMS administration system',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='WebCMS Team',
    author_email='team@webcms.example.com',
    url='https://github.com/webcms/webcms',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'SQLAlchemy>=2.0.0',
        'psycopg2-binary>=2.9.0',
        'plyvel>=1.5.0',
        'redis>=4.6.0',
        'python-dotenv>=1.0.0',
        'bcrypt>=4.0.0',
        'cryptography>=41.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
        ],
        'prod': [
            'redis>=4.6.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'webcms-admin=webcms.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    python_requires='>=3.8',
    keywords='cms admin panel content management system',
    project_urls={
        'Documentation': 'https://webcms.readthedocs.io',
        'Source': 'https://github.com/webcms/webcms',
        'Tracker': 'https://github.com/webcms/webcms/issues',
    },
)
