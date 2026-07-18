"""
Internationalization (i18n) Support

Provides multi-language support for WebCMS Admin Panel
"""

import json
import os
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class Translation:
    """Translation entry."""
    key: str
    value: str
    language: str
    context: Optional[str] = None


class I18nManager:
    """Internationalization manager."""
    
    def __init__(self, default_language: str = 'en', translations_dir: str = 'translations'):
        self.default_language = default_language
        self.translations_dir = translations_dir
        self._translations: Dict[str, Dict[str, str]] = {}
        self._available_languages: List[str] = []
        
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files."""
        if not os.path.exists(self.translations_dir):
            os.makedirs(self.translations_dir)
            self._create_default_translations()
        
        for filename in os.listdir(self.translations_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]  # Remove .json
                filepath = os.path.join(self.translations_dir, filename)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self._translations[lang_code] = json.load(f)
                        self._available_languages.append(lang_code)
                except Exception:
                    pass
    
    def _create_default_translations(self):
        """Create default English translations."""
        default_translations = {
            "app.name": "WebCMS Admin",
            "app.tagline": "Content Management System",
            
            # Common
            "common.save": "Save",
            "common.cancel": "Cancel",
            "common.delete": "Delete",
            "common.edit": "Edit",
            "common.create": "Create",
            "common.search": "Search",
            "common.filter": "Filter",
            "common.loading": "Loading...",
            "common.error": "Error",
            "common.success": "Success",
            "common.warning": "Warning",
            "common.confirm": "Confirm",
            "common.close": "Close",
            "common.back": "Back",
            "common.next": "Next",
            "common.previous": "Previous",
            "common.submit": "Submit",
            "common.reset": "Reset",
            
            # Navigation
            "nav.dashboard": "Dashboard",
            "nav.content": "Content",
            "nav.pages": "Pages",
            "nav.posts": "Posts",
            "nav.media": "Media",
            "nav.users": "Users",
            "nav.roles": "Roles",
            "nav.settings": "Settings",
            "nav.plugins": "Plugins",
            "nav.themes": "Themes",
            "nav.backups": "Backups",
            "nav.cache": "Cache",
            "nav.analytics": "Analytics",
            
            # User management
            "user.username": "Username",
            "user.email": "Email",
            "user.password": "Password",
            "user.role": "Role",
            "user.active": "Active",
            "user.created": "Created",
            "user.last_login": "Last Login",
            "user.actions": "Actions",
            "user.add_new": "Add New User",
            "user.edit": "Edit User",
            "user.delete_confirm": "Are you sure you want to delete this user?",
            
            # Content
            "content.title": "Title",
            "content.slug": "Slug",
            "content.status": "Status",
            "content.published": "Published",
            "content.draft": "Draft",
            "content.archived": "Archived",
            "content.author": "Author",
            "content.created_at": "Created At",
            "content.updated_at": "Updated At",
            "content.content": "Content",
            "content.excerpt": "Excerpt",
            "content.tags": "Tags",
            "content.category": "Category",
            
            # Settings
            "settings.general": "General Settings",
            "settings.site_name": "Site Name",
            "settings.site_url": "Site URL",
            "settings.admin_email": "Admin Email",
            "settings.language": "Language",
            "settings.timezone": "Timezone",
            "settings.permalink": "Permalink Structure",
            "settings.posts_per_page": "Posts Per Page",
            
            # Errors
            "error.not_found": "Not found",
            "error.unauthorized": "Unauthorized",
            "error.forbidden": "Forbidden",
            "error.validation": "Validation error",
            "error.server": "Server error",
            "error.required": "This field is required",
            "error.invalid_email": "Invalid email address",
            "error.invalid_slug": "Invalid slug format",
            
            # Success messages
            "success.created": "Created successfully",
            "success.updated": "Updated successfully",
            "success.deleted": "Deleted successfully",
            "success.saved": "Saved successfully",
            "success.backup_created": "Backup created successfully",
            "success.cache_cleared": "Cache cleared successfully",
        }
        
        filepath = os.path.join(self.translations_dir, 'en.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(default_translations, f, indent=2, ensure_ascii=False)
        
        self._translations['en'] = default_translations
        self._available_languages.append('en')
    
    def translate(self, key: str, language: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key to the specified language.
        
        Args:
            key: Translation key
            language: Target language (default: default_language)
            **kwargs: Variables for interpolation
        
        Returns:
            Translated string
        """
        lang = language or self.default_language
        
        # Get translation
        translation = self._translations.get(lang, {}).get(key)
        
        # Fallback to default language
        if translation is None and lang != self.default_language:
            translation = self._translations.get(self.default_language, {}).get(key)
        
        # Fallback to key itself
        if translation is None:
            translation = key
        
        # Interpolate variables
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return translation
    
    def t(self, key: str, **kwargs) -> str:
        """Shorthand for translate."""
        return self.translate(key, **kwargs)
    
    def add_translation(self, language: str, key: str, value: str):
        """
        Add or update a translation.
        
        Args:
            language: Language code
            key: Translation key
            value: Translated value
        """
        if language not in self._translations:
            self._translations[language] = {}
            self._available_languages.append(language)
        
        self._translations[language][key] = value
        
        # Save to file
        self._save_language(language)
    
    def _save_language(self, language: str):
        """Save language translations to file."""
        filepath = os.path.join(self.translations_dir, f'{language}.json')
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._translations[language], f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    def get_available_languages(self) -> List[str]:
        """Get list of available languages."""
        return self._available_languages.copy()
    
    def get_translations(self, language: str) -> Dict[str, str]:
        """Get all translations for a language."""
        return self._translations.get(language, {}).copy()
    
    def import_translations(self, language: str, translations: Dict[str, str]):
        """
        Import multiple translations.
        
        Args:
            language: Language code
            translations: Dictionary of key-value pairs
        """
        if language not in self._translations:
            self._translations[language] = {}
            self._available_languages.append(language)
        
        self._translations[language].update(translations)
        self._save_language(language)
    
    def export_translations(self, language: str) -> Dict[str, str]:
        """Export translations for a language."""
        return self.get_translations(language)
    
    def get_missing_translations(self, language: str) -> List[str]:
        """
        Get list of keys missing translations.
        
        Args:
            language: Language code
        
        Returns:
            List of missing keys
        """
        if language == self.default_language:
            return []
        
        default_keys = set(self._translations.get(self.default_language, {}).keys())
        lang_keys = set(self._translations.get(language, {}).keys())
        
        return list(default_keys - lang_keys)
    
    def get_translation_coverage(self, language: str) -> float:
        """
        Get translation coverage percentage.
        
        Args:
            language: Language code
        
        Returns:
            Coverage percentage (0-100)
        """
        if language == self.default_language:
            return 100.0
        
        default_count = len(self._translations.get(self.default_language, {}))
        lang_count = len(self._translations.get(language, {}))
        
        if default_count == 0:
            return 0.0
        
        return (lang_count / default_count) * 100


# Global instance
i18n = I18nManager()


def translate(key: str, language: Optional[str] = None, **kwargs) -> str:
    """Global translate function."""
    return i18n.translate(key, language, **kwargs)


def t(key: str, **kwargs) -> str:
    """Global shorthand translate function."""
    return i18n.t(key, **kwargs)


# Export
__all__ = [
    'I18nManager',
    'i18n',
    'translate',
    't',
    'Translation'
]
