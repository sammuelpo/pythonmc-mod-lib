"""
PythonMC - Python library for controlling Minecraft nodes.

This library provides an API to communicate with the PythonMC mod
running in Minecraft, allowing Python scripts to control cameras,
audio players, and other nodes.
"""

import json
import sys
import uuid
import os
from typing import Any, Dict, Optional, List


class PythonMCBridge:
    """Bridge client for communicating with Java via stdin/stdout."""
    
    def __init__(self):
        self.bridge_enabled = os.environ.get("PYTHONMC_BRIDGE_ENABLED") == "1"
        
        if not self.bridge_enabled:
            print("Warning: PythonMC Bridge not enabled", file=sys.stderr)
    
    def send_command(self, command: str, params: Dict[str, Any]) -> Dict:
        """Send a command to Java and wait for response."""
        if not self.bridge_enabled:
            raise RuntimeError("Bridge is not enabled")
        
        request_id = str(uuid.uuid4())
        
        request = {
            "id": request_id,
            "command": command,
            "params": params
        }
        
        # Send to Java with BRIDGE: prefix
        message = "BRIDGE:" + json.dumps(request)
        print(message, flush=True)
        
        # Wait for response
        timeout = 100  # Maximum lines to read before timeout
        for _ in range(timeout):
            line = sys.stdin.readline().strip()
            if line.startswith("BRIDGE:"):
                response = json.loads(line[7:])  # Remove "BRIDGE:" prefix
                if response.get("id") == request_id:
                    if response.get("status") == "error":
                        raise Exception(f"Bridge error: {response.get('error', 'Unknown error')}")
                    return response.get("result", {})
        
        raise TimeoutError("No response from bridge")


class Engine:
    """Main Engine interface for PythonMC."""
    
    _bridge = PythonMCBridge()
    
    @classmethod
    def get_node(cls, node_name: str) -> 'Node':
        """
        Get a node by name.
        
        Args:
            node_name: Name of the node to get
            
        Returns:
            Node object
            
        Example:
            camera = Engine.get_node("MainCamera")
        """
        result = cls._bridge.send_command("get_node", {
            "node_name": node_name
        })
        
        # Create appropriate node wrapper based on type
        node_type = result.get("node_type")
        if node_type == "CameraNode" or node_type == "Camera3D":
            return CameraNode._from_result(result)
        elif node_type == "AudioPlayerNode" or node_type == "AudioPlayer":
            return AudioPlayerNode._from_result(result)
        else:
            return Node._from_result(result)
    
    @classmethod
    def create_node(cls, node_type: str, node_name: str, parent: str = "Root") -> 'Node':
        """
        Create a new node.
        
        Args:
            node_type: Type of node ("Camera3D", "AudioPlayer", etc.)
            node_name: Name for the new node
            parent: Parent node name (default: "Root")
            
        Returns:
            Created node object
            
        Example:
            audio = Engine.create_node("AudioPlayer", "BackgroundMusic")
        """
        result = cls._bridge.send_command("create_node", {
            "node_type": node_type,
            "node_name": node_name,
            "parent": parent
        })
        
        # Return appropriate wrapper
        if node_type in ["CameraNode", "Camera3D"]:
            return CameraNode(result["node_id"], node_name, node_type)
        elif node_type in ["AudioPlayerNode", "AudioPlayer"]:
            return AudioPlayerNode(result["node_id"], node_name, node_type)
        else:
            return Node(result["node_id"], node_name, node_type)
    
    @classmethod
    def list_nodes(cls) -> List[Dict[str, str]]:
        """
        List all nodes in the scene.
        
        Returns:
            List of dicts with node info
        """
        result = cls._bridge.send_command("list_nodes", {})
        return result if isinstance(result, list) else []


class Node:
    """Base node wrapper."""
    
    def __init__(self, node_id: str, name: str, node_type: str):
        self.node_id = node_id
        self.name = name
        self.node_type = node_type
        self._bridge = Engine._bridge
    
    @classmethod
    def _from_result(cls, result: Dict):
        """Create node from bridge result."""
        return cls(
            result["node_id"],
            result.get("node_name", ""),
            result["node_type"]
        )
    
    def set_property(self, property: str, value: Any):
        """
        Set a property value.
        
        Args:
            property: Property name
            value: Property value
        """
        self._bridge.send_command("set_property", {
            "node_id": self.node_id,
            "property": property,
            "value": value
        })
    
    def get_property(self, property: str) -> Any:
        """
        Get a property value.
        
        Args:
            property: Property name
            
        Returns:
            Property value
        """
        result = self._bridge.send_command("get_property", {
            "node_id": self.node_id,
            "property": property
        })
        return result.get("value")
    
    def call_method(self, method: str, *args):
        """
        Call a method on the node.
        
        Args:
            method: Method name
            *args: Method arguments
            
        Returns:
            Method result
        """
        return self._bridge.send_command("call_method", {
            "node_id": self.node_id,
            "method": method,
            "args": list(args)
        })
    
    def delete(self):
        """Delete this node."""
        self._bridge.send_command("delete_node", {
            "node_id": self.node_id
        })


class CameraNode(Node):
    """Camera node wrapper for controlling camera."""
    
    def move(self, x: float, y: float, z: float):
        """
        Move camera to position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate
            
        Example:
            camera.move(100, 70, 200)
        """
        self.set_property("position", [x, y, z])
    
    def rotate(self, yaw: float, pitch: float):
        """
        Rotate camera.
        
        Args:
            yaw: Yaw rotation (horizontal)
            pitch: Pitch rotation (vertical)
            
        Example:
            camera.rotate(45, -10)
        """
        self.set_property("rotation", [yaw, pitch])
    
    def set_fov(self, fov: float):
        """
        Set field of view.
        
        Args:
            fov: FOV value (typically 60-120)
        """
        self.set_property("fov", fov)
    
    def attach_to_player(self):
        """Attach camera to player."""
        self.call_method("attachToPlayer")
    
    def detach_from_player(self):
        """Detach camera from player."""
        self.call_method("detachFromPlayer")


class AudioPlayerNode(Node):
    """Audio player node wrapper for controlling sounds."""
    
    def play(self):
        """
        Play audio.
        
        Example:
            audio.play()
        """
        self.call_method("play")
    
    def stop(self):
        """Stop audio."""
        self.call_method("stop")
    
    def set_sound(self, sound_id: str):
        """
        Set sound ID.
        
        Args:
            sound_id: Minecraft sound ID (e.g. "minecraft:music.creative")
            
        Example:
            audio.set_sound("minecraft:music.creative")
        """
        self.set_property("soundId", sound_id)
    
    def set_volume(self, volume: float):
        """
        Set volume.
        
        Args:
            volume: Volume (0.0 to 4.0, default 1.0)
        """
        self.set_property("volume", volume)
    
    def set_pitch(self, pitch: float):
        """
        Set pitch.
        
        Args:
            pitch: Pitch (0.1 to 2.0, default 1.0)
        """
        self.set_property("pitch", pitch)
    
    def set_loop(self, loop: bool):
        """
        Set loop mode.
        
        Args:
            loop: True to loop, False to play once
        """
        self.set_property("loop", loop)
    
    def set_position(self, x: float, y: float, z: float):
        """
        Set 3D position of sound.
        
        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate
        """
        self.set_property("position", [x, y, z])


# Module-level convenience functions
def get_node(node_name: str) -> Node:
    """Get a node by name. Alias for Engine.get_node()."""
    return Engine.get_node(node_name)

def create_node(node_type: str, node_name: str, parent: str = "Root") -> Node:
    """Create a new node. Alias for Engine.create_node()."""
    return Engine.create_node(node_type, node_name, parent)

def list_nodes() -> List[Dict[str, str]]:
    """List all nodes. Alias for Engine.list_nodes()."""
    return Engine.list_nodes()


__all__ = [
    'Engine',
    'Node',
    'CameraNode',
    'AudioPlayerNode',
    'get_node',
    'create_node',
    'list_nodes',
]
