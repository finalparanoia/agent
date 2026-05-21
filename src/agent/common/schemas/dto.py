from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

from agent.common.schemas.database import (
    World, WorldDefinition, ReactionDefinition, CharacterDefinition,
    RuntimeData, RawRequestRespondPair
)


class WorldDefinitionDTO(BaseModel):
    id: Optional[int] = -1
    world_id: str
    value: str


class ReactionDefinitionDTO(BaseModel):
    id: Optional[int] = -1
    world_id: str
    name: str
    description: str = Field(default="")
    user_reaction: str = Field(default="")
    target_reaction: str = Field(default="")


class CharacterDefinitionDTO(BaseModel):
    id: Optional[int] = -1
    name: str
    description: str


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    world: Optional[World] = None
    world_definitions: List[WorldDefinition] = Field(default_factory=list)
    reactions: List[ReactionDefinition] = Field(default_factory=list)
    characters: List[CharacterDefinition] = Field(default_factory=list)
    runtime_data: Optional[RuntimeData] = None
    runtime_history: List[RawRequestRespondPair] = Field(default_factory=list)
