
#!/usr/bin/env python3
"""
WebCMS Security Audit Script

Performs security checks and hardening recommendations
"""

import os
import sys
import json
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SecurityAuditor:
    """Security audit for WebCMS."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def check_environment_variables(self):
        """Check critical environment variables."""
        critical_vars = [
            'JWT_SECRET_KEY',
            'ADMIN_API_KEY',
            'DATABASE_URL',
        ]
        
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                self.issues.append(f"Missing environment variable: {var}")
            elif len(value) < 32:
                self.warnings.append(f"{var} is too short (should be 32+ chars)")
            elif 'default' in value.lower() or 'change' in value.lower():
                self.warnings.append(f"{var} appears to be using default value")
            else:
                self.passed.append(f"{var} is set securely")
    
    def check_file_permissions(self):
        """Check file permissions."""
        sensitive_files = [
            '.env',
            'config.py',
            'data/webcms.db',
        ]
        
        for filepath in sensitive_files:
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                mode = oct(stat.st_mode)[-3:]
                
                if filepath.endswith('.db') or filepath.startswith('data/'):
                    if mode != '600':
                        self.warnings.append(f"{filepath} has permissions {mode}, should be 600")
                    else:
                        self.passed.append(f"{filepath} has correct permissions")
                else:
                    if mode != '644':
                        self.warnings.append(f"{filepath} has permissions {mode}, should be 644")
                    else:
                        self.passed.append(f"{filepath} has correct permissions")
    
    def check_ssl_configuration(self):
        """Check SSL configuration."""
        ssl_files = [
            'ssl/cert.pem',
            'ssl/key.pem',
        ]
        
        has_ssl = all(os.path.exists(f) for f in ssl_files)
        
        if has_ssl:
            self.passed.append("SSL certificates are present")
            
            # Check if self-signed
            with open('ssl/cert.pem', 'r') as f:
                cert_content = f.read()
                if 'localhost' in cert_content:
                    self.warnings.append("SSL certificate appears to be self-signed")
        else:
            self.issues.append("SSL certificates are missing")
    
    def check_dependencies(self):
        """Check for outdated or vulnerable dependencies."""
        try:
            import subprocess
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                if len(outdated) > 5:
                    self.warnings.append(f"{len(outdated)} dependencies are outdated")
                else:
                    self.passed.append("Dependencies are up to date")
        except Exception:
            self.warnings.append("Could not check dependency versions")
    
    def check_debug_mode(self):
        """Check if debug mode is disabled."""
        debug = os.getenv('FLASK_DEBUG', '').lower()
        env = os.getenv('FLASK_ENV', '').lower()
        
        if debug == 'true' or debug == '1':
            self.issues.append("FLASK_DEBUG is enabled - disable in production")
        elif env == 'development':
            self.warnings.append("FLASK_ENV is set to development")
        else:
            self.passed.append("Debug mode is properly disabled")
    
    def check_rate_limiting(self):
        """Check rate limiting configuration."""
        from webcms.admin.rate_limiter import rate_limiter
        
        if rate_limiter.enabled:
            self.passed.append("Rate limiting is enabled")
        else:
            self.warnings.append("Rate limiting is disabled")
    
    def generate_report(self):
        """Generate security audit report."""
        print("=" * 60)
        print("WebCMS Security Audit Report")
        print("=" * 60)
        
        print(f"\n✓ Passed: {len(self.passed)}")
        for item in self.passed:
            print(f"  ✓ {item}")
        
        print(f"\n⚠ Warnings: {len(self.warnings)}")
        for item in self.warnings:
            print(f"  ⚠ {item}")
        
        print(f"\n✗ Issues: {len(self.issues)}")
        for item in self.issues:
            print(f"  ✗ {item}")
        
        print("\n" + "=" * 60)
        if not self.issues:
            print("✓ Security audit passed")
            return 0
        else:
            print("✗ Security audit failed - fix critical issues")
            return 1


def main():
    """Run security audit."""
    auditor = SecurityAuditor()
    
    print("Running security checks...")
    
    auditor.check_environment_variables()
    auditor.check_file_permissions()
    auditor.check_ssl_configuration()
    auditor.check_dependencies()
    auditor.check_debug_mode()
    
    try:
        auditor.check_rate_limiting()
    except Exception as e:
        auditor.warnings.append(f"Could not check rate limiting: {e}")
    
    return auditor.generate_report()


if __name__ == '__main__':
    sys.exit(main())
