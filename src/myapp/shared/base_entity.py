"""Базова абстракція Entity — об'єкт з ідентичністю (id), що зберігається
протягом усього життєвого циклу об'єкта, незалежно від зміни інших атрибутів.
"""
from __future__ import annotations

from abc import ABC


class Entity(ABC):
    id: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        if type(self) is not type(other):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
