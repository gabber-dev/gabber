# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import logging
from abc import abstractmethod

from livekit import rtc

from ..secret import PublicSecret, SecretProvider
from typing import TYPE_CHECKING, Callable, TypeVar, cast

from ..pad import (
    Pad,
    SinkPad,
    SourcePad,
    PropertySourcePad,
    PropertySinkPad,
    StatelessSinkPad,
    StatelessSourcePad,
)
from ..editor.models import NodeMetadata, NodeNote
from ..types import runtime

if TYPE_CHECKING:
    from ..graph import Graph

T = TypeVar("T", bound=runtime.RuntimePadValue)


class Node:
    def __init__(
        self,
        *,
        graph: "Graph",
        secret_provider: SecretProvider,
        secrets: list[PublicSecret],
        logger: logging.Logger | logging.LoggerAdapter,
    ):
        self.graph: "Graph" = graph
        self.room: rtc.Room
        self.id: str = "ERORR"
        self.pads: list[Pad] = []
        self.editor_position: tuple[float, float] = (0, 0)
        self.editor_dimensions: tuple[float, float] | None = None
        self.editor_name: str = "ERROR"
        self.secret_provider = secret_provider
        self.secrets = secrets
        self._base_logger = logger
        self._logger: logging.LoggerAdapter | None = None

    @property
    def logger(self) -> logging.LoggerAdapter:
        if self._logger is None:
            self._logger = logging.LoggerAdapter(self._base_logger, {"node": self.id})
        return self._logger

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

    def get_notes(self) -> list[NodeNote]:
        return []

    @abstractmethod
    def resolve_pads(self): ...

    @abstractmethod
    async def run(self):
        pass

    def get_pad(self, pad_id: str) -> Pad | None:
        for pad in self.pads:
            if not pad:
                logging.error(f"Pad is None in node {self.id}")
                continue
            if pad.get_id() == pad_id:
                return pad
        return None

    def get_pad_required(self, pad_id: str) -> Pad:
        pad = self.get_pad(pad_id)
        if not pad:
            raise ValueError(f"Pad with id {pad_id} not found in node {self.id}")
        return pad

    def get_typed_pad(self, _: type[T], pad_id: str) -> Pad[T] | None:
        pad = self.get_pad(pad_id)
        return cast(Pad[T], pad)

    def get_property_source_pad(
        self, _: type[T], pad_id: str
    ) -> PropertySourcePad[T] | None:
        pad = self.get_pad(pad_id)
        assert isinstance(pad, PropertySourcePad)
        return cast(PropertySourcePad[T], pad)

    def get_property_sink_pad(
        self, _: type[T], pad_id: str
    ) -> PropertySinkPad[T] | None:
        pad = self.get_pad(pad_id)
        assert isinstance(pad, PropertySinkPad)
        return cast(PropertySinkPad[T], pad)

    def get_stateless_source_pad(
        self, _: type[T], pad_id: str
    ) -> StatelessSourcePad[T] | None:
        pad = self.get_pad(pad_id)
        assert isinstance(pad, StatelessSourcePad)
        return cast(StatelessSourcePad[T], pad)

    def get_stateless_sink_pad(
        self, _: type[T], pad_id: str
    ) -> StatelessSinkPad[T] | None:
        pad = self.get_pad(pad_id)
        assert isinstance(pad, StatelessSinkPad)
        return cast(StatelessSinkPad[T], pad)

    def get_property_source_pad_required(
        self, _: type[T], pad_id: str
    ) -> PropertySourcePad[T]:
        pad = self.get_property_source_pad(_, pad_id)
        if not pad:
            raise ValueError(
                f"PropertySourcePad with id {pad_id} not found in node {self.id}"
            )
        return pad

    def get_property_sink_pad_required(
        self, _: type[T], pad_id: str
    ) -> PropertySinkPad[T]:
        pad = self.get_property_sink_pad(_, pad_id)
        if not pad:
            raise ValueError(
                f"PropertySinkPad with id {pad_id} not found in node {self.id}"
            )
        return pad

    def get_stateless_sink_pad_required(
        self, _: type[T], pad_id: str
    ) -> StatelessSinkPad[T]:
        pad = self.get_stateless_sink_pad(_, pad_id)
        if not pad:
            raise ValueError(
                f"PropertySinkPad with id {pad_id} not found in node {self.id}"
            )
        return pad

    def get_stateless_source_pad_required(
        self, _: type[T], pad_id: str
    ) -> StatelessSourcePad[T]:
        pad = self.get_stateless_source_pad(_, pad_id)
        if not pad:
            raise ValueError(
                f"StatelessSourcePad with id {pad_id} not found in node {self.id}"
            )
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
