from typing import Optional, List, Dict, Any

from sqlmodel import Session, select, func, or_, col

from agent.common.schemas.database import (
    World, WorldDefinition, ReactionDefinition, CharacterDefinition,
    RuntimeData, RawRequestRespondPair
)
from agent.common.schemas.dto import SearchResult


class WorldTemplateQueries:
    def __init__(self, session: Session):
        self.session = session

    def combined_search(self, runtime_id: str, query: str) -> SearchResult:
        world_id = self._resolve_world_id(runtime_id)
        if not world_id:
            return SearchResult()

        bm25_result = self._bm25(runtime_id, query)
        relation_result = self._relation(runtime_id, query)
        vector_result = self._vector(runtime_id, query)

        return self._merge_results([bm25_result, relation_result, vector_result])

    def _resolve_world_id(self, runtime_id: str) -> Optional[str]:
        stmt = select(RuntimeData.world_id).where(RuntimeData.id == runtime_id)

        # noinspection PyTypeChecker
        row: str = self.session.exec(stmt).first()
        return row

    def _query_static_templates(self, world_id: str) -> Dict[str, Any]:
        world = self.session.exec(
            select(World).where(World.id == world_id)
        ).first()

        world_definitions = list(self.session.exec(
            select(WorldDefinition).where(WorldDefinition.world_id == world_id)
        ).all())

        reactions = list(self.session.exec(
            select(ReactionDefinition).where(ReactionDefinition.world_id == world_id)
        ).all())

        characters = list(self.session.exec(
            select(CharacterDefinition)
        ).all())

        return {
            "world": world,
            "world_definitions": world_definitions,
            "reactions": reactions,
            "characters": characters,
        }

    def _query_runtime_data(self, runtime_id: str) -> Dict[str, Any]:
        runtime_data = self.session.exec(
            select(RuntimeData).where(RuntimeData.id == runtime_id)
        ).first()

        runtime_history = list(self.session.exec(
            select(RawRequestRespondPair).where(
                RawRequestRespondPair.runtime_id == runtime_id
            )
        ).all())

        return {
            "runtime_data": runtime_data,
            "runtime_history": runtime_history,
        }

    def _bm25(self, runtime_id: str, query: str) -> SearchResult:
        world_id = self._resolve_world_id(runtime_id)
        if not world_id:
            return SearchResult()

        static = self._query_static_templates(world_id)
        runtime = self._query_runtime_data(runtime_id)

        ts_query = func.plainto_tsquery("simple", query)

        return SearchResult(
            world=static["world"],
            world_definitions=self._bm25_filter_definitions(
                static["world_definitions"], query, ts_query
            ),
            reactions=self._bm25_filter_reactions(
                static["reactions"], query, ts_query
            ),
            characters=self._bm25_filter_characters(
                static["characters"], query, ts_query
            ),
            runtime_data=runtime["runtime_data"],
            runtime_history=self._bm25_filter_history(
                runtime["runtime_history"], query, ts_query
            ),
        )

    def _bm25_filter_definitions(
        self, items: List[WorldDefinition], query: str, ts_query
    ) -> List[WorldDefinition]:
        if not query or not items:
            return items
        stmt = (
            select(WorldDefinition)
            .where(col(WorldDefinition.id).in_([d.id for d in items]))
            .where(func.to_tsvector("simple", WorldDefinition.value).op("@@")(ts_query))
        )

        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _bm25_filter_reactions(
        self, items: List[ReactionDefinition], query: str, ts_query
    ) -> List[ReactionDefinition]:
        if not query or not items:
            return items
        combined_vector = func.to_tsvector(
            "simple",
            func.coalesce(ReactionDefinition.name, "")
            + " " + func.coalesce(ReactionDefinition.description, "")
            + " " + func.coalesce(ReactionDefinition.user_reaction, "")
            + " " + func.coalesce(ReactionDefinition.target_reaction, ""),
        )
        stmt = (
            select(ReactionDefinition)
            .where(col(ReactionDefinition.id).in_([r.id for r in items]))
            .where(combined_vector.op("@@")(ts_query))
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _bm25_filter_characters(
        self, items: List[CharacterDefinition], query: str, ts_query
    ) -> List[CharacterDefinition]:
        if not query or not items:
            return items
        combined_vector = func.to_tsvector(
            "simple",
            func.coalesce(CharacterDefinition.name, "")
            + " " + func.coalesce(CharacterDefinition.description, ""),
        )
        stmt = (
            select(CharacterDefinition)
            .where(col(CharacterDefinition.id).in_([c.id for c in items]))
            .where(combined_vector.op("@@")(ts_query))
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _bm25_filter_history(
        self, items: List[RawRequestRespondPair], query: str, ts_query
    ) -> List[RawRequestRespondPair]:
        if not query or not items:
            return items
        combined_vector = func.to_tsvector(
            "simple",
            func.coalesce(RawRequestRespondPair.request, "")
            + " " + func.coalesce(RawRequestRespondPair.respond, "")
            + " " + func.coalesce(RawRequestRespondPair.event_brief, ""),
        )
        stmt = (
            select(RawRequestRespondPair)
            .where(col(RawRequestRespondPair.id).in_([h.id for h in items]))
            .where(combined_vector.op("@@")(ts_query))
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _relation(self, runtime_id: str, query: str) -> SearchResult:
        world_id = self._resolve_world_id(runtime_id)
        if not world_id:
            return SearchResult()

        static = self._query_static_templates(world_id)
        runtime = self._query_runtime_data(runtime_id)

        pattern = f"%{query}%"

        return SearchResult(
            world=static["world"],
            world_definitions=self._relation_filter_definitions(
                static["world_definitions"], pattern
            ),
            reactions=self._relation_filter_reactions(
                static["reactions"], pattern
            ),
            characters=self._relation_filter_characters(
                static["characters"], pattern
            ),
            runtime_data=runtime["runtime_data"],
            runtime_history=self._relation_filter_history(
                runtime["runtime_history"], pattern
            ),
        )

    def _relation_filter_definitions(
        self, items: List[WorldDefinition], pattern: str
    ) -> List[WorldDefinition]:
        if not items:
            return items
        stmt = (
            select(WorldDefinition)
            .where(col(WorldDefinition.id).in_([d.id for d in items]))
            .where(col(WorldDefinition.value).ilike(pattern))
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _relation_filter_reactions(
        self, items: List[ReactionDefinition], pattern: str
    ) -> List[ReactionDefinition]:
        if not items:
            return items
        stmt = (
            select(ReactionDefinition)
            .where(col(ReactionDefinition.id).in_([r.id for r in items]))
            .where(
                or_(
                    col(ReactionDefinition.name).ilike(pattern),
                    col(ReactionDefinition.description).ilike(pattern),
                    col(ReactionDefinition.user_reaction).ilike(pattern),
                    col(ReactionDefinition.target_reaction).ilike(pattern),
                )
            )
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _relation_filter_characters(
        self, items: List[CharacterDefinition], pattern: str
    ) -> List[CharacterDefinition]:
        if not items:
            return items
        stmt = (
            select(CharacterDefinition)
            .where(col(CharacterDefinition.id).in_([c.id for c in items]))
            .where(
                or_(
                    col(CharacterDefinition.name).ilike(pattern),
                    col(CharacterDefinition.description).ilike(pattern),
                )
            )
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _relation_filter_history(
        self, items: List[RawRequestRespondPair], pattern: str
    ) -> List[RawRequestRespondPair]:
        if not items:
            return items
        stmt = (
            select(RawRequestRespondPair)
            .where(col(RawRequestRespondPair.id).in_([h.id for h in items]))
            .where(
                or_(
                    col(RawRequestRespondPair.request).ilike(pattern),
                    col(RawRequestRespondPair.respond).ilike(pattern),
                    col(RawRequestRespondPair.event_brief).ilike(pattern),
                )
            )
        )
        # noinspection PyTypeChecker
        return list(self.session.exec(stmt).all())

    def _vector(self, runtime_id: str, query: str) -> SearchResult:
        _ = self, runtime_id, query
        return SearchResult()

    @staticmethod
    def _merge_results(results: List[SearchResult]) -> SearchResult:
        if not results:
            return SearchResult()

        world = None
        runtime_data = None
        seen_def_ids: set = set()
        seen_reaction_ids: set = set()
        seen_char_ids: set = set()
        seen_history_ids: set = set()
        merged_definitions: List[WorldDefinition] = []
        merged_reactions: List[ReactionDefinition] = []
        merged_characters: List[CharacterDefinition] = []
        merged_history: List[RawRequestRespondPair] = []

        for r in results:
            if r.world and not world:
                world = r.world

            if r.runtime_data and not runtime_data:
                runtime_data = r.runtime_data

            for wd in r.world_definitions:
                if wd.id not in seen_def_ids:
                    merged_definitions.append(wd)
                    seen_def_ids.add(wd.id)

            for rx in r.reactions:
                if rx.id not in seen_reaction_ids:
                    merged_reactions.append(rx)
                    seen_reaction_ids.add(rx.id)

            for ch in r.characters:
                if ch.id not in seen_char_ids:
                    merged_characters.append(ch)
                    seen_char_ids.add(ch.id)

            for rh in r.runtime_history:
                if rh.id not in seen_history_ids:
                    merged_history.append(rh)
                    seen_history_ids.add(rh.id)

        return SearchResult(
            world=world,
            world_definitions=merged_definitions,
            reactions=merged_reactions,
            characters=merged_characters,
            runtime_data=runtime_data,
            runtime_history=merged_history,
        )
