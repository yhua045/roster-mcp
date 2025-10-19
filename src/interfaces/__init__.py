"""
Interfaces for roster management system.

This package contains abstract interfaces following SOLID principles,
particularly Dependency Inversion and Interface Segregation.
"""

from .role_history_manager import IRoleHistoryManager, IStorageAdapter
from .availability_evaluator import IAvailabilityEvaluator, IAvailabilityDataSource
from .roster_analyzer import IRosterAnalyzer, IAIProvider

__all__ = [
    'IRoleHistoryManager',
    'IStorageAdapter',
    'IAvailabilityEvaluator',
    'IAvailabilityDataSource',
    'IRosterAnalyzer',
    'IAIProvider',
]
