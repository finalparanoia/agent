from typing import Optional, List
from agent.common.application.agent_flow import key_word_agent, writer_agent, brief_agent
from sqlmodel import Session, select
from agent.common.repo.template_cmd import WorldTemplateCommands
from agent.common.repo.template_query import WorldTemplateQueries
from agent.common.schemas.database import World
from agent.common.schemas.dto import RuntimeDataDTO, RawRequestRespondPairDTO, KeywordsDTO


class RuntimeManagement:
    """运行时管理类"""
    def __init__(self, session: Session):
        self.session = session
        self._cmd = WorldTemplateCommands(session)
        self._query = WorldTemplateQueries(session)
        self._runtime_id: Optional[str] = None

    def initialize(self, world_id: str, character_ids: List[str]) -> str:
        """初始化运行时数据"""
        world = self.session.exec(
            select(World).where(World.id == world_id)
        ).first()
        if not world:
            raise ValueError(f"World not found: {world_id}")

        payload = RuntimeDataDTO(
            world_id=world_id,
            label=world.name,
            character_ids=character_ids,
        )
        self._runtime_id = self._cmd.runtime_data(payload)
        assert self._runtime_id is not None
        return self._runtime_id

    def chat(self, request: str) -> str:
        """开始会话"""
        if not self._runtime_id:
            raise RuntimeError("Runtime not initialized, call initialize() first")

        # 使用关键词提取agent
        keywords_dto: KeywordsDTO = key_word_agent.run_sync(request).output

        keywords = keywords_dto.keywords

        # 根据关键词混合检索上下文
        search_result = self._query.combined_search(self._runtime_id, keywords)
        context_parts = []

        # 组装上下文
        if search_result.world:
            context_parts.append(f"[World] {search_result.world.name}")

        for wd in search_result.world_definitions:
            context_parts.append(f"[Definition] {wd.value}")

        for c in search_result.characters:
            char_desc = c.description
            if c.description_patch:
                char_desc += f" ({c.description_patch})"
            char_info = f"[Character] {c.name}: {char_desc}"
            if c.status:
                char_info += f" | status: {c.status}"
            context_parts.append(char_info)

        for rh in search_result.runtime_history:
            context_parts.append(f"[History] Q: {rh.request} A: {rh.respond}")

        context = "\n".join(context_parts) + f"\n用户指令：{request}"

        # 调用写作agent
        respond_context = writer_agent.run_sync(context).output

        brief = brief_agent.run_sync(respond_context).output

        # 问答对入库
        pair_payload = RawRequestRespondPairDTO(
            runtime_id=self._runtime_id,
            request=request,
            respond=respond_context,
            event_brief=brief,
        )
        self._cmd.pair_data(pair_payload)

        return respond_context
