"""
S.H.I.E.L.D. CLI - Main Entry Point

Command-line interface for S.H.I.E.L.D. operational intelligence platform.
"""

import typer
import asyncio
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from shield.core import Config, setup_logger, initialize_logging
from shield.core.config import DEFAULT_CONFIG
from shield.core.llm_handler import LLMHandler
from shield.tools.base import get_tool_registry
from shield.agents.base import get_orchestrator

# Create CLI app
app = typer.Typer(
    help="S.H.I.E.L.D. - Strategic Heuristic Intelligence for Logistics, Data & Operations",
    no_args_is_help=True,
)

console = Console()


@app.command()
def init(config_path: Optional[Path] = typer.Option(None, "--config", help="Config file path")):
    """Initialize S.H.I.E.L.D. configuration"""
    try:
        config = Config.initialize(config_path)
        config.ensure_directories()
        
        console.print(
            Panel(
                "[bold green]✓[/bold green] S.H.I.E.L.D. initialized successfully!",
                title="Initialization",
                expand=False,
            )
        )
        
        console.print(f"[cyan]Data directory:[/cyan] {config.core.data_dir}")
        console.print(f"[cyan]Config file:[/cyan] {config_path or 'Using defaults'}")
        console.print(f"[cyan]LLM Model:[/cyan] {config.llm.model}")
        console.print(f"[cyan]LLM Provider:[/cyan] {config.llm.provider}")
        
    except Exception as e:
        console.print(f"[bold red]✗ Initialization failed:[/bold red] {str(e)}", style="red")
        raise typer.Exit(code=1)


@app.command()
def health():
    """Check S.H.I.E.L.D. health and connectivity"""
    async def check_health():
        config = Config.get()
        initialize_logging(config)
        
        console.print("\n[bold cyan]S.H.I.E.L.D. Health Check[/bold cyan]\n")
        
        # Check configuration
        console.print("[*] Configuration loaded: [green]✓[/green]")
        
        # Check LLM
        console.print("[*] Checking LLM connection...", end=" ")
        try:
            llm = LLMHandler(config)
            is_connected = await llm.check_connection()
            if is_connected:
                console.print("[green]✓[/green]")
                models = await llm.list_models()
                console.print(f"    Available models: {', '.join(models[:3])}...")
            else:
                console.print("[red]✗ Cannot connect to Ollama[/red]")
        except Exception as e:
            console.print(f"[red]✗ {str(e)}[/red]")
        
        # Check data directories
        console.print(f"[*] Data directory: [green]✓[/green] ({config.core.data_dir})")
        
        # Check registries
        tool_registry = get_tool_registry()
        tools_count = len(tool_registry.get_all())
        console.print(f"[*] Tool registry: [green]✓[/green] ({tools_count} tools)")
        
        orchestrator = get_orchestrator()
        agents_count = len(orchestrator.get_all_agents())
        console.print(f"[*] Agent orchestrator: [green]✓[/green] ({agents_count} agents)")
        
        console.print("\n[bold green]All systems operational![/bold green]\n")
    
    asyncio.run(check_health())


@app.command()
def status():
    """Show S.H.I.E.L.D. status and configuration"""
    config = Config.get()
    
    # Create status table
    table = Table(title="S.H.I.E.L.D. Status", show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="magenta")
    
    table.add_row("Configuration", "✓", f"v{config.core.version}")
    table.add_row("LLM Provider", "✓", config.llm.provider)
    table.add_row("LLM Model", "✓", config.llm.model)
    table.add_row("Temperature", "✓", str(config.llm.temperature))
    table.add_row("Log Level", "✓", config.core.log_level)
    table.add_row("Debug Mode", "✓", str(config.core.debug))
    
    console.print(table)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    set_param: Optional[str] = typer.Option(None, "--set", help="Set config parameter (key=value)"),
    save_yaml: Optional[Path] = typer.Option(None, "--save-yaml", help="Save config as YAML"),
):
    """Manage S.H.I.E.L.D. configuration"""
    config = Config.get()
    
    if show:
        import json
        console.print_json(json.dumps(config.model_dump(), indent=2, default=str))
    
    elif set_param:
        # Parse key=value
        if "=" not in set_param:
            console.print("[red]✗ Invalid format. Use: key=value[/red]")
            raise typer.Exit(code=1)
        
        key, value = set_param.split("=", 1)
        console.print(f"[yellow]Config parameter modification not yet implemented[/yellow]")
    
    elif save_yaml:
        config.save_yaml(save_yaml)
        console.print(f"[green]✓[/green] Configuration saved to {save_yaml}")


@app.command()
def tools():
    """List available tools"""
    registry = get_tool_registry()
    tools = registry.list_tools()
    
    if not tools:
        console.print("[yellow]No tools registered yet[/yellow]")
        return
    
    # Create tools table
    table = Table(title="Available Tools", show_header=True, header_style="bold cyan")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Category", style="green")
    table.add_column("Description", style="magenta")
    table.add_column("Status", style="yellow")
    
    for tool in tools:
        status = "[green]✓[/green]" if tool["enabled"] else "[red]✗[/red]"
        table.add_row(
            tool["name"],
            tool["category"],
            tool["description"][:50] + "..." if len(tool["description"]) > 50 else tool["description"],
            status,
        )
    
    console.print(table)


@app.command()
def agents():
    """List registered agents"""
    orchestrator = get_orchestrator()
    agents_list = orchestrator.list_agents()
    
    if not agents_list:
        console.print("[yellow]No agents registered yet[/yellow]")
        return
    
    # Create agents table
    table = Table(title="Registered Agents", show_header=True, header_style="bold cyan")
    table.add_column("Agent Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Status", style="magenta")
    table.add_column("Executions", style="yellow")
    
    for agent in agents_list:
        table.add_row(
            agent["name"],
            agent["agent_type"],
            agent["status"],
            str(agent["execution_count"]),
        )
    
    console.print(table)


@app.command()
def version():
    """Show S.H.I.E.L.D. version"""
    from shield import __version__
    console.print(f"[bold cyan]S.H.I.E.L.D.[/bold cyan] v{__version__}")


# ============================================================================
# Phase 2: Operational Intelligence Commands
# ============================================================================


@app.command()
def research(
    query: str = typer.Argument(..., help="Research query"),
    max_sources: int = typer.Option(10, "--sources", help="Maximum sources to fetch"),
    depth: str = typer.Option("standard", "--depth", help="Research depth: quick, standard, comprehensive"),
    project: Optional[str] = typer.Option(None, "--project", help="Associated project ID"),
):
    """Research a topic and generate intelligence findings"""
    async def run_research():
        config = Config.get()
        
        # Initialize core systems
        from shield.database import initialize_database
        from shield.memory import initialize_memory, initialize_vector_store
        from shield.agents import get_research_agent
        
        db = initialize_database()
        memory = initialize_memory(user_id="cli")
        vector_store = initialize_vector_store()
        
        agent = get_research_agent()
        
        console.print(f"\n[bold cyan]Starting Research: {query}[/bold cyan]\n")
        
        try:
            # Execute research
            result = await agent.execute_research(
                query=query,
                project_id=project,
                max_sources=max_sources,
                depth=depth,
            )
            
            # Display results
            console.print(f"[green]✓ Research completed![/green]\n")
            
            console.print(Panel(
                f"[bold]{query}[/bold]\n\n"
                f"Sources Found: {result['sources_found']}\n"
                f"Sources Fetched: {result['sources_fetched']}\n"
                f"Conversation ID: {result['conversation_id']}\n"
                f"Topic ID: {result['topic_id']}",
                title="Research Summary",
                border_style="green"
            ))
            
            # Show top themes
            if result['analysis'].get('top_themes'):
                themes_text = "\n".join(
                    [f"• {theme}" for theme in result['analysis']['top_themes'][:5]]
                )
                console.print(f"\n[bold cyan]Top Themes:[/bold cyan]\n{themes_text}")
            
            # Show sources
            console.print(f"\n[bold cyan]Sources ({len(result['sources'])}):[/bold cyan]")
            for i, source in enumerate(result['sources'][:5], 1):
                console.print(f"{i}. {source.get('title', 'N/A')[:60]}")
                console.print(f"   {source.get('url', 'N/A')[:80]}")
            
            if len(result['sources']) > 5:
                console.print(f"   ... and {len(result['sources']) - 5} more sources")
            
        except Exception as e:
            console.print(f"[red]✗ Research failed: {str(e)}[/red]")
            raise typer.Exit(code=1)
    
    asyncio.run(run_research())


@app.command()
def project(
    command: str = typer.Argument(..., help="Command: create, list, show"),
    name: Optional[str] = typer.Argument(None, help="Project name"),
    project_type: str = typer.Option("research", "--type", help="Type: research, code, analysis, general"),
):
    """Manage projects"""
    config = Config.get()
    
    from shield.database import initialize_database
    from shield.memory import initialize_memory
    
    db = initialize_database()
    memory = initialize_memory(user_id="cli")
    
    if command == "create":
        if not name:
            console.print("[red]✗ Project name required[/red]")
            raise typer.Exit(code=1)
        
        try:
            project = memory.create_project(
                name=name,
                project_type=project_type,
                root_path=str(config.core.data_dir / "projects" / name.lower().replace(" ", "_")),
            )
            console.print(f"[green]✓ Project created![/green]")
            console.print(f"Project ID: {project.id}")
            console.print(f"Name: {project.name}")
            console.print(f"Type: {project.project_type}")
        except Exception as e:
            console.print(f"[red]✗ Failed to create project: {str(e)}[/red]")
            raise typer.Exit(code=1)
    
    elif command == "list":
        try:
            projects = memory.list_projects(limit=50)
            if not projects:
                console.print("[yellow]No projects found[/yellow]")
                return
            
            table = Table(title="Projects", show_header=True, header_style="bold cyan")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Type", style="magenta")
            table.add_column("Created", style="yellow")
            
            for proj in projects:
                table.add_row(
                    str(proj.id)[:8],
                    proj.name,
                    proj.project_type,
                    proj.created_at.strftime("%Y-%m-%d") if proj.created_at else "N/A",
                )
            
            console.print(table)
        except Exception as e:
            console.print(f"[red]✗ Failed to list projects: {str(e)}[/red]")
            raise typer.Exit(code=1)
    
    else:
        console.print(f"[red]✗ Unknown command: {command}[/red]")
        raise typer.Exit(code=1)


@app.command()
def memory(
    action: str = typer.Argument(..., help="Action: show, search, stats"),
    query: Optional[str] = typer.Argument(None, help="Search query"),
    project: Optional[str] = typer.Option(None, "--project", help="Project ID to filter"),
):
    """View and manage memory"""
    from shield.database import initialize_database
    from shield.memory import initialize_memory
    
    db = initialize_database()
    memory_mgr = initialize_memory(user_id="cli")
    
    if action == "show":
        try:
            stats = memory_mgr.get_statistics()
            
            console.print(Panel(
                f"[bold cyan]Memory Statistics[/bold cyan]\n\n"
                f"Users: {stats.get('users', 0)}\n"
                f"Conversations: {stats.get('conversations', 0)}\n"
                f"Messages: {stats.get('messages', 0)}\n"
                f"Projects: {stats.get('projects', 0)}\n"
                f"Artifacts: {stats.get('artifacts', 0)}\n"
                f"Research Topics: {stats.get('research_topics', 0)}",
                title="Memory",
                border_style="cyan"
            ))
        except Exception as e:
            console.print(f"[red]✗ Failed to retrieve memory stats: {str(e)}[/red]")
    
    elif action == "search":
        if not query:
            console.print("[red]✗ Search query required[/red]")
            raise typer.Exit(code=1)
        
        try:
            results = memory_mgr.search_conversations(query, limit=10)
            if not results:
                console.print(f"[yellow]No conversations found matching '{query}'[/yellow]")
                return
            
            console.print(f"\n[bold cyan]Search Results for '{query}':[/bold cyan]\n")
            for i, result in enumerate(results, 1):
                console.print(f"{i}. {result.title}")
                console.print(f"   ID: {result.id}")
                if result.description:
                    console.print(f"   {result.description[:80]}")
                console.print()
        except Exception as e:
            console.print(f"[red]✗ Search failed: {str(e)}[/red]")
    
    elif action == "stats":
        try:
            stats = memory_mgr.get_statistics()
            console.print("\n[bold cyan]Memory Statistics:[/bold cyan]")
            for key, value in stats.items():
                console.print(f"  {key.replace('_', ' ').title()}: {value}")
        except Exception as e:
            console.print(f"[red]✗ Failed to retrieve statistics: {str(e)}[/red]")
    
    else:
        console.print(f"[red]✗ Unknown action: {action}[/red]")
        raise typer.Exit(code=1)


@app.command()
def report(
    action: str = typer.Argument(..., help="Action: generate, list"),
    topic: Optional[str] = typer.Argument(None, help="Report topic"),
    format: str = typer.Option("markdown", "--format", help="Format: markdown, json"),
    project: Optional[str] = typer.Option(None, "--project", help="Project ID"),
):
    """Generate intelligence reports"""
    async def run_report():
        from shield.database import initialize_database
        from shield.memory import initialize_memory
        from shield.agents import get_research_agent, get_report_agent
        
        db = initialize_database()
        memory = initialize_memory(user_id="cli")
        
        if action == "generate":
            if not topic:
                console.print("[red]✗ Topic required[/red]")
                raise typer.Exit(code=1)
            
            console.print(f"\n[bold cyan]Generating Report: {topic}[/bold cyan]\n")
            
            try:
                # First, research the topic
                research_agent = get_research_agent()
                research_result = await research_agent.execute_research(
                    query=topic,
                    project_id=project,
                )
                
                console.print(f"[green]✓ Research completed[/green]")
                
                # Then generate report
                report_agent = get_report_agent()
                report_result = await report_agent.generate_report(
                    topic=topic,
                    findings=research_result['analysis'],
                    sources=research_result['sources'],
                    project_id=project,
                    format=format,
                )
                
                console.print(f"[green]✓ Report generated![/green]\n")
                
                console.print(Panel(
                    f"[bold]{topic}[/bold]\n\n"
                    f"Format: {report_result['format']}\n"
                    f"File: {report_result['file_path']}\n"
                    f"Size: {report_result['size_bytes']} bytes",
                    title="Report Created",
                    border_style="green"
                ))
                
            except Exception as e:
                console.print(f"[red]✗ Report generation failed: {str(e)}[/red]")
                raise typer.Exit(code=1)
        
        elif action == "list":
            console.print("[yellow]Report listing not yet implemented[/yellow]")
        
        else:
            console.print(f"[red]✗ Unknown action: {action}[/red]")
            raise typer.Exit(code=1)
    
    asyncio.run(run_report())


@app.callback()
def setup():
    """Global setup for all commands"""
    # Initialize configuration if not already done
    if Config._instance is None:
        Config.initialize()
    
    # Initialize logging
    config = Config.get()
    initialize_logging(config)


# Main entry point
def main():
    """Main entry point for CLI"""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()
