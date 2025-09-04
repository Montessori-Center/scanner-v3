# src/api/main.py
"""
FastAPI Backend for Scanner v3
Modern API for project analysis system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime
import json

app = FastAPI(
    title="Scanner v3 API",
    description="Modern project analyzer for LLM context",
    version="3.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# DATA MODELS
# ============================================================================

class ScanRequest(BaseModel):
    """Request model for starting a scan"""
    path: str
    analyzers: Optional[List[str]] = None
    profile: str = "balanced"  # fast, balanced, deep
    output_format: str = "json"  # json, markdown, context

class ScanStatus(BaseModel):
    """Status model for scan progress"""
    scan_id: str
    status: str  # pending, scanning, analyzing, completed, failed
    progress: int  # 0-100
    current_analyzer: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AnalyzerInfo(BaseModel):
    """Information about an analyzer"""
    name: str
    description: str
    enabled: bool = True
    execution_time: Optional[float] = None

# ============================================================================
# STORAGE (Replace with Redis in production)
# ============================================================================

scans_storage: Dict[str, ScanStatus] = {}
websocket_connections: Dict[str, WebSocket] = {}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with simple UI"""
    return """
    <html>
        <head>
            <title>Scanner v3 API</title>
            <style>
                body { font-family: Arial; padding: 50px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
                h1 { color: #667eea; }
                .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { font-weight: bold; color: #28a745; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 Scanner v3 API</h1>
                <p>Modern project analyzer for LLM context - Part of EternalMax Project</p>
                
                <h3>Available Endpoints:</h3>
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/health</code> - Health check
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/analyzers</code> - List all analyzers
                </div>
                <div class="endpoint">
                    <span class="method">POST</span> <code>/api/scan</code> - Start new scan
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/scan/{scan_id}</code> - Get scan status
                </div>
                <div class="endpoint">
                    <span class="method">GET</span> <code>/api/scans</code> - List all scans
                </div>
                <div class="endpoint">
                    <span class="method">WS</span> <code>/ws/{scan_id}</code> - WebSocket for real-time updates
                </div>
                
                <h3>Documentation:</h3>
                <p>
                    <a href="/docs">📖 Interactive API Documentation (Swagger UI)</a><br>
                    <a href="/redoc">📚 Alternative Documentation (ReDoc)</a>
                </p>
            </div>
        </body>
    </html>
    """

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/analyzers", response_model=List[AnalyzerInfo])
async def list_analyzers():
    """Get list of all available analyzers"""
    from src.core.container import Container
    
    container = Container()
    analyzers = []
    
    for name, analyzer_class in container.list_analyzers().items():
        analyzers.append(AnalyzerInfo(
            name=name,
            description=analyzer_class.description if hasattr(analyzer_class, 'description') else f"{name} analyzer",
            enabled=True
        ))
    
    return analyzers

@app.post("/api/scan", response_model=ScanStatus)
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Start a new scan"""
    # Validate path
    project_path = Path(request.path)
    if not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
    
    if not project_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {request.path}")
    
    # Create scan task
    scan_id = str(uuid.uuid4())
    scan_task = ScanStatus(
        scan_id=scan_id,
        status="pending",
        progress=0,
        started_at=datetime.now()
    )
    
    scans_storage[scan_id] = scan_task
    
    # Start background scan
    background_tasks.add_task(run_scan_task, scan_id, request)
    
    return scan_task

@app.get("/api/scan/{scan_id}", response_model=ScanStatus)
async def get_scan_status(scan_id: str):
    """Get status of a specific scan"""
    if scan_id not in scans_storage:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    return scans_storage[scan_id]

@app.get("/api/scans", response_model=List[ScanStatus])
async def list_scans(limit: int = 20):
    """List all scans (most recent first)"""
    scans = list(scans_storage.values())
    scans.sort(key=lambda x: x.started_at, reverse=True)
    return scans[:limit]

@app.delete("/api/scan/{scan_id}")
async def cancel_scan(scan_id: str):
    """Cancel a running scan"""
    if scan_id not in scans_storage:
        raise HTTPException(status_code=404, detail=f"Scan not found: {scan_id}")
    
    scan = scans_storage[scan_id]
    if scan.status in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed scan")
    
    scan.status = "cancelled"
    scan.completed_at = datetime.now()
    
    return {"message": "Scan cancelled"}

# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/{scan_id}")
async def websocket_endpoint(websocket: WebSocket, scan_id: str):
    """WebSocket connection for real-time scan updates"""
    await websocket.accept()
    websocket_connections[scan_id] = websocket
    
    try:
        while True:
            # Send updates
            if scan_id in scans_storage:
                scan = scans_storage[scan_id]
                await websocket.send_json({
                    "type": "status",
                    "data": {
                        "status": scan.status,
                        "progress": scan.progress,
                        "current_analyzer": scan.current_analyzer
                    }
                })
                
                if scan.status in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if scan_id in websocket_connections:
            del websocket_connections[scan_id]

# ============================================================================
# BACKGROUND SCAN TASK
# ============================================================================

async def run_scan_task(scan_id: str, request: ScanRequest):
    """Background task to run scan and analysis"""
    from src.core.scanner import Scanner
    from src.core.container import Container
    from src.core.config import Settings
    
    scan_task = scans_storage[scan_id]
    
    try:
        # Update status
        scan_task.status = "scanning"
        scan_task.progress = 5
        await notify_websocket(scan_id, "Scanning project files...")
        
        # Initialize scanner
        settings = Settings(profile=request.profile)
        scanner = Scanner(settings)
        
        # Run scan
        scan_result = await scanner.scan(Path(request.path))
        
        scan_task.progress = 30
        await notify_websocket(scan_id, f"Found {scan_result.total_files} files")
        
        # Run analyzers
        scan_task.status = "analyzing"
        container = Container()
        
        # Get requested analyzers or use all
        if request.analyzers:
            analyzer_names = request.analyzers
        else:
            analyzer_names = list(container.list_analyzers().keys())
        
        results = {}
        for i, analyzer_name in enumerate(analyzer_names):
            scan_task.current_analyzer = analyzer_name
            
            # Get and run analyzer
            analyzer = container.get_analyzer(analyzer_name)
            if analyzer:
                try:
                    await notify_websocket(scan_id, f"Running {analyzer_name} analyzer...")
                    
                    start_time = datetime.now()
                    analysis_result = await analyzer.analyze(scan_result)
                    execution_time = (datetime.now() - start_time).total_seconds()
                    
                    results[analyzer_name] = {
                        "data": analysis_result.data,
                        "execution_time": execution_time
                    }
                except Exception as e:
                    results[analyzer_name] = {
                        "error": str(e),
                        "execution_time": 0
                    }
            
            # Update progress
            progress = 30 + int(70 * (i + 1) / len(analyzer_names))
            scan_task.progress = progress
        
        # Generate summary
        summary = generate_summary(results)
        
        # Complete scan
        scan_task.status = "completed"
        scan_task.progress = 100
        scan_task.completed_at = datetime.now()
        scan_task.duration = (scan_task.completed_at - scan_task.started_at).total_seconds()
        scan_task.results = {
            "scan": {
                "total_files": scan_result.total_files,
                "total_size": scan_result.total_size,
                "scan_duration": scan_result.duration
            },
            "analysis": results,
            "summary": summary
        }
        
        await notify_websocket(scan_id, "Scan completed successfully!")
        
    except Exception as e:
        scan_task.status = "failed"
        scan_task.error = str(e)
        scan_task.completed_at = datetime.now()
        await notify_websocket(scan_id, f"Scan failed: {e}")

async def notify_websocket(scan_id: str, message: str):
    """Send notification to WebSocket if connected"""
    if scan_id in websocket_connections:
        ws = websocket_connections[scan_id]
        try:
            await ws.send_json({"type": "message", "data": message})
        except:
            pass

def generate_summary(results: Dict) -> Dict:
    """Generate summary for LLM context"""
    summary = {
        "total_analyzers_run": len(results),
        "successful_analyzers": sum(1 for r in results.values() if "error" not in r),
        "failed_analyzers": sum(1 for r in results.values() if "error" in r),
        "key_findings": {}
    }
    
    # Extract key findings from each analyzer
    if "security" in results and "data" in results["security"]:
        data = results["security"]["data"]
        summary["key_findings"]["security_issues"] = data.get("total_issues", 0)
        summary["key_findings"]["critical_security"] = data.get("critical_count", 0)
    
    if "api" in results and "data" in results["api"]:
        data = results["api"]["data"]
        summary["key_findings"]["api_endpoints"] = data.get("total", 0)
    
    if "dependencies" in results and "data" in results["dependencies"]:
        data = results["dependencies"]["data"]
        summary["key_findings"]["total_dependencies"] = data.get("total", 0)
    
    if "todos" in results and "data" in results["todos"]:
        data = results["todos"]["data"]
        summary["key_findings"]["todos"] = data.get("total", 0)
    
    if "errors" in results and "data" in results["errors"]:
        data = results["errors"]["data"]
        summary["key_findings"]["total_errors"] = data.get("total_errors", 0)
    
    return summary

# ============================================================================
# STARTUP AND SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    print("Scanner v3 API starting...")
    print("Dashboard: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Scanner v3 API shutting down...")
    # Close all WebSocket connections
    for ws in websocket_connections.values():
        await ws.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
