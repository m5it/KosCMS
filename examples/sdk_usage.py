#!/usr/bin/env python3
"""
WebCMS Admin SDK Usage Examples

Demonstrates how to use the Python SDK for various operations
"""

from webcms.client import create_client, WebCMSAdminClient


def example_basic_usage():
    """Basic SDK usage example."""
    print("=" * 70)
    print("Example 1: Basic Usage")
    print("=" * 70)
    
    # Create client with username/password
    client = create_client(
        base_url='http://localhost:5000',
        username='admin',
        password='admin123'
    )
    
    # Get dashboard
    print("\nGetting dashboard...")
    response = client.get_dashboard()
    if response.success:
        print(f"Dashboard loaded: {len(response.data.get('widgets', []))} widgets")
    else:
        print(f"Error: {response.error}")


def example_user_management():
    """User management example."""
    print("\n" + "=" * 70)
    print("Example 2: User Management")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        api_key='your-api-key'
    )
    
    # List users
    print("\nListing users...")
    response = client.list_users(limit=10)
    if response.success:
        users = response.data.get('users', [])
        print(f"Found {len(users)} users")
        for user in users[:3]:  # Show first 3
            print(f"  - {user.get('username')} ({user.get('email')})")
    
    # Create user
    print("\nCreating user...")
    response = client.create_user(
        username='johndoe',
        email='john@example.com',
        password='securepass123',
        role='editor'
    )
    if response.success:
        print(f"User created: {response.data.get('id')}")
    else:
        print(f"Error: {response.error}")


def example_content_management():
    """Content management example."""
    print("\n" + "=" * 70)
    print("Example 3: Content Management")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        username='admin',
        password='admin123'
    )
    
    # Create page
    print("\nCreating page...")
    response = client.create_page(
        title='About Us',
        slug='about-us',
        content='<h1>About Our Company</h1><p>We are awesome!</p>',
        status='published',
        template='page.html'
    )
    if response.success:
        print(f"Page created: {response.data.get('id')}")
    
    # List pages
    print("\nListing pages...")
    response = client.list_pages()
    if response.success:
        pages = response.data.get('pages', [])
        print(f"Found {len(pages)} pages")
        for page in pages[:3]:
            print(f"  - {page.get('title')} ({page.get('status')})")
    
    # Create post
    print("\nCreating blog post...")
    response = client.create_post(
        title='Welcome to Our Blog',
        slug='welcome-post',
        content='# Welcome\\n\\nThis is our first post!',
        status='published',
        format='markdown'
    )
    if response.success:
        print(f"Post created: {response.data.get('id')}")


def example_settings_management():
    """Settings management example."""
    print("\n" + "=" * 70)
    print("Example 4: Settings Management")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        username='admin',
        password='admin123'
    )
    
    # Get current settings
    print("\nGetting settings...")
    response = client.get_settings()
    if response.success:
        settings = response.data.get('settings', {})
        print(f"Site name: {settings.get('site_name')}")
        print(f"Posts per page: {settings.get('posts_per_page')}")
    
    # Update settings
    print("\nUpdating settings...")
    response = client.update_settings(
        site_name='My Awesome Website',
        posts_per_page=20
    )
    if response.success:
        print("Settings updated successfully")


def example_cache_operations():
    """Cache operations example."""
    print("\n" + "=" * 70)
    print("Example 5: Cache Operations")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        api_key='your-api-key'
    )
    
    # Get cache stats
    print("\nGetting cache stats...")
    response = client.get_cache_stats()
    if response.success:
        print(f"Cache keys: {response.data.get('keys')}")
        print(f"Hit rate: {response.data.get('hit_rate', 0):.2%}")
    
    # Clear cache
    print("\nClearing cache...")
    response = client.clear_cache(pattern='*')
    if response.success:
        print("Cache cleared successfully")
    
    # Warm cache
    print("\nWarming cache...")
    response = client.warm_cache()
    if response.success:
        print("Cache warmed successfully")


def example_backup_operations():
    """Backup operations example."""
    print("\n" + "=" * 70)
    print("Example 6: Backup Operations")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        username='admin',
        password='admin123'
    )
    
    # List backups
    print("\nListing backups...")
    response = client.list_backups()
    if response.success:
        backups = response.data.get('backups', [])
        print(f"Found {len(backups)} backups")
        for backup in backups:
            print(f"  - {backup.get('name')} ({backup.get('status')})")
    
    # Create backup
    print("\nCreating backup...")
    response = client.create_backup(name="Manual Backup")
    if response.success:
        print(f"Backup created: {response.data.get('id')}")


def example_batch_operations():
    """Batch operations example."""
    print("\n" + "=" * 70)
    print("Example 7: Batch Operations")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        username='admin',
        password='admin123'
    )
    
    # Create multiple users
    print("\nCreating multiple users...")
    users_to_create = [
        {'username': 'user1', 'email': 'user1@example.com', 'password': 'pass123'},
        {'username': 'user2', 'email': 'user2@example.com', 'password': 'pass123'},\n        {'username': 'user3', 'email': 'user3@example.com', 'password': 'pass123'},
    ]
    
    created_users = []
    for user_data in users_to_create:
        response = client.create_user(**user_data)
        if response.success:
            created_users.append(response.data.get('id'))
            print(f"Created: {user_data['username']}")
    
    print(f"\nTotal users created: {len(created_users)}")


def example_error_handling():
    """Error handling example."""
    print("\n" + "=" * 70)
    print("Example 8: Error Handling")
    print("=" * 70)
    
    client = create_client(
        base_url='http://localhost:5000',
        username='admin',
        password='wrong-password'  # This will fail
    )
    
    # This should fail
    response = client.list_users()
    if not response.success:
        print(f"Expected error occurred:")
        print(f"  Status code: {response.status_code}")
        print(f"  Error: {response.error}")
        print("\nError handling works correctly!")


def run_all_examples():
    """Run all examples."""
    print("""\n╔══════════════════════════════════════════════════════════════════════╗
║           WebCMS Admin SDK Usage Examples                              ║
╚══════════════════════════════════════════════════════════════════════╝\n""")
    
    examples = [
        example_basic_usage,
        example_user_management,
        example_content_management,
        example_settings_management,
        example_cache_operations,
        example_backup_operations,
        example_batch_operations,
        example_error_handling,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == '__main__':
    run_all_examples()
