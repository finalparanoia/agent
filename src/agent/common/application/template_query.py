from sqlmodel import Session, select

from agent.common.schemas.database import World, WorldDefinition, ReactionDefinition, CharacterDefinition
from agent.common.schemas.dto import WorldDefinitionDTO, ReactionDefinitionDTO, CharacterDefinitionDTO


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
