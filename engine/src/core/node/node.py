# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

from abc import abstractmethod

from livekit import rtc
from pydantic import BaseModel

from core.secret import PublicSecret, SecretProvider

from ..pad import Pad, SinkPad, SourcePad


class NodeMetadata(BaseModel):
    primary: str
    secondary: str
    tags: list[str] = []


class Node:
    def __init__(
        self,
        *,
        secret_provider: SecretProvider,
        secrets: list[PublicSecret],
    ):
        self.room: rtc.Room
        self.id: str = "ERORR"
        self.pads: list[Pad] = []
        self.editor_position: tuple[float, float] = (0, 0)
        self.editor_dimensions: tuple[float, float] | None = None
        self.editor_name: str = "ERROR"
        self.secret_provider = secret_provider
        self.secrets = secrets
        # Display state for editor minimization
        self.display_state: str = "expanded"  # "expanded" | "minimized"

    @classmethod
    def get_type(cls) -> str:
        return cls.__name__

    @classmethod
    def get_description(cls) -> str:
        return f"Node of type {cls.__name__}"

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        """Get the metadata structure for this node type"""
        return NodeMetadata(primary="core", secondary="general", tags=["default"])

    @abstractmethod
    async def resolve_pads(self): ...

    @abstractmethod
    async def run(self):
        pass

    def get_pad(self, pad_id: str) -> Pad | None:
        for pad in self.pads:
            if pad.get_id() == pad_id:
                return pad
        return None

    def get_pad_required(self, pad_id: str) -> Pad:
        pad = self.get_pad(pad_id)
        if not pad:
            raise ValueError(f"Pad with id {pad_id} not found in node {self.id}")
        return pad

    def get_connected_nodes(self) -> list["Node"]:
        connected_nodes: dict[str, "Node"] = {}
        for pad in self.pads:
            if isinstance(pad, SinkPad):
                prev_pad = pad.get_previous_pad()
                if not prev_pad:
                    continue

                connected_nodes[prev_pad.get_owner_node().id] = (
                    prev_pad.get_owner_node()
                )
            elif isinstance(pad, SourcePad):
                for np in pad.get_next_pads():
                    connected_nodes[np.get_owner_node().id] = np.get_owner_node()

        return list(connected_nodes.values())

    def disconnect_all(self):
        try:
            for pad in self.pads:
                if isinstance(pad, SinkPad):
                    prev_pad = pad.get_previous_pad()
                    if not prev_pad:
                        continue
                    prev_pad.disconnect(pad)
                elif isinstance(pad, SourcePad):
                    for np in pad.get_next_pads():
                        pad.disconnect(np)
        except Exception as e:
            print(f"Error disconnecting pads for node {self.id}: {e}")

    def toggle_display_state(self):
        """Toggle between expanded and minimized display states"""
        if self.display_state == "expanded":
            self.display_state = "minimized"
        else:
            self.display_state = "expanded"

    def get_consolidated_pads(self) -> dict[str, list[str]]:
        """Get lists of pad IDs grouped by type for consolidated display"""
        sink_pads = []
        source_pads = []
        
        for pad in self.pads:
            if isinstance(pad, SinkPad):
                sink_pads.append(pad.get_id())
            elif isinstance(pad, SourcePad):
                source_pads.append(pad.get_id())
        
        return {
            "sink": sink_pads,
            "source": source_pads
        }
