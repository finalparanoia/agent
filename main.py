from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from agent.common.schemas.database import init_db, get_db_session
from agent.common.repo.template_cmd import WorldTemplateCommands
from agent.common.schemas.dto import (
    WorldDefinitionDTO, ReactionDefinitionDTO, CharacterDefinitionDTO
)
from agent.common.application.runtime import RuntimeManagement

console = Console()


def seed_world(cmd: WorldTemplateCommands) -> str:
    console.rule("[bold cyan]Step 1: 创建世界模板数据")

    world_id = cmd.create_world(name="赛博朋克都市-新上海")
    console.print(f"  [green]✓[/] 创建 World: {world_id}")

    definitions = [
        "新上海是一座建于2087年的超级都市，由三层立体结构组成：地面层（旧城）、中层（商业区）、顶层（精英居住区）",
        "城市由AI议会统治，人类与仿生人共存，仿生人拥有有限公民权",
        "城市中流通的货币为信用点，黑市则使用加密代币'幽灵币'",
        "网络空间'深网'与现实世界通过神经接口连接，黑客被称为'潜行者'",
    ]
    for value in definitions:
        cmd.world_define(WorldDefinitionDTO(world_id=world_id, value=value))
    console.print(f"  [green]✓[/] 写入 {len(definitions)} 条世界设定")

    reactions = [
        ReactionDefinitionDTO(
            world_id=world_id,
            name="黑市交易",
            description="在地下黑市进行非法物品或信息的交易",
            user_reaction="尝试在黑市寻找稀有物品",
            target_reaction="黑市商人审视来者，低声报出价格",
        ),
        ReactionDefinitionDTO(
            world_id=world_id,
            name="神经骇入",
            description="通过神经接口入侵目标系统或他人意识",
            user_reaction="启动骇入程序，潜入目标网络",
            target_reaction="防火墙发出警报，数据流中出现异常波动",
        ),
        ReactionDefinitionDTO(
            world_id=world_id,
            name="区域冲突",
            description="不同势力在城区边界发生的武装对峙或交火",
            user_reaction="卷入冲突，选择阵营或试图调停",
            target_reaction="枪声在巷道中回响，霓虹灯碎片如雨落下",
        ),
    ]
    for r in reactions:
        cmd.reaction_define(r)
    console.print(f"  [green]✓[/] 写入 {len(reactions)} 组反应三元组")

    characters = [
        CharacterDefinitionDTO(
            name="零",
            description="神秘的潜行者，擅长神经骇入，左臂装有军用级义体接口，总是穿着一件褪色的长风衣",
        ),
        CharacterDefinitionDTO(
            name="薇薇安",
            description="黑市情报贩子，表面经营一家复古唱片店，实际掌握着新上海最大的地下信息网络",
        ),
        CharacterDefinitionDTO(
            name="K-7",
            description="仿生人侦探，AI议会直属调查员，拥有最高权限的执法模块，但对人类情感充满好奇",
        ),
    ]
    for c in characters:
        cmd.character_define(c)
    console.print(f"  [green]✓[/] 写入 {len(characters)} 个角色")

    return world_id


def run_roleplay(session, world_id: str):
    console.rule("[bold cyan]Step 2: 初始化运行时")

    rt = RuntimeManagement(session)
    runtime_id = rt.initialize(world_id)
    console.print(f"  [green]✓[/] Runtime 初始化完成: {runtime_id}")

    console.rule("[bold cyan]Step 3: AI RolePlay")

    rounds = [
        "我走进了薇薇安的唱片店，推开门时铃铛叮当作响。我低声说：'我需要关于K-7的情报。'",
        "我决定尝试骇入城市监控网络，追踪K-7的位置。我启动了神经接口，意识开始沉入深网。",
    ]

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
        world_id = seed_world(cmd)
        session.flush()
        run_roleplay(session, world_id)

    console.print()
    console.print("[bold green]✅ 全流程测试完成[/]")


if __name__ == "__main__":
    main()
