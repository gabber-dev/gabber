from gabber import ConnectionDetails
from abc import abstractmethod, ABC


class ConnectionProvider(ABC):
    @abstractmethod
    async def get_connection(self, *, run_id: str) -> ConnectionDetails: ...
