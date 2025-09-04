"""Command-line interface for Scanner v3"""
import typer
import asyncio
import json
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

from src.core.container import Container
from src.core.config import Settings

app = typer.Typer(
    name="scanner",
    help="🔍 Scanner v3 - Modern project analyzer for LLM context",
    add_completion=False,
)

console = Console()


@app.command()
def scan(
    path: Path = typer.Argument(Path.cwd(), help="Project path to scan"),
    profile: str = typer.Option("balanced", "--profile", "-p", help="Performance profile: fast/balanced/deep"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Scan project and run all analyzers"""
    
    console.print(f"[cyan]🔍 Scanning project: {path}[/cyan]")
    
    # Create container with settings
    settings = Settings(profile=profile)
    container = Container(settings)
    
    # Run scan
    scan_result = asyncio.run(container.scanner.scan(path))
    
    console.print(f"[green]✓ Found {scan_result.total_files} files ({scan_result.total_size:,} bytes)[/green]")
    console.print(f"[green]✓ Scan took {scan_result.duration:.2f} seconds[/green]")
    
    # Get available analyzers
    analyzers = container.get_analyzer_names()
    console.print(f"\n[cyan]📊 Running {len(analyzers)} analyzers...[/cyan]")
    
    results = {}
    
    # Run analyzers with progress bar
    with Progress() as progress:
        task = progress.add_task("[cyan]Analyzing...", total=len(analyzers))
        
        for analyzer_name in analyzers:
            analyzer = container.get_analyzer(analyzer_name)
            if analyzer:
                try:
                    result = asyncio.run(analyzer.analyze(scan_result))
                    results[analyzer_name] = result.data
                    progress.advance(task)
                except Exception as e:
                    console.print(f"[red]✗ {analyzer_name} failed: {e}[/red]")
                    results[analyzer_name] = {"error": str(e)}
    
    # Show summary table
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
                finding = f"Analyzed successfully"
                
            table.add_row(name, finding)
        else:
            table.add_row(name, f"[red]Error[/red]")
    
    console.print(table)
    
    # Save output if requested
    if output:
        output_data = {
            "version": "3.0.0",
            "project": str(path),
            "profile": profile,
            "scan": {
                "total_files": scan_result.total_files,
                "total_size": scan_result.total_size,
                "duration": scan_result.duration
            },
            "results": results
        }
        
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        console.print(f"\n[green]✓ Results saved to {output}[/green]")


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
