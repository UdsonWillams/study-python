"""Modelos Pydantic usados na API."""

from pydantic import BaseModel


class ProgressIn(BaseModel):
    topic_id: int


class ProgressOut(BaseModel):
    completed_topic_ids: list[int]
