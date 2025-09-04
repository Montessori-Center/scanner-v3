"""Quick test of scanner and manifest analyzer"""
import asyncio
from pathlib import Path
from src.core.container import Container

async def main():
    # Create container
    container = Container()
    
    # Scan current project (scanner itself)
    print("🔍 Scanning current project...")
    scan_result = await container.scanner.scan(Path.cwd())
    
    print(f"✓ Found {scan_result.total_files} files")
    print(f"✓ Total size: {scan_result.total_size:,} bytes")
    print(f"✓ Scan took: {scan_result.duration:.2f} seconds")
    
    # Run manifest analyzer
    print("\n📊 Running manifest analyzer...")
    analyzer = container.get_analyzer("manifest")
    if analyzer:
        result = await analyzer.analyze(scan_result)
        
        print(f"✓ Project type: {result.data['project_type']}")
        print(f"✓ Languages: {result.data['languages']}")
        print(f"✓ Has tests: {result.data['has_tests']}")
        print(f"✓ Has git: {result.data['has_git']}")
    else:
        print("❌ Manifest analyzer not found")

if __name__ == "__main__":
    asyncio.run(main())
