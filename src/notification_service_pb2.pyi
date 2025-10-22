from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UNKNOWN: _ClassVar[MessageType]
    HELLO: _ClassVar[MessageType]
    GOODBYE: _ClassVar[MessageType]
UNKNOWN: MessageType
HELLO: MessageType
GOODBYE: MessageType

class SendMessageRequest(_message.Message):
    __slots__ = ("client_id", "message_type")
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    message_type: MessageType
    def __init__(self, client_id: _Optional[str] = ..., message_type: _Optional[_Union[MessageType, str]] = ...) -> None: ...

class SendMessageResponse(_message.Message):
    __slots__ = ("success", "message")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ...) -> None: ...

class GetClientStatusRequest(_message.Message):
    __slots__ = ("client_id",)
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    client_id: str
    def __init__(self, client_id: _Optional[str] = ...) -> None: ...

class GetClientStatusResponse(_message.Message):
    __slots__ = ("client_statuses",)
    class ClientStatusesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CLIENT_STATUSES_FIELD_NUMBER: _ClassVar[int]
    client_statuses: _containers.ScalarMap[str, str]
    def __init__(self, client_statuses: _Optional[_Mapping[str, str]] = ...) -> None: ...
