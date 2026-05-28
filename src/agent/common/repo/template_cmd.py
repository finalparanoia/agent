from sqlmodel import Session, select, col

from agent.common.schemas.database import (
    World, WorldDefinition, CharacterDefinition,
    RuntimeData, RawRequestRespondPair, RuntimeCharacter
)
from agent.common.schemas.dto import (
    WorldDefinitionDTO, CharacterDefinitionDTO,
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

    def character_define(self, payload: CharacterDefinitionDTO):
        data = CharacterDefinition(
            world_id=payload.world_id,
            name=payload.name,
            description=payload.description,
        )
        self.session.add(data)
        self.session.flush()
        return data.id

    def runtime_data(self, payload: RuntimeDataDTO):
        data = RuntimeData(
            world_id=payload.world_id,
            label=payload.label,
        )
        self.session.add(data)
        self.session.flush()

        character_statement = select(CharacterDefinition).where(col(CharacterDefinition.id).in_(payload.character_ids))

        for character_entity in self.session.exec(character_statement).all():
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
