import json
from typing import Optional, List

from litellm import completion, ModelResponse
from sqlmodel import Session, select
from loguru import logger
from agent.common.config import SETTINGS
from agent.common.repo.template_cmd import WorldTemplateCommands
from agent.common.repo.template_query import WorldTemplateQueries
from agent.common.schemas.database import World
from agent.common.schemas.dto import RuntimeDataDTO, RawRequestRespondPairDTO


class RuntimeManagement:
    def __init__(self, session: Session):
        self.session = session
        self._cmd = WorldTemplateCommands(session)
        self._query = WorldTemplateQueries(session)
        self._runtime_id: Optional[str] = None

    def initialize(self, world_id: str) -> str:
        world = self.session.exec(
            select(World).where(World.id == world_id)
        ).first()
        if not world:
            raise ValueError(f"World not found: {world_id}")

        payload = RuntimeDataDTO(
            world_id=world_id,
            label=world.name,
        )
        self._runtime_id = self._cmd.runtime_data(payload)
        assert self._runtime_id is not None
        return self._runtime_id

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        keyword_prompt = (
            "你是一个关键词提取助手。请从用户输入中提取用于检索的关键词，"
            "返回JSON格式的字符串列表，不要输出任何其他内容。\n"
            '示例输出：["关键词1", "关键词2", "关键词3"]'
        )
        response = completion(
            model=SETTINGS.llm_model,
            messages=[
                {"role": "system", "content": keyword_prompt},
                {"role": "user", "content": text},
            ],
            api_key=SETTINGS.llm_api_key or None,
            api_base=SETTINGS.llm_api_base or None,
        )
        if not isinstance(response, ModelResponse):
            raise RuntimeError("Expected ModelResponse but got streaming response")
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("LLM returned empty response for keyword extraction")
        try:
            keywords = json.loads(content.strip())
            if isinstance(keywords, list) and all(isinstance(k, str) for k in keywords):
                return keywords
        except json.JSONDecodeError:
            pass
        logger.warning(f"Failed to parse keywords from LLM response: {content}, falling back to raw text")
        return [text]

    def chat(self, request: str) -> str:
        if not self._runtime_id:
            raise RuntimeError("Runtime not initialized, call initialize() first")

        keywords = self._extract_keywords(request)

        search_result = self._query.combined_search(self._runtime_id, keywords)

        logger.debug(f"Extracted keywords: {keywords}, search query: {search_result}")


        context_parts = []

        if search_result.world:
            context_parts.append(f"[World] {search_result.world.name}")

        for wd in search_result.world_definitions:
            context_parts.append(f"[Definition] {wd.value}")

        for r in search_result.reactions:
            context_parts.append(
                f"[Reaction] {r.name}: {r.description} "
                f"| user: {r.user_reaction} | target: {r.target_reaction}"
            )

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

        context = "\n".join(context_parts)

        system_prompt = (
            "你是一个小说创作AI，你将根据下面内容进行故事创作。"
            "Use the following context to answer the user's question accurately.\n\n"
            f"--- World Context ---\n{context}\n--- End of Context ---"
            "严格按照用户输入的内容行文，可以对用户的指令进行任意的细致化描写，但绝对不要进行任何自作主张的情节推动"
            "只输出正文"
        )
        logger.debug(system_prompt)

        response = completion(
            model=SETTINGS.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request},
            ],
            api_key=SETTINGS.llm_api_key or None,
            api_base=SETTINGS.llm_api_base or None,
        )

        if not isinstance(response, ModelResponse):
            raise RuntimeError("Expected ModelResponse but got streaming response")

        respond = response.choices[0].message.content
        if respond is None:
            raise RuntimeError("LLM returned empty response")

        event_brief = respond[:200] if len(respond) > 200 else respond

        pair_payload = RawRequestRespondPairDTO(
            runtime_id=self._runtime_id,
            request=request,
            respond=respond,
            event_brief=event_brief,
        )
        self._cmd.pair_data(pair_payload)

        return respond
