from sqlmodel import Session, select

from agent.common.schemas.database import (
    World, WorldDefinition, ReactionDefinition, CharacterDefinition,
    RuntimeData, RawRequestRespondPair, RuntimeCharacter
)
from agent.common.schemas.dto import (
    WorldDefinitionDTO, ReactionDefinitionDTO, CharacterDefinitionDTO,
    RuntimeDataDTO, RawRequestRespondPairDTO
)


class WorldTemplateCommands:
    def __init__(self, session: Session):
        self.session = session

    def create_world(self, name: str):
        data = World(name=name)
        self.session.add(data)
        return data.id

    def rename(self, world_id: str, new_name: str):
        statement = select(World).where(World.id == world_id)
        data = self.session.exec(statement).one()
        data.name = new_name
        self.session.add(data)

    def world_define(self, payload: WorldDefinitionDTO):
        data = WorldDefinition(
            world_id=payload.world_id,
            value=payload.value,
        )
        self.session.add(data)

    def reaction_define(self, payload: ReactionDefinitionDTO):
        data = ReactionDefinition(
            world_id=payload.world_id,
            name=payload.name,
            description=payload.description,
            user_reaction=payload.user_reaction,
            target_reaction=payload.target_reaction,
        )
        self.session.add(data)

    def character_define(self, payload: CharacterDefinitionDTO):
        data = CharacterDefinition(
            world_id=payload.world_id,
            name=payload.name,
            description=payload.description,
        )
        self.session.add(data)

    def runtime_data(self, payload: RuntimeDataDTO):
        data = RuntimeData(
            world_id=payload.world_id,
            label=payload.label,
        )
        self.session.add(data)
        self.session.flush()

        for character_entity in data.world.character:
            character_entity: CharacterDefinition
            character_data = RuntimeCharacter(
                character_id=character_entity.id,
                runtime_data_id=data.id,
                name=character_entity.name,
                description=character_entity.description,
            )
            self.session.add(character_data)
        return data.id

    def pair_data(self, payload: RawRequestRespondPairDTO):
        data = RawRequestRespondPair(
            runtime_id=payload.runtime_id,
            request=payload.request,
            respond=payload.respond,
            event_brief=payload.event_brief,
        )
        self.session.add(data)
