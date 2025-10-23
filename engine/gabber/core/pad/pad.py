# Copyright 2025 Fluently AI, Inc. DBA Gabber. All rights reserved.
# SPDX-License-Identifier: SUL-1.0

import asyncio
import logging
from dataclasses import dataclass
from ..types import runtime, pad_constraints
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Protocol,
    runtime_checkable,
    Generic,
    TypeVar,
)

from .request_context import RequestContext

if TYPE_CHECKING:
    from ..node import Node

PAD_T = TypeVar("PAD_T", bound=runtime.RuntimePadValue)


class Pad(Protocol, Generic[PAD_T]):
    _update_handlers: set[Callable[["Pad[PAD_T]", PAD_T], None]]
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
    def set_type_constraints(
        self, constraints: list[pad_constraints.BasePadType] | None
    ) -> None: ...
    def get_type_constraints(self) -> list[pad_constraints.BasePadType] | None: ...
    def get_default_type_constraints(
        self,
    ) -> list[pad_constraints.BasePadType] | None: ...
    def set_default_type_constraints(
        self, constraints: list[pad_constraints.BasePadType] | None
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
                handler(self, value)
            except Exception as e:
                logging.error(f"Error in update handler {handler}: {e}")

    def _resolve_type_constraints(self) -> None:
        intersection = self.get_default_type_constraints()
        for p in self._pad_links:
            intersection = pad_constraints.INTERSECTION(
                intersection, p.get_default_type_constraints()
            )

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
            intersection = pad_constraints.INTERSECTION(
                intersection, p.get_default_type_constraints()
            )

        for p in all_pads:
            p.set_type_constraints(intersection)

    @property
    def logger(self) -> logging.LoggerAdapter:
        if self._logger is None:
            self._logger = logging.LoggerAdapter(
                self.get_owner_node().logger, {"pad": self.get_id()}
            )
        return self._logger


PROXY_PAD_T = TypeVar("PROXY_PAD_T", bound=runtime.RuntimePadValue)


@runtime_checkable
class ProxyPad(Protocol, Generic[PROXY_PAD_T]):
    def get_other(self) -> Pad[PROXY_PAD_T]: ...


SINK_PAD_T = TypeVar("SINK_PAD_T", bound=runtime.RuntimePadValue)


@runtime_checkable
class SinkPad(Pad[SINK_PAD_T], Protocol, Generic[SINK_PAD_T]):
    def get_previous_pad(self) -> "SourcePad[SINK_PAD_T] | None": ...
    def set_previous_pad(self, pad: "SourcePad[SINK_PAD_T] | None") -> None: ...
    def _get_queue(self) -> asyncio.Queue["Item[SINK_PAD_T] | None"]: ...

    def disconnect(self) -> None:
        prev_pad = self.get_previous_pad()
        if prev_pad:
            prev_pad.disconnect(self)

    def __aiter__(self) -> "SinkPad[SINK_PAD_T]":
        return self

    async def __anext__(self) -> "Item[SINK_PAD_T]":
        queue = self._get_queue()
        item = await queue.get()
        if item is None:
            raise StopAsyncIteration
        return item


SOURCE_PAD_T = TypeVar("SOURCE_PAD_T", bound=runtime.RuntimePadValue)


@runtime_checkable
class SourcePad(Pad[SOURCE_PAD_T], Protocol, Generic[SOURCE_PAD_T]):
    def get_next_pads(self) -> list["SinkPad[SOURCE_PAD_T]"]: ...
    def set_next_pads(self, pads: list["SinkPad[SOURCE_PAD_T]"]) -> None: ...

    def push_item(self, value: SOURCE_PAD_T, ctx: RequestContext) -> None:
        notify_type = False
        if isinstance(value, NOTIFIABLE_TYPES):
            notify_type = True
            if isinstance(value, runtime.BaseRuntimeType):
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
                parent=ctx,
                timeout=ctx._timeout_s,
                originator=self.get_id(),
                metadata=ctx.metadata,
            )

            item = Item[SOURCE_PAD_T](value=value, ctx=new_ctx)

            q.put_nowait(item)

        ctx.complete()

    def connect(self, sink_pad: "SinkPad[SOURCE_PAD_T]") -> None:
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

    def disconnect(self, sink_pad: "SinkPad[SOURCE_PAD_T]") -> None:
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
                if isinstance(tc[0], pad_constraints.NodeReference):
                    sink_pad.set_value(None)

    def disconnect_all(self) -> None:
        for np in self.get_next_pads():
            np.set_previous_pad(None)
        self.set_next_pads([])

    def can_connect(self, other: "Pad[SOURCE_PAD_T]") -> bool:
        if not isinstance(other, SinkPad):
            return False

        if other.get_previous_pad() is not None:
            return False

        intersection = pad_constraints.INTERSECTION(
            self.get_type_constraints(), other.get_type_constraints()
        )

        if intersection is not None and len(intersection) == 0:
            return False

        return True


PROPERTY_PAD_T = TypeVar("PROPERTY_PAD_T", bound=runtime.RuntimePadValue)


@runtime_checkable
class PropertyPad(Pad[PROPERTY_PAD_T], Protocol, Generic[PROPERTY_PAD_T]):
    def get_value(self) -> PROPERTY_PAD_T: ...
    def set_value(self, value: PROPERTY_PAD_T): ...


ITEM_T = TypeVar("ITEM_T", bound=runtime.RuntimePadValue)


@dataclass
class Item(Generic[ITEM_T]):
    value: ITEM_T
    ctx: "RequestContext"


NOTIFIABLE_TYPES = (
    # Primitives
    str,
    int,
    float,
    bool,
    list,
    runtime.Trigger,
    runtime.ContextMessage,
    runtime.AudioClip,
    runtime.VideoClip,
    runtime.Enum,
)
