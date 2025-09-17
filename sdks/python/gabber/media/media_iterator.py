import asyncio
from typing import Generic, TypeVar, Protocol
from weakref import ref

T = TypeVar("T")


class MediaIteratorOwner(Protocol):
    def remove_iterator(self, iterator: "MediaIterator"): ...


class MediaIterator(Generic[T]):
    def __init__(self, *, owner: MediaIteratorOwner):
        self._q = asyncio.Queue[T | None]()
        self._owner = ref(owner)

    def _push(self, item: T):
        self._q.put_nowait(item)

    def _eos(self):
        self._q.put_nowait(None)

    def __aiter__(self):
        return self

    async def __anext__(self):
        item = await self._q.get()
        if item is None:
            raise StopAsyncIteration
        return item

    def cleanup(self):
        while not self._q.empty():
            self._q.get_nowait()
        self._q.put_nowait(None)

        owner = self._owner()
        if owner is not None:
            owner.remove_iterator(self)
