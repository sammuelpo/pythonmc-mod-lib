"""
PythonMC - Python library for Minecraft mod integration

This package allows Python scripts to control Minecraft through
the PythonMC mod's bridge system.
"""

from .pythonmc import (
    Engine,
    Node,
    CameraNode,
    AudioPlayerNode,
    get_node,
    create_node,
    list_nodes
)

from .__version__ import __version__, __author__

__all__ = [
    'Engine',
    'Node', 
    'CameraNode',
    'AudioPlayerNode',
    'get_node',
    'create_node',
    'list_nodes',
    '__version__',
    '__author__'
]
