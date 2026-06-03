from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from typing import Tuple, List
from agent.common.schemas.database import init_db, get_db_session
from agent.common.repo.template_cmd import WorldTemplateCommands
from agent.common.schemas.dto import (
    WorldDefinitionDTO, CharacterDefinitionDTO,
    WorldBook
)
from agent.common.application.runtime import RuntimeManagement
from agent.define.sfw import WORLD_BOOK_DATA, ROUND

console = Console()


def seed_world(cmd: WorldTemplateCommands, book_data: dict) -> Tuple[str, List[str]]:
    console.rule("[bold cyan]Step 1: 创建世界模板数据")

    book = WorldBook.model_validate(book_data)

    world_id = cmd.create_world(name=book.name)
    console.print(f"  [green]✓[/] 创建 World: {world_id}")

    for d in book.definitions:
        cmd.world_define(WorldDefinitionDTO(world_id=world_id, value=d.value))
    console.print(f"  [green]✓[/] 写入 {len(book.definitions)} 条世界设定")
    character_ids = []
    for c in book.characters:
        character_id = cmd.character_define(CharacterDefinitionDTO(
            world_id=world_id,
            name=c.name,
            description=c.description,
        ))
        character_ids.append(character_id)
    console.print(f"  [green]✓[/] 写入 {len(book.characters)} 个角色")

    return world_id, character_ids


def run_roleplay(session, world_id: str, character_ids: List[str]):
    console.rule("[bold cyan]Step 2: 初始化运行时")

    rt = RuntimeManagement(session)
    runtime_id = rt.initialize(world_id, character_ids=character_ids)
    console.print(f"  [green]✓[/] Runtime 初始化完成: {runtime_id}")

    console.rule("[bold cyan]Step 3: AI RolePlay")

    rounds = ROUND

    for i, user_input in enumerate(rounds, 1):
        console.print()
        console.print(Panel(
            f"[bold yellow]第 {i} 轮[/]\n\n{user_input}",
            title="[bold magenta]👤 用户输入[/]",
            border_style="magenta",
        ))

        with console.status("[bold green]AI 正在思考...[/]", spinner="dots"):
            respond = rt.chat(user_input)

        console.print(Panel(
            Markdown(respond),
            title="[bold cyan]🤖 AI 回复[/]",
            border_style="cyan",
        ))

    console.rule("[bold cyan]Step 4: 运行时历史记录")

    from agent.common.repo.template_query import WorldTemplateQueries
    query = WorldTemplateQueries(session)
    result = query.combined_search(runtime_id, "")

    table = Table(title="交互历史", show_lines=True)
    table.add_column("轮次", style="bold", width=6)
    table.add_column("用户输入", style="magenta", max_width=40)
    table.add_column("AI 回复", style="cyan", max_width=60)

    for idx, rh in enumerate(result.runtime_history, 1):
        table.add_row(str(idx), rh.request, rh.respond)

    console.print(table)


def main():
    init_db()

    with get_db_session() as session:
        cmd = WorldTemplateCommands(session)
        world_id, character_ids = seed_world(cmd, WORLD_BOOK_DATA)
        session.flush()
        run_roleplay(session, world_id, character_ids)

    console.print()
    console.print("[bold green]✅ 全流程测试完成[/]")


if __name__ == "__main__":
    main()
