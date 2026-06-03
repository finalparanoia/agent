from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from agent.common.config import SETTINGS


model = OpenAIResponsesModel(SETTINGS.llm_model, provider=OpenAIProvider(
    base_url=SETTINGS.llm_api_base, api_key=SETTINGS.llm_api_key
))
