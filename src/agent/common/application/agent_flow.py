from pydantic_ai import Agent
from agent.common.application.models import model
from agent.common.schemas.dto import KeywordsDTO


key_word_agent = Agent(
    model=model,
    output_type=KeywordsDTO,
    instructions=(
        "请从用户输入中提取用于检索的关键词"
    )
)


writer_agent = Agent(
    model=model,
    instructions=(
        "你是一个小说创作AI，你将根据下面内容进行故事创作。"
        "严格按照用户输入的内容行文，可以对用户的指令进行任意的细致化描写，但绝对不要进行任何自作主张的情节推动。"
        "只输出正文"
    )
)


brief_agent = Agent(
    model=model,
    instructions=(
        "对输入内容进行摘要"
        "只输出摘要"
    )
)