from agent.common.schemas.database import init_db, get_test_session, World
from agent.common.schemas.dto import WorldDefinitionDTO, ReactionDefinitionDTO, CharacterDefinitionDTO
from agent.common.application.template_cmd import WorldTemplateCommands

init_db()
s = next(get_test_session())


w = WorldTemplateCommands(s)


world_id = w.create_world(name="test")
w.rename(world_id, "rename_test")

s.commit()
