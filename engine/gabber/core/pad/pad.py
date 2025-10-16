# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from dataclasses import dataclass
from .. import runtime_types
from typing import TYPE_CHECKING, Any, Callable, Protocol, runtime_checkable

from .request_context import RequestContext
from .types import INTERSECTION, BasePadType, NodeReference

if TYPE_CHECKING:
    from ..node import Node


class Pad(Protocol):
    _update_handlers: set[Callable[["Pad", Any], None]]
    _pad_links: set["Pad"]
    _logger: logging.LoggerAdapter | None

    def __init__(self):
        self._update_handlers = set()
        self._pad_links = set()
        self._logger = None

    def get_id(self) -> str: ...
    def set_id(self, id: str) -> None: ...
    def get_group(self) -> str: ...
    def get_editor_type(self) -> str: ...
    def set_type_constraints(self, constraints: list[BasePadType] | None) -> None: ...
    def get_type_constraints(self) -> list[BasePadType] | None: ...
    def get_default_type_constraints(self) -> list[BasePadType] | None: ...
    def set_default_type_constraints(
        self, constraints: list[BasePadType] | None
    ) -> None: ...
    def get_owner_node(self) -> "Node": ...
    def link_types_to_pad(self, other: "Pad") -> None:
        self._pad_links.add(other)
        other._pad_links.add(self)
        self._resolve_type_constraints()

    def unlink_types_from_pad(self, other: "Pad") -> None:
        if other in self._pad_links:
            self._pad_links.remove(other)
        if self in other._pad_links:
            other._pad_links.remove(self)
        self._resolve_type_constraints()
        other._resolve_type_constraints()

    def unlink_all(self) -> None:
        for p in self._pad_links.copy():
            self.unlink_types_from_pad(p)

    def _add_update_handler(self, handler: Callable[["Pad", Any], None]):
        self._update_handlers.add(handler)

    def _remove_update_handler(self, handler: Callable[["Pad", Any], None]) -> None:
        if handler in self._update_handlers:
            self._update_handlers.remove(handler)

    def _notify_update(self, value: Any) -> None:
        for handler in self._update_handlers:
            try:
                logging.info("NEIL calling handler %s", self.get_id())
                handler(self, value)
            except Exception as e:
                logging.error(f"Error in update handler {handler}: {e}")

    def _resolve_type_constraints(self) -> None:
        intersection = self.get_default_type_constraints()
        for p in self._pad_links:
            intersection = INTERSECTION(intersection, p.get_default_type_constraints())

        all_pads: list[Pad] = []
        q: list[Pad] = [self]
        seen = set()
        while q:
            current = q.pop(0)
            if current in seen:
                continue
            seen.add(current)
            all_pads.append(current)
            for p in current._pad_links:
                if p not in all_pads:
                    q.append(p)

            if isinstance(current, SourcePad):
                next_pads = current.get_next_pads()
                for np in next_pads:
                    if np not in all_pads:
                        q.append(np)
            elif isinstance(current, SinkPad):
                prev_pad = current.get_previous_pad()
                if prev_pad and prev_pad not in all_pads:
                    q.append(prev_pad)

        intersection = self.get_default_type_constraints()
        for p in all_pads:
            intersection = INTERSECTION(intersection, p.get_default_type_constraints())

        for p in all_pads:
            p.set_type_constraints(intersection)

    @property
    def logger(self) -> logging.LoggerAdapter:
        if self._logger is None:
            self._logger = logging.LoggerAdapter(
                self.get_owner_node().logger, {"pad": self.get_id()}
            )
        return self._logger


@runtime_checkable
class ProxyPad(Protocol):
    def get_other(self) -> Pad: ...


@runtime_checkable
class SinkPad(Pad, Protocol):
    def get_previous_pad(self) -> "SourcePad | None": ...
    def set_previous_pad(self, pad: "SourcePad | None") -> None: ...
    def _get_queue(self) -> asyncio.Queue["Item | None"]: ...

    def disconnect(self) -> None:
        prev_pad = self.get_previous_pad()
        if prev_pad:
            prev_pad.disconnect(self)

    def __aiter__(self) -> "SinkPad":
        return self

    async def __anext__(self) -> "Item":
        queue = self._get_queue()
        item = await queue.get()
        if item is None:
            raise StopAsyncIteration
        return item


@runtime_checkable
class SourcePad(Pad, Protocol):
    def get_next_pads(self) -> list["SinkPad"]: ...
    def set_next_pads(self, pads: list["SinkPad"]) -> None: ...

    def push_item(self, value: Any, ctx: RequestContext) -> None:
        notify_type = False
        if isinstance(value, NOTIFIABLE_TYPES):
            notify_type = True
            if isinstance(value, runtime_types.BaseRuntimeType):
                self.logger.info(
                    f"Source Pad Push: {value.log_type()}", extra=value.to_log_values()
                )
            else:
                self.logger.info(
                    f"Source Pad Push: {type(value)}", extra={"value": str(value)}
                )

        # Setting value notifies for itself so we skip it
        if isinstance(self, PropertyPad):
            self.set_value(value)
        else:
            if notify_type:
                self._notify_update(value)

        for np in self.get_next_pads():
            q = np._get_queue()
            if q.qsize() > 1_000:
                logging.warning(
                    f"SinkPad queue size exceeded 1000, skipping. {np.get_owner_node().id}:{np.get_id()}"
                )
                if ctx is not None:
                    ctx.complete()

            if isinstance(np, PropertyPad):
                np.set_value(value)
            else:
                if notify_type:
                    np._notify_update(value)
            new_ctx = RequestContext(
                parent=ctx, timeout=ctx._timeout_s, originator=self.get_id()
            )

            item = Item(value=value, ctx=new_ctx)

            q.put_nowait(item)

        ctx.complete()

    def connect(self, sink_pad: "SinkPad") -> None:
        if not self.can_connect(sink_pad):
            raise ValueError(
                f"Cannot connect to this type of SinkPad: {self.get_owner_node().id}.{self.get_id()} -> {sink_pad.get_owner_node().id}.{sink_pad.get_id()}"
            )
        next_pads = self.get_next_pads()
        next_pads.append(sink_pad)
        self.set_next_pads(next_pads)
        sink_pad.set_previous_pad(self)

        self._resolve_type_constraints()

        if isinstance(self, PropertyPad):
            v = self.get_value()
            for np in next_pads:
                if isinstance(np, PropertyPad):
                    np.set_value(v)

    def disconnect(self, sink_pad: "SinkPad") -> None:
        next_pads = self.get_next_pads()
        next_pads = [
            np
            for np in next_pads
            if (
                np.get_id() == sink_pad.get_id()
                and np.get_owner_node().id == sink_pad.get_owner_node().id
            )
            is False
        ]
        self.set_next_pads(next_pads)
        sink_pad.set_previous_pad(None)
        self._resolve_type_constraints()
        sink_pad._resolve_type_constraints()
        if isinstance(sink_pad, PropertyPad):
            tc = sink_pad.get_type_constraints()
            if tc is not None and len(tc) == 1:
                if isinstance(tc[0], NodeReference):
                    sink_pad.set_value(None)

    def disconnect_all(self) -> None:
        for np in self.get_next_pads():
            np.set_previous_pad(None)
        self.set_next_pads([])

    def can_connect(self, other: "Pad") -> bool:
        if not isinstance(other, SinkPad):
            return False

        if other.get_previous_pad() is not None:
            return False

        intersection = INTERSECTION(
            self.get_type_constraints(), other.get_type_constraints()
        )

        if intersection is not None and len(intersection) == 0:
            return False

        return True


@runtime_checkable
class PropertyPad(Pad, Protocol):
    def get_value(self) -> Any: ...
    def set_value(self, value: Any): ...


@dataclass
class Item:
    value: Any
    ctx: "RequestContext"


NOTIFIABLE_TYPES = (
    # Primitives
    str,
    int,
    float,
    bool,
    list,
    runtime_types.Trigger,
    runtime_types.ContextMessage,
    runtime_types.AudioClip,
    runtime_types.VideoClip,
)
