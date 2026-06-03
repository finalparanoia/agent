from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List

from agent.common.schemas.database import (
    World, WorldDefinition, RuntimeCharacter,
    RuntimeData, RawRequestRespondPair
)


class WorldDefinitionDTO(BaseModel):
    id: Optional[int] = -1
    world_id: str
    value: str


class CharacterDefinitionDTO(BaseModel):
    id: Optional[int] = -1
    world_id: str
    name: str
    description: str


class RuntimeDataDTO(BaseModel):
    id: Optional[str] = None
    world_id: str
    character_ids: List[str]
    label: str


class RawRequestRespondPairDTO(BaseModel):
    id: Optional[int] = -1
    runtime_id: str
    request: str
    respond: str
    event_brief: str = Field(default="")


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    world: Optional[World] = None
    world_definitions: List[WorldDefinition] = Field(default_factory=list)
    characters: List[RuntimeCharacter] = Field(default_factory=list)
    runtime_data: Optional[RuntimeData] = None
    runtime_history: List[RawRequestRespondPair] = Field(default_factory=list)


class WorldBookDefinition(BaseModel):
    value: str


    @model_validator(mode='before')
    @classmethod
    def wrap_string(cls, data):
        """将字符串数据包装为字典格式，确保数据结构一致"""
        if isinstance(data, str):
            return {'value': data}
        return data

class WorldBookCharacter(BaseModel):
    name: str
    description: str


class WorldBook(BaseModel):
    name: str
    definitions: List[WorldBookDefinition] = Field(default_factory=list)
    characters: List[WorldBookCharacter] = Field(default_factory=list)


class KeywordsDTO(BaseModel):
    keywords: List[str]
