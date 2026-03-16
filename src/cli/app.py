from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.pipeline.orchestrator import StoryPipeline
from src.schemas.outline import StoryOutline
from src.utils.logging import setup_logging

console = Console()


def display_outline(outline: StoryOutline) -> None:
    console.print(Panel("[bold]Story Outline[/bold]", style="blue"))

    if outline.title_suggestions:
        console.print("[bold]Title Ideas:[/bold]")
        for t in outline.title_suggestions:
            console.print(f"  • {t}")
        console.print()

    if outline.moral_lesson:
        console.print(f"[bold]Moral Lesson:[/bold] {outline.moral_lesson}\n")

    # Characters table
    if outline.characters:
        table = Table(title="Characters")
        table.add_column("Name", style="cyan")
        table.add_column("Age")
        table.add_column("Personality")
        table.add_column("Background")
        for c in outline.characters:
            table.add_row(c.name, str(c.age), c.personality, c.background)
        console.print(table)
        console.print()

    # Cultural elements
    if outline.cultural_elements:
        console.print("[bold]Cultural Elements:[/bold]")
        for ce in outline.cultural_elements:
            console.print(f"  [{ce.category}] {ce.detail}")
        console.print()

    # Plot
    plot = outline.refined_plot or outline.plot
    if plot:
        console.print(Panel(f"[bold]Beginning:[/bold]\n{plot.beginning}", title="Plot"))
        console.print(Panel(f"[bold]Middle:[/bold]\n{plot.middle}"))
        console.print(Panel(f"[bold]End:[/bold]\n{plot.end}"))

    # Environment
    if outline.environment:
        env = outline.environment
        console.print(Panel(
            f"[bold]Sensory:[/bold] {env.sensory_details}\n"
            f"[bold]Time/Weather:[/bold] {env.time_and_weather}\n"
            f"[bold]Local Features:[/bold] {env.local_features}",
            title="Environment",
        ))


def review_outline(outline: StoryOutline) -> StoryOutline:
    display_outline(outline)

    while True:
        console.print("\n[bold]Actions:[/bold] [a]pprove  [e]dit  [r]eject")
        choice = click.prompt("Choice", type=click.Choice(["a", "e", "r"]))

        if choice == "a":
            console.print("[green]Outline approved.[/green]")
            return outline
        elif choice == "e":
            data = json.dumps(outline.model_dump(), indent=2, ensure_ascii=False)
            editor = os.environ.get("EDITOR", "nano")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write(data)
                tmp_path = f.name
            try:
                subprocess.run([editor, tmp_path], check=True)
                with open(tmp_path) as f:
                    edited = json.load(f)
                outline = StoryOutline.model_validate(edited)
                console.print("[green]Outline updated.[/green]")
                display_outline(outline)
            except Exception as e:
                console.print(f"[red]Edit failed: {e}[/red]")
            finally:
                os.unlink(tmp_path)
        elif choice == "r":
            console.print("[yellow]Outline rejected. Regenerating...[/yellow]")
            return None  # type: ignore[return-value]


@click.group()
def cli() -> None:
    """Children's Story Generation Pipeline"""
    pass


@cli.command()
@click.option("--location", default="", help="Story setting location")
@click.option("--culture", default="", help="Cultural context")
@click.option(
    "--grade",
    default=4,
    type=click.IntRange(3, 6),
    help="Target grade level (3-6)",
)
@click.option(
    "--config-dir",
    default="config",
    type=click.Path(exists=True),
    help="Config directory path",
)
@click.option("--fast", is_flag=True, help="Use Flash for critique instead of Pro (Gemini only)")
@click.option("--no-review", is_flag=True, help="Skip HITL outline review")
@click.option("--resume", "resume_run_id", default=None, help="Resume a previous run by ID")
@click.option(
    "--provider",
    type=click.Choice(["gemini", "claude"], case_sensitive=False),
    default="gemini",
    help="LLM provider to use (default: gemini)",
)
@click.option("--log-level", default="INFO", help="Logging level")
def generate(
    location: str,
    culture: str,
    grade: int,
    config_dir: str,
    fast: bool,
    no_review: bool,
    resume_run_id: str | None,
    provider: str,
    log_level: str,
) -> None:
    """Generate a children's story through the full pipeline."""
    setup_logging(log_level)
    load_dotenv()

    if not resume_run_id and (not location or not culture):
        console.print("[red]Error: --location and --culture are required for new runs[/red]")
        sys.exit(1)

    if provider == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            console.print("[red]Error: ANTHROPIC_API_KEY not set in environment or .env[/red]")
            sys.exit(1)
    else:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            console.print("[red]Error: GOOGLE_API_KEY not set in environment or .env[/red]")
            sys.exit(1)

    pipeline = StoryPipeline(config_dir=config_dir, api_key=api_key, fast=fast, provider=provider)
    callback = None if no_review else review_outline

    run_id = pipeline.run(
        location=location,
        culture_context=culture,
        target_grade=grade,
        review_callback=callback,
        resume_run_id=resume_run_id,
    )

    console.print(f"\n[bold green]Done![/bold green] Run ID: {run_id}")
    console.print(f"Output: output/{run_id}/final/story_final.json")


if __name__ == "__main__":
    cli()
