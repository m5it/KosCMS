"""
OAuth2 Integration

Google and GitHub OAuth2 authentication.
"""

import secrets
import urllib.parse
from typing import Dict, Optional, Tuple
import http.client


class OAuthManager:
    """OAuth2 provider integration."""
    
    def __init__(self):
        self.providers: Dict[str, Dict] = {}
    
    def register_provider(self, name: str, client_id: str,
                          client_secret: str,
                          authorize_url: str,
                          token_url: str,
                          userinfo_url: str,
                          scopes: list) -> None:
        """
        Register OAuth provider.
        
        Args:
            name: Provider name (google, github)
            client_id: OAuth client ID
            client_secret: OAuth client secret
            authorize_url: Authorization endpoint
            token_url: Token endpoint
            userinfo_url: User info endpoint
            scopes: Requested scopes
        """
        self.providers[name] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "authorize_url": authorize_url,
            "token_url": token_url,
            "userinfo_url": userinfo_url,
            "scopes": scopes
        }
    
    def get_authorization_url(self, provider: str,
                               redirect_uri: str,
                               state: Optional[str] = None) -> str:
        """
        Get OAuth authorization URL.
        
        Args:
            provider: Provider name
            redirect_uri: Callback URL
            state: CSRF protection state
        
        Returns:
            Authorization URL
        """
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = self.providers[provider]
        
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": config["client_id"],
            "redirect_uri": redirect_uri,
            "scope": " ".join(config["scopes"]),
            "response_type": "code",
            "state": state
        }
        
        return f"{config['authorize_url']}?{urllib.parse.urlencode(params)}"
    
    def exchange_code(self, provider: str, code: str,
                      redirect_uri: str) -> Optional[Dict]:
        """
        Exchange authorization code for tokens.
        
        Args:
            provider: Provider name
            code: Authorization code
            redirect_uri: Callback URL
        
        Returns:
            Token data or None
        """
        if provider not in self.providers:
            return None
        
        config = self.providers[provider]
        
        # Build token request
        data = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        # Make request to token endpoint
        # This is simplified - real implementation would use requests library
        try:
            parsed = urllib.parse.urlparse(config["token_url"])
            conn = http.client.HTTPSConnection(parsed.netloc)
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            body = urllib.parse.urlencode(data)
            conn.request("POST", parsed.path, body, headers)
            
            response = conn.getresponse()
            if response.status == 200:
                import json
                return json.loads(response.read().decode())
            
            return None
            
        except Exception:
            return None
    
    def get_user_info(self, provider: str, 
                      access_token: str) -> Optional[Dict]:
        """
        Get user info from provider.
        
        Args:
            provider: Provider name
            access_token: OAuth access token
        
        Returns:
            User info or None
        """
        if provider not in self.providers:
            return None
        
        config = self.providers[provider]
        
        try:
            parsed = urllib.parse.urlparse(config["userinfo_url"])
            conn = http.client.HTTPSConnection(parsed.netloc)
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            conn.request("GET", parsed.path, headers=headers)
            response = conn.getresponse()
            
            if response.status == 200:
                import json
                return json.loads(response.read().decode())
            
            return None
            
        except Exception:
            return None
    
    def register_google(self, client_id: str, client_secret: str) -> None:
        """Register Google OAuth."""
        self.register_provider(
            "google",
            client_id,
            client_secret,
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "https://www.googleapis.com/oauth2/v2/userinfo",
            ["openid", "email", "profile"]
        )
    
    def register_github(self, client_id: str, client_secret: str) -> None:
        """Register GitHub OAuth."""
        self.register_provider(
            "github",
            client_id,
            client_secret,
            "https://github.com/login/oauth/authorize",
            "https://github.com/login/oauth/access_token",
            "https://api.github.com/user",
            ["user:email"]
        )