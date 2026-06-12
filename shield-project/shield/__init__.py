"""
S.H.I.E.L.D. - Strategic Heuristic Intelligence for Logistics, Data & Operations

A personal operational intelligence platform for autonomous task execution,
research, analysis, and code generation.
"""

__version__ = "0.1.0"
__author__ = "Shield Project"
__description__ = "Strategic Heuristic Intelligence for Logistics, Data & Operations"

from shield.core.config import Config, ShieldConfig
from shield.core.logger import setup_logger, get_logger

__all__ = [
    "Config",
    "ShieldConfig",
    "setup_logger",
    "get_logger",
]
