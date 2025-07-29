from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Document:
    """Core Document entity"""
    id: str
    title: str
    text: str
    version: int
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self):
        """Convert document to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'version': self.version,
            'created_at': self.created_at.isoformat() + 'Z',
            'updated_at': self.updated_at.isoformat() + 'Z'
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create document from dictionary"""
        return cls(
            id=data['id'],
            title=data['title'],
            text=data['text'],
            version=data['version'],
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', ''))
        ) 