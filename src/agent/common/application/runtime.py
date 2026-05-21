from typing import Optional

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

    def chat(self, request: str) -> str:
        if not self._runtime_id:
            raise RuntimeError("Runtime not initialized, call initialize() first")

        search_result = self._query.combined_search(self._runtime_id, request)

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
            context_parts.append(f"[Character] {c.name}: {c.description}")

        for rh in search_result.runtime_history:
            context_parts.append(f"[History] Q: {rh.request} A: {rh.respond}")

        context = "\n".join(context_parts)

        system_prompt = (
            "你是一个小说创作AI，你将根据下面内容进行故事创作。"
            "Use the following context to answer the user's question accurately.\n\n"
            f"--- World Context ---\n{context}\n--- End of Context ---"
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
