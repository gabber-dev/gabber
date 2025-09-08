from .media_iterator import MediaIterator
from typing import Generic, TypeVar

T = TypeVar("T")


class VirtualDevice(Generic[T]):
    def __init__(self):
        self._iterators: list[MediaIterator[T]] = []

    def push(self, item: T):
        for iterator in self._iterators:
            iterator._push(item)

    def _close(self):
        for iterator in self._iterators:
            iterator._eos()

    def create_iterator(self):
        iterator = MediaIterator[T](owner=self)
        self._iterators.append(iterator)
        return iterator

    def remove_iterator(self, iterator: MediaIterator[T]):
        self._iterators.remove(iterator)
