from sqlmodel import Session, select

from agent.common.schemas.database import World, WorldDefinition, ReactionDefinition, CharacterDefinition
from agent.common.schemas.dto import WorldDefinitionDTO, ReactionDefinitionDTO, CharacterDefinitionDTO


class RuntimeManagement:
    def __init__(self, session: Session):
        self.session = session

    def initialize(self, world_id: str):
        # 根据world id 读取对应的各项模板数据，创建运行时数据库记录RuntimeData
        pass

    def chat(self, request: str):
        # 接受用户输入的指令字符串，使用WorldTemplateQueries进行检索，然后调用打模型进行检索增强生成，相关结果调用存储至RawRequestRespondPair
        # 返还本次生成的respond字符串
        pass
