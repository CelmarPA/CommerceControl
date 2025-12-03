# app/schemas/message_schema.py

"""
Message Schema
--------------

Simple response model used for returning uniform message structures
across multiple endpoints.
"""

from pydantic import BaseModel


class Message(BaseModel):
    """
    Schema representing a generic message response.

    :param detail: Message text returned to the client.
    :type detail: str
    """

    detail: str
