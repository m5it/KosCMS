"""
Asset Pipeline

CSS/JS minification and bundling.
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set


class AssetPipeline:
    """Asset pipeline for CSS/JS processing."""
    
    def __init__(self, static_dir: str, output_dir: str = "dist",
                 cache_enabled: bool = True):
        self.static_dir = Path(static_dir)
        self.output_dir = self.static_dir / output_dir
        self.cache_enabled = cache_enabled
        self._cache: Dict[str, str] = {}
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_css(self, files: List[str], bundle_name: str = "bundle") -> str:
        """
        Process and minify CSS files.
        
        Args:
            files: List of CSS file paths
            bundle_name: Output bundle name
        
        Returns:
            Path to processed CSS
        """
        combined = []
        
        for file_path in files:
            full_path = self.static_dir / file_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                    # Simple minification
                    content = self._minify_css(content)
                    combined.append(content)
        
        # Create bundle
        bundle_content = "\\n".join(combined)
        bundle_hash = hashlib.md5(bundle_content.encode()).hexdigest()[:8]
        output_name = f"{bundle_name}.{bundle_hash}.css"
        output_path = self.output_dir / output_name
        
        with open(output_path, 'w') as f:
            f.write(bundle_content)
        
        return f"dist/{output_name}"
    
    def process_js(self, files: List[str], bundle_name: str = "bundle") -> str:
        """
        Process and minify JS files.
        
        Args:
            files: List of JS file paths
            bundle_name: Output bundle name
        
        Returns:
            Path to processed JS
        """
        combined = []
        
        for file_path in files:
            full_path = self.static_dir / file_path
            if full_path.exists():
                with open(full_path, 'r') as f:
                    content = f.read()
                    # Simple minification
                    content = self._minify_js(content)
                    combined.append(content)
        
        # Create bundle
        bundle_content = ";\\n".join(combined)
        bundle_hash = hashlib.md5(bundle_content.encode()).hexdigest()[:8]
        output_name = f"{bundle_name}.{bundle_hash}.js"
        output_path = self.output_dir / output_name
        
        with open(output_path, 'w') as f:
            f.write(bundle_content)
        
        return f"dist/{output_name}"
    
    def _minify_css(self, css: str) -> str:
        """Simple CSS minification."""
        # Remove comments
        css = re.sub(r'/\\*.*?\\*/', '', css, flags=re.DOTALL)
        # Remove whitespace
        css = re.sub(r'\\s+', ' ', css)
        # Remove spaces around symbols
        css = re.sub(r'\\s*([{}:;,])\\s*', r'\\1', css)
        return css.strip()
    
    def _minify_js(self, js: str) -> str:
        """Simple JS minification."""
        # Remove single-line comments
        js = re.sub(r'//.*$', '', js, flags=re.MULTILINE)
        # Remove multi-line comments
        js = re.sub(r'/\\*.*?\\*/', '', js, flags=re.DOTALL)
        # Remove extra whitespace
        lines = [line.strip() for line in js.split('\\n')]
        js = '\\n'.join(line for line in lines if line)
        return js
    
    def get_asset_url(self, path: str, theme: Optional[str] = None) -> str:
        """
        Get asset URL with cache busting.
        
        Args:
            path: Asset path
            theme: Theme name
        
        Returns:
            URL with hash
        """
        if theme:
            full_path = self.static_dir / "themes" / theme / path
        else:
            full_path = self.static_dir / path
        
        if not full_path.exists():
            return path
        
        # Get file hash for cache busting
        mtime = full_path.stat().st_mtime
        file_hash = hashlib.md5(str(mtime).encode()).hexdigest()[:8]
        
        # Add hash to filename
        stem = full_path.stem
        suffix = full_path.suffix
        return f"{stem}.{file_hash}{suffix}"
    
    def clear_cache(self) -> None:
        """Clear asset cache."""
        self._cache.clear()
        
        # Remove old bundles
        for file in self.output_dir.glob("*"):
            if file.is_file():
                file.unlink()