import logging
from . import client, runtime

from typing import Any
from pydantic import TypeAdapter

client_pad_value_adapter = TypeAdapter(client.ClientPadValue)


class Mapper:
    @staticmethod
    def client_to_runtime(
        client_value: client.ClientPadValue | Any,
    ) -> runtime.RuntimePadValue:
        if isinstance(client_value, dict):
            c_v = is_client_pad_value(client_value)
            if c_v is not None:
                client_value = c_v
            else:
                old_cm = is_old_context_message(client_value)
                if old_cm is not None:
                    return old_cm

                old_schema = is_old_schema(client_value)
                if old_schema is not None:
                    return old_schema
        elif isinstance(client_value, list):
            rvs: list[runtime.RuntimePadValue] = []
            for item in client_value:
                r_item = Mapper.client_to_runtime(item)
                if r_item is not None:
                    rvs.append(r_item)
            return rvs
        elif isinstance(client_value, str):
            return client_value
        elif isinstance(client_value, bool):
            return client_value
        elif isinstance(client_value, (int, float)):
            return client_value
        elif isinstance(client_value, client.ClientPadValue):
            if client_value is None:
                return None
            elif client_value.type == "string":
                return client_value.value
            elif client_value.type == "integer":
                return client_value.value
            elif client_value.type == "float":
                return client_value.value
            elif client_value.type == "boolean":
                return client_value.value
            elif client_value.type == "trigger":
                return runtime.Trigger()
            elif client_value.type == "list":
                rvs: list[runtime.RuntimePadValue] = []
                for item in client_value.items:
                    r_item = Mapper.client_to_runtime(item)
                    if r_item is not None:
                        rvs.append(r_item)
                return rvs
            else:
                raise ValueError(
                    f"Unsupported client pad value type: {client_value.type}"
                )

        raise ValueError(
            f"Unknown client pad value: {client_value} ({type(client_value)})"
        )

    @staticmethod
    def runtime_to_client(
        runtime_value: runtime.RuntimePadValue | Any,
    ) -> client.ClientPadValue:
        if runtime_value is None:
            return None
        if isinstance(runtime_value, bool):
            return client.Boolean(value=runtime_value)
        elif isinstance(runtime_value, int):
            return client.Integer(value=runtime_value)
        elif isinstance(runtime_value, float):
            return client.Float(value=runtime_value)
        elif isinstance(runtime_value, str):
            return client.String(value=runtime_value)
        elif isinstance(runtime_value, list):
            items: list[client.ClientPadValue] = []
            for item in runtime_value:
                c_item = Mapper.runtime_to_client(item)
                if c_item is not None:
                    items.append(c_item)
            return client.List(count=len(items), items=items)
        elif isinstance(runtime_value, runtime.Trigger):
            return client.Trigger()
        elif isinstance(runtime_value, runtime.ContextMessage):
            client_cm = Mapper.runtime_context_message_to_client(runtime_value)
            return client_cm

        raise ValueError(
            f"Unknown runtime pad value: {runtime_value} ({type(runtime_value)})"
        )

    @staticmethod
    def runtime_context_message_to_client(
        runtime_value: runtime.ContextMessage,
    ) -> client.ContextMessage:
        cnts: list[client.ContextMessageContentItem] = []
        for cnt in runtime_value.content:
            if cnt.type == "audio":
                cnts.append(
                    client.ContextMessageContentItem(
                        content_type="audio",
                        audio=client.ContextMessageContentItem_Audio(
                            duration=cnt.clip.duration,
                            transcription=cnt.clip.transcription,
                            handle="",
                        ),
                    )
                )
            elif cnt.type == "image":
                cnts.append(
                    client.ContextMessageContentItem(
                        content_type="image",
                        image=client.ContextMessageContentItem_Image(
                            width=cnt.frame.width,
                            height=cnt.frame.height,
                            handle="",
                        ),
                    )
                )
            elif cnt.type == "video":
                w = h = 0
                if len(cnt.clip.video) > 0:
                    w = cnt.clip.video[0].width
                    h = cnt.clip.video[0].height
                cnts.append(
                    client.ContextMessageContentItem(
                        content_type="video",
                        video=client.ContextMessageContentItem_Video(
                            width=w,
                            height=h,
                            duration=cnt.clip.duration,
                            handle="",
                        ),
                    )
                )
            elif cnt.type == "text":
                cnts.append(
                    client.ContextMessageContentItem(
                        content_type="text",
                        text=cnt.content,
                    )
                )

        return client.ContextMessage(
            role=runtime_value.role,
            content=cnts,
        )


def is_client_pad_value(client_value: Any) -> client.ClientPadValue | None:
    if isinstance(client_value, dict) and "type" in client_value:
        try:
            return client_pad_value_adapter.validate_python(client_value)
        except Exception:
            pass

    return None


def is_old_context_message(v: dict) -> runtime.ContextMessage | None:
    try:
        return runtime.ContextMessage.model_validate(v)
    except Exception:
        pass

    return None


def is_old_schema(v: dict) -> runtime.Schema | None:
    try:
        return runtime.Schema.model_validate(v)
    except Exception:
        pass

    return None
