"""
X-Ray Storage Backend - Manages persistence of decision trails
"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from .core import XRayContext


class XRayStorage:
    """
    Storage backend for X-Ray decision trails.
    Supports in-memory and file-based storage.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize storage backend.
        
        Args:
            storage_path: Optional path to directory for file storage.
                         If None, uses in-memory storage only.
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self._in_memory: Dict[str, Dict] = {}
        
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, context: XRayContext):
        """
        Save a decision trail.
        
        Args:
            context: XRayContext to save
        """
        trail = context.get_trail()
        execution_id = trail['execution_id']
        
        # Save to in-memory
        self._in_memory[execution_id] = trail
        
        # Save to file if storage path is configured
        if self.storage_path:
            file_path = self.storage_path / f"{execution_id}.json"
            with open(file_path, 'w') as f:
                json.dump(trail, f, indent=2, default=str)
    
    def get(self, execution_id: str) -> Optional[Dict]:
        """
        Retrieve a decision trail by execution ID.
        
        Args:
            execution_id: Unique identifier of the execution
            
        Returns:
            Decision trail dictionary or None if not found
        """
        # Try in-memory first
        if execution_id in self._in_memory:
            return self._in_memory[execution_id]
        
        # Try file storage
        if self.storage_path:
            file_path = self.storage_path / f"{execution_id}.json"
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
        
        return None
    
    def list_all(self, limit: Optional[int] = None) -> List[Dict]:
        """
        List all stored decision trails.
        
        Args:
            limit: Optional limit on number of trails to return
            
        Returns:
            List of decision trail dictionaries
        """
        trails = list(self._in_memory.values())
        
        # Also check file storage
        if self.storage_path:
            for file_path in self.storage_path.glob("*.json"):
                if file_path.stem not in self._in_memory:
                    try:
                        with open(file_path, 'r') as f:
                            trails.append(json.load(f))
                    except Exception:
                        continue
        
        # Sort by creation time (newest first)
        trails.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        if limit:
            trails = trails[:limit]
        
        return trails
    
    def clear(self):
        """Clear all stored trails (both in-memory and file-based)"""
        self._in_memory.clear()
        
        if self.storage_path:
            for file_path in self.storage_path.glob("*.json"):
                file_path.unlink()


# Global storage instance
_default_storage: Optional[XRayStorage] = None


def get_storage() -> XRayStorage:
    """Get the global storage instance, creating it if necessary"""
    global _default_storage
    if _default_storage is None:
        _default_storage = XRayStorage()
    return _default_storage


def set_storage(storage: XRayStorage):
    """Set the global storage instance"""
    global _default_storage
    _default_storage = storage

