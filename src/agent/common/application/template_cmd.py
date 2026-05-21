from sqlmodel import Session, select

from agent.common.schemas.database import World, WorldDefinition, ReactionDefinition, CharacterDefinition
from agent.common.schemas.dto import WorldDefinitionDTO, ReactionDefinitionDTO, CharacterDefinitionDTO


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
            name=payload.name,
            description=payload.description,
        )
        self.session.add(data)



class WorldTemplateQueries:
    def __init__(self, session: Session):
        self.session = session

    def combined_search(self, runtime_id: str, query: str):
        pass

    def _bm25(self, runtime_id: str, query: str):
        # 全文检索
        pass

    def _relation(self, runtime_id: str, query: str):
        # 相似文本模糊检索
        pass

    def _vector(self, runtime_id: str, query: str):
        # 向量检索
        pass
