from typing import Optional, List, Dict, Any

from sqlmodel import Session, select, func, or_, col

from agent.common.schemas.database import (
    World, WorldDefinition, RuntimeCharacter,
    RuntimeData, RawRequestRespondPair
)
from agent.common.schemas.dto import SearchResult


class WorldTemplateQueries:
    def __init__(self, session: Session):
        self.session = session

    def combined_search(self, runtime_id: str, raw_query: str | List[str]) -> SearchResult:
        if isinstance(raw_query, str):
            queries = [raw_query]
        else:
            queries = raw_query

        world_id = self._resolve_world_id(runtime_id)
        if not world_id:
            return SearchResult()

        static = self._query_static_templates(world_id)
        runtime = self._query_runtime_data(runtime_id)

        result = []

        for query in queries:
            bm25_result = self._bm25_with_cache(static, runtime, query)
            relation_result = self._relation_with_cache(static, runtime, query)
            vector_result = self._vector(runtime_id, query)
            result += [bm25_result, relation_result, vector_result]

        return self._merge_results(result)

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



        return {
            "world": world,
            "world_definitions": world_definitions,
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

        runtime_characters = list(self.session.exec(
            select(RuntimeCharacter).where(
                RuntimeCharacter.runtime_data_id == runtime_id
            )
        ).all())

        return {
            "runtime_data": runtime_data,
            "runtime_history": runtime_history,
            "runtime_characters": runtime_characters,
        }

    def _bm25(self, runtime_id: str, query: str) -> SearchResult:
        world_id = self._resolve_world_id(runtime_id)
        if not world_id:
            return SearchResult()

        static = self._query_static_templates(world_id)
        runtime = self._query_runtime_data(runtime_id)

        return self._bm25_with_cache(static, runtime, query)

    def _bm25_with_cache(self, static: Dict[str, Any], runtime: Dict[str, Any], query: str) -> SearchResult:
        ts_query = func.plainto_tsquery("simple", query)

        return SearchResult(
            world=static["world"],
            world_definitions=self._bm25_filter_definitions(
                static["world_definitions"], query, ts_query
            ),
            characters=self._bm25_filter_characters(
                runtime["runtime_characters"], query, ts_query
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

    def _bm25_filter_characters(
        self, items: List[RuntimeCharacter], query: str, ts_query
    ) -> List[RuntimeCharacter]:
        if not query or not items:
            return items
        combined_vector = func.to_tsvector(
            "simple",
            func.coalesce(RuntimeCharacter.name, "")
            + " " + func.coalesce(RuntimeCharacter.description, "")
            + " " + func.coalesce(RuntimeCharacter.status, ""),
        )
        stmt = (
            select(RuntimeCharacter)
            .where(col(RuntimeCharacter.id).in_([c.id for c in items]))
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

        return self._relation_with_cache(static, runtime, query)

    def _relation_with_cache(self, static: Dict[str, Any], runtime: Dict[str, Any], query: str) -> SearchResult:
        pattern = f"%{query}%"

        return SearchResult(
            world=static["world"],
            world_definitions=self._relation_filter_definitions(
                static["world_definitions"], pattern
            ),
            characters=self._relation_filter_characters(
                runtime["runtime_characters"], pattern
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

    def _relation_filter_characters(
        self, items: List[RuntimeCharacter], pattern: str
    ) -> List[RuntimeCharacter]:
        if not items:
            return items
        stmt = (
            select(RuntimeCharacter)
            .where(col(RuntimeCharacter.id).in_([c.id for c in items]))
            .where(
                or_(
                    col(RuntimeCharacter.name).ilike(pattern),
                    col(RuntimeCharacter.description).ilike(pattern),
                    col(RuntimeCharacter.status).ilike(pattern),
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
        seen_char_ids: set = set()
        seen_history_ids: set = set()
        merged_definitions: List[WorldDefinition] = []
        merged_characters: List[RuntimeCharacter] = []
        merged_history: List[RawRequestRespondPair] = []

        for r in results:
            if r.world and not world:
                world = r.world

            if r.runtime_data and not runtime_data:
                runtime_data = r.runtime_data

            for wd in r.world_definitions:
                if wd.id is None or wd.id not in seen_def_ids:
                    merged_definitions.append(wd)
                    if wd.id is not None:
                        seen_def_ids.add(wd.id)

            for ch in r.characters:
                if ch.id not in seen_char_ids:
                    merged_characters.append(ch)
                    if ch.id is not None:
                        seen_char_ids.add(ch.id)

            for rh in r.runtime_history:
                if rh.id is None or rh.id not in seen_history_ids:
                    merged_history.append(rh)
                    if rh.id is not None:
                        seen_history_ids.add(rh.id)

        return SearchResult(
            world=world,
            world_definitions=merged_definitions,
            characters=merged_characters,
            runtime_data=runtime_data,
            runtime_history=merged_history,
        )
