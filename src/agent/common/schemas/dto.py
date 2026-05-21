from pydantic import BaseModel, Field
from typing import Optional


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
