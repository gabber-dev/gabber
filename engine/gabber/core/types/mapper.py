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
        if not isinstance(client_value, (client.ClientPadValue)):
            raise ValueError(f"Unexpected client pad value: {type(client_value)}")

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
        elif client_value.type == "secret":
            return runtime.Secret(
                secret_id=client_value.secret_id, name=client_value.name
            )
        elif client_value.type == "enum":
            return runtime.Enum(value=client_value.value)
        elif client_value.type == "context_message_role":
            return runtime.ContextMessageRole(
                value=runtime.ContextMessageRoleEnum(client_value.value)
            )
        elif client_value.type == "float":
            return client_value.value
        elif client_value.type == "context_message":
            return Mapper.client_context_message_to_runtime(client_value)
        elif client_value.type == "object":
            return client_value.value
        elif client_value.type == "node_reference":
            return runtime.NodeReference(node_id=client_value.node_id)
        elif client_value.type == "schema":
            return Mapper.client_schema_to_runtime(client_value)
        elif client_value.type == "viseme":
            val = runtime.VisemeEnum(client_value.value)
            return runtime.Viseme(value=val)

        raise ValueError(f"Unsupported client pad value type: {client_value.type}")

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
        elif isinstance(runtime_value, dict):
            return client.Object(value=runtime_value)
        elif isinstance(runtime_value, runtime.Trigger):
            return client.Trigger()
        elif isinstance(runtime_value, runtime.ContextMessage):
            client_cm = Mapper.runtime_context_message_to_client(runtime_value)
            return client_cm
        elif isinstance(runtime_value, runtime.Schema):
            return Mapper.runtime_schema_to_client(runtime_value)
        elif isinstance(runtime_value, runtime.NodeReference):
            return client.NodeReference(node_id=runtime_value.node_id)
        elif isinstance(runtime_value, runtime.ToolDefinition):
            return client.ToolDefinition(
                name=runtime_value.name,
                description=runtime_value.description,
                parameters=Mapper.runtime_schema_to_client(runtime_value.parameters)
                if runtime_value.parameters
                else None,
            )
        elif isinstance(runtime_value, runtime.ContextMessageRole):
            return client.ContextMessageRole(
                value=client.ContextMessageRoleEnum(runtime_value.value)
            )
        elif isinstance(runtime_value, runtime.Secret):
            return client.Secret(
                secret_id=runtime_value.secret_id, name=runtime_value.name
            )
        elif isinstance(runtime_value, runtime.AudioClip):
            return client.AudioClip(
                duration=runtime_value.duration,
                transcription=runtime_value.transcription,
            )
        elif isinstance(runtime_value, runtime.VideoClip):
            return client.VideoClip(
                duration=runtime_value.duration, frame_count=len(runtime_value.video)
            )
        elif isinstance(runtime_value, runtime.Enum):
            return client.Enum(value=runtime_value.value)
        elif isinstance(runtime_value, runtime.Viseme):
            val = client.VisemeEnum(runtime_value.value.value)
            return client.Viseme(value=val)

        raise ValueError(f"Unknown runtime pad value ({type(runtime_value)})")

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
                            start_timestamp=cnt.clip.start_timestamp,
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
                            timestamp=cnt.frame.timestamp,
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
                            start_timestamp=cnt.clip.start_timestamp,
                            frame_count=len(cnt.clip.video),
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
            role=client.ContextMessageRole(
                value=client.ContextMessageRoleEnum(runtime_value.role.value)
            ),
            content=cnts,
        )

    @staticmethod
    def runtime_schema_to_client(runtime_value: runtime.Schema) -> client.Schema:
        return client.Schema(
            properties=runtime_value.properties,
            required=runtime_value.required,
            defaults=runtime_value.defaults,
        )

    @staticmethod
    def client_context_message_to_runtime(
        client_value: client.ContextMessage,
    ) -> runtime.ContextMessage:
        cnts: list[runtime.ContextMessageContentItem] = []
        for cnt in client_value.content:
            if cnt.content_type == "audio" and cnt.audio is not None:
                logging.warning("Audio content in context messages is not supported")
                continue
            elif cnt.content_type == "image" and cnt.image is not None:
                logging.warning("Image content in context messages is not supported")
            elif cnt.content_type == "video" and cnt.video is not None:
                logging.warning("Video content in context messages is not supported")
            elif cnt.content_type == "text" and cnt.text is not None:
                cnts.append(
                    runtime.ContextMessageContentItem_Text(
                        type="text", content=cnt.text
                    )
                )
        return runtime.ContextMessage(
            tool_calls=[],
            role=runtime.ContextMessageRoleEnum(client_value.role.value),
            content=cnts,
        )

    @staticmethod
    def client_schema_to_runtime(client_value: client.Schema) -> runtime.Schema:
        return runtime.Schema(
            properties=client_value.properties,
            required=client_value.required,
            defaults=client_value.defaults,
        )


def is_client_pad_value(client_value: Any) -> client.ClientPadValue | None:
    if isinstance(client_value, dict) and "type" in client_value:
        try:
            return client_pad_value_adapter.validate_python(client_value)
        except Exception:
            pass

    return None
