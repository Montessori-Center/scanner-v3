#!/usr/bin/env python3
"""Command-line interface for Scanner v3 with parallel execution"""
import asyncio
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from src.core.config import Settings
from src.core.container import Container
from src.core.validators import InputValidator
from src.output.context import LLMContextBuilder
from src.output.json import JSONFormatter
from src.output.markdown import MarkdownFormatter

app = typer.Typer(
    name="scanner",
    help="🔍 Scanner v3 - Modern project analyzer for LLM context",
    add_completion=False,
)

console = Console()


async def run_analyzer_async(analyzer, scan_result, name):
    """Run single analyzer asynchronously"""
    try:
        start = time.time()
        result = await analyzer.analyze(scan_result)
        duration = time.time() - start
        return name, result.data, duration, None
    except Exception as e:
        return name, {"error": str(e)}, 0, str(e)


async def run_analyzers_parallel(container, analyzer_names, scan_result):
    """Run multiple analyzers in parallel"""
    tasks = []
    for name in analyzer_names:
        analyzer = container.get_analyzer(name)
        if analyzer:
            tasks.append(run_analyzer_async(analyzer, scan_result, name))

    results = await asyncio.gather(*tasks)
    return results


@app.command()
def scan(
    path: Path = typer.Argument(Path.cwd(), help="Project path to scan"),
    profile: str = typer.Option("balanced", "--profile", "-p", help="Performance profile: fast/balanced/deep"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table/json/markdown/context"),
    analyzers: Optional[str] = typer.Option(None, "--analyzers", "-a", help="Comma-separated list of analyzers to run"),
    parallel: bool = typer.Option(True, "--parallel/--sequential", help="Run analyzers in parallel or sequential"),
):
    """Scan project and run analyzers"""

    # Validate input path
    if not InputValidator.validate_path(path):
        console.print(f"[red]❌ Invalid or unsafe path: {path}[/red]")
        return

    console.print(f"[cyan]🔍 Scanning project: {path}[/cyan]")

    # Create container with settings
    settings = Settings(profile=profile)
    container = Container(settings)

    # Run scan asynchronously
    async def scan_async():
        scanner = container.scanner
        return await scanner.scan(path)

    scan_start = time.time()
    scan_result = asyncio.run(scan_async())
    scan_time = time.time() - scan_start

    console.print(f"[green]✓ Found {scan_result.total_files} files ({scan_result.total_size:,} bytes)[/green]")
    console.print(f"[green]✓ Scan took {scan_time:.2f} seconds[/green]")

    # Get analyzers to run
    if analyzers:
        analyzer_names = [a.strip() for a in analyzers.split(",")]
    else:
        analyzer_names = container.get_analyzer_names()

    mode = "parallel" if parallel else "sequential"
    console.print(f"\n[cyan]📊 Running {len(analyzer_names)} analyzers ({mode})...[/cyan]")

    # Prepare results structure
    results = {
        "scan_info": {
            "path": str(path),
            "total_files": scan_result.total_files,
            "total_size": scan_result.total_size,
            "duration": scan_result.duration
        },
        "analyzers": {}
    }

    # Run analyzers
    analysis_start = time.time()

    if parallel:
        # Parallel execution
        async def run_all():
            return await run_analyzers_parallel(container, analyzer_names, scan_result)

        analyzer_results = asyncio.run(run_all())

        # Process results
        for name, data, duration, error in analyzer_results:
            results["analyzers"][name] = data
            if not error:
                console.print(f"[green]✓[/green] {name:15} [{duration:5.2f}s]")
            else:
                console.print(f"[red]✗[/red] {name:15} Error: {error}")
    else:
        # Sequential execution (original)
        with Progress() as progress:
            task = progress.add_task("[cyan]Analyzing...", total=len(analyzer_names))

            for analyzer_name in analyzer_names:
                analyzer = container.get_analyzer(analyzer_name)
                if analyzer:
                    try:
                        start = time.time()
                        result = asyncio.run(analyzer.analyze(scan_result))
                        duration = time.time() - start
                        results["analyzers"][analyzer_name] = result.data
                        console.print(f"[green]✓[/green] {analyzer_name:15} [{duration:5.2f}s]")
                        progress.advance(task)
                    except Exception as e:
                        console.print(f"[red]✗ {analyzer_name} failed: {e}[/red]")
                        results["analyzers"][analyzer_name] = {"error": str(e)}

    analysis_time = time.time() - analysis_start
    total_time = time.time() - scan_start

    console.print("\n[cyan]⏱️ Performance:[/cyan]")
    console.print(f"  • Scanning: {scan_time:.2f}s")
    console.print(f"  • Analysis: {analysis_time:.2f}s")
    console.print(f"  • Total: {total_time:.2f}s")

    if parallel and len(analyzer_names) > 1:
        speedup = (len(analyzer_names) * analysis_time / len(analyzer_names)) / analysis_time
        console.print(f"  • Speedup: {speedup:.1f}x (parallel)")

    # Format output based on format option
    if format == "table":
        _show_summary_table(results["analyzers"])
    elif format == "json":
        formatter = JSONFormatter()
        formatted_output = formatter.format(results)
        if output:
            output.write_text(formatted_output)
            console.print(f"[green]✓ JSON results saved to {output}[/green]")
        else:
            console.print(formatted_output)
    elif format == "markdown":
        formatter = MarkdownFormatter()
        formatted_output = formatter.format(results)
        if output:
            output.write_text(formatted_output)
            console.print(f"[green]✓ Markdown report saved to {output}[/green]")
        else:
            console.print(formatted_output)
    elif format == "context":
        builder = LLMContextBuilder()
        llm_context = builder.format(results)
        if output:
            output.write_text(llm_context)
            console.print(f"[green]✓ LLM context saved to {output}[/green]")
        else:
            console.print(llm_context)
    else:
        console.print(f"[red]Unknown format: {format}[/red]")


def _show_summary_table(results: dict):
    """Show summary table of analysis results"""
    table = Table(title="Analysis Summary")
    table.add_column("Analyzer", style="cyan")
    table.add_column("Key Findings", style="white")

    for name, data in results.items():
        if "error" not in data:
            # Extract key info based on analyzer type
            if name == "manifest":
                finding = f"Type: {data.get('project_type', 'unknown')}, Files: {data.get('total_files', 0)}"
            elif name == "dependencies":
                finding = f"Total: {data.get('total', 0)}, Primary: {data.get('primary_language', 'unknown')}"
            elif name == "env":
                finding = f"Variables: {data.get('count', 0)}, Sources: {len(data.get('sources', []))}"
            elif name == "todos":
                finding = f"Total: {data.get('total', 0)}, High priority: {data.get('by_priority', {}).get('high', 0)}"
            elif name == "security":
                finding = f"Issues: {data.get('total', 0)}, Critical: {len(data.get('vulnerabilities', {}).get('critical', []))}"
            elif name == "api":
                finding = f"Endpoints: {data.get('total', 0)}, Frameworks: {', '.join(data.get('frameworks', []))}"
            else:
                finding = "Analyzed successfully"

            table.add_row(name, finding)
        else:
            table.add_row(name, f"[red]Error: {data['error']}[/red]")

    console.print(table)


@app.command()
def list():
    """List available analyzers"""
    container = Container()
    analyzers = container.get_analyzer_names()

    table = Table(title="Available Analyzers")
    table.add_column("Name", style="cyan")
    table.add_column("Module", style="white")

    for name in sorted(analyzers):
        analyzer = container.get_analyzer(name)
        if analyzer:
            table.add_row(name, analyzer.description)

    console.print(table)
    console.print(f"\n[green]Total: {len(analyzers)} analyzers[/green]")


@app.command()
def version():
    """Show version"""
    console.print("[cyan]Scanner v3.0.0[/cyan]")
    console.print("Part of Eternal Max Project")


if __name__ == "__main__":
    app()
