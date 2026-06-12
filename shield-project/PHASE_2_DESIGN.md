# S.H.I.E.L.D. Phase 2: Memory & Operational Tools Design

## Overview

Phase 2 transforms S.H.I.E.L.D. from a framework into an **operational intelligence platform** capable of performing real, meaningful tasks. Focus shifts from infrastructure to practical capabilities: persistent memory, file management, web intelligence, and code generation.

## Architecture: Memory & Operational Stack

```
┌─────────────────────────────────────────────────────┐
│              CLI / User Interface                    │
├─────────────────────────────────────────────────────┤
│           OPERATIONAL TASKS LAYER                    │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │Research Task │  │Code Gen Task │  │Report Task ││
│  └──────────────┘  └──────────────┘  └────────────┘│
├─────────────────────────────────────────────────────┤
│            TOOLS & SERVICES LAYER                    │
│  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │File Tools       │  │Web Search Tools         │  │
│  │Directory Tools  │  │Research Pipeline        │  │
│  │Project Tools    │  │Code Generation Tools    │  │
│  └─────────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│             MEMORY MANAGEMENT LAYER                  │
│  ┌──────────────────┐  ┌────────────────────────┐  │
│  │Memory Manager    │  │Conversation Memory     │  │
│  ├──────────────────┤  ├────────────────────────┤  │
│  │Project Memory    │  │Semantic Search         │  │
│  ├──────────────────┤  ├────────────────────────┤  │
│  │Knowledge Store   │  │Context Retrieval       │  │
│  └──────────────────┘  └────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│           DATABASE & STORAGE LAYER                   │
│  ┌──────────────────┐  ┌────────────────────────┐  │
│  │SQLite Database   │  │ChromaDB Vector Store   │  │
│  │ • Conversations  │  │ • Embeddings           │  │
│  │ • Projects       │  │ • Semantic Search      │  │
│  │ • Metadata       │  │ • Knowledge Graph      │  │
│  └──────────────────┘  └────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐ │
│  │File System Storage                              │ │
│  │ • Artifacts (code, reports, etc.)               │ │
│  │ • Project directories                           │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 1. Memory Layer Architecture

### 1.1 SQLite Database Schema

**Core Tables:**

```sql
-- Users & Sessions
users:
  - user_id (PK)
  - username
  - created_at
  - preferences (JSON)

sessions:
  - session_id (PK)
  - user_id (FK)
  - started_at
  - ended_at
  - context (JSON)

-- Conversations & Messages
conversations:
  - conversation_id (PK)
  - user_id (FK)
  - project_id (FK, nullable)
  - title
  - description
  - created_at
  - updated_at
  - tags (JSON)

messages:
  - message_id (PK)
  - conversation_id (FK)
  - role (user/assistant/system/agent)
  - content
  - message_type (text/code/file/report)
  - metadata (JSON)
  - created_at
  - tokens_used
  - tool_calls (JSON)

-- Projects & Artifacts
projects:
  - project_id (PK)
  - user_id (FK)
  - name
  - description
  - root_path
  - type (research/code/analysis)
  - status (active/archived)
  - created_at
  - updated_at
  - metadata (JSON)

artifacts:
  - artifact_id (PK)
  - project_id (FK)
  - name
  - type (code/document/report/data)
  - file_path
  - content_hash
  - created_at
  - size_bytes
  - metadata (JSON)

-- Research & Sources
research_topics:
  - topic_id (PK)
  - conversation_id (FK)
  - title
  - query
  - created_at
  - findings_summary (JSON)

sources:
  - source_id (PK)
  - topic_id (FK)
  - url
  - title
  - content_hash
  - snippet
  - source_type (web/document/internal)
  - relevance_score
  - fetched_at

-- Memory & Embeddings
embeddings:
  - embedding_id (PK)
  - message_id (FK, nullable)
  - artifact_id (FK, nullable)
  - text_chunk
  - vector_id (ChromaDB ref)
  - created_at

-- Tool Execution Log
tool_executions:
  - execution_id (PK)
  - tool_name
  - parameters (JSON)
  - result (JSON)
  - status (success/failed/error)
  - duration_ms
  - created_at
```

### 1.2 Memory Manager Service

```python
class MemoryManager:
    """
    Central memory management service.
    
    Handles:
    - Conversation persistence
    - Project memory
    - Semantic search
    - Context retrieval
    - Memory cleanup
    """
    
    # Methods:
    - save_conversation()
    - load_conversation()
    - save_project_memory()
    - retrieve_project_context()
    - search_memories()
    - add_embedding()
    - cleanup_old_memories()
    - export_memory()
    - import_memory()
```

### 1.3 ChromaDB Integration

```python
class VectorStore:
    """
    Semantic memory using ChromaDB.
    
    Stores embeddings of:
    - Conversation messages
    - Research findings
    - Code snippets
    - Documentation
    - Project context
    """
    
    # Methods:
    - add_message()
    - add_artifact()
    - search_similar()
    - get_project_context()
    - semantic_search()
    - delete_collection()
```

---

## 2. Operational Tools

### 2.1 File Tools (`shield/tools/file_tools.py`)

**Tools:**
- `read_file` - Read text files (txt, py, json, yaml, md)
- `read_pdf` - Extract text from PDF
- `read_docx` - Extract text from Word documents
- `read_csv` - Parse and analyze CSV
- `write_file` - Create/update files
- `analyze_code` - Parse and analyze Python code
- `get_file_info` - Get file metadata

### 2.2 Directory Tools (`shield/tools/directory_tools.py`)

**Tools:**
- `list_directory` - List files/folders
- `create_directory` - Create directories
- `delete_directory` - Remove directories
- `copy_file` - Copy files
- `move_file` - Move files
- `delete_file` - Delete files
- `search_files` - Find files by pattern

### 2.3 Project Tools (`shield/tools/project_tools.py`)

**Tools:**
- `create_project` - Initialize new project
- `create_project_structure` - Scaffold project directories
- `generate_readme` - Create README
- `add_to_project` - Add files to project
- `get_project_structure` - List project hierarchy
- `save_project_state` - Persist project state

### 2.4 Web Search Tools (`shield/tools/web_search_tools.py`)

**Tools:**
- `search_duckduckgo` - Search DuckDuckGo
- `search_tavily` - Search Tavily API
- `fetch_page_content` - Get full page content
- `summarize_content` - Summarize page content

### 2.5 Code Generation Tools (`shield/tools/code_tools.py`)

**Tools:**
- `generate_code` - Generate code from description
- `create_python_project` - Create Python project structure
- `generate_requirements` - Create requirements.txt
- `validate_code` - Check code syntax
- `format_code` - Format Python code (black)

---

## 3. Research Pipeline

### 3.1 Research Workflow

```
Query
  ↓
[Research Agent]
  ├─ search_duckduckgo()
  ├─ search_tavily()
  ├─ fetch_page_content() [top 5 results]
  ├─ store_findings_in_memory()
  ├─ analyze_findings()
  └─ generate_summary()
  ↓
[Report Generation]
  ├─ organize_findings()
  ├─ detect_contradictions()
  ├─ identify_trends()
  ├─ cite_sources()
  └─ create_structured_report()
  ↓
[Persist to Memory]
  ├─ save_conversation()
  ├─ store_sources()
  ├─ create_embeddings()
  └─ tag_project()
```

### 3.2 Research Agent

```python
class ResearchAgent(Agent):
    """
    Autonomous research agent.
    
    Capabilities:
    - Web search
    - Content fetching
    - Finding analysis
    - Contradiction detection
    - Trend identification
    - Report generation
    """
    
    async def execute_research_task(query: str):
        1. Search multiple sources
        2. Fetch and analyze content
        3. Detect patterns/contradictions
        4. Generate summary
        5. Store in memory
        6. Create report
```

---

## 4. First Real Demo: Complete Workflow

### Objective
```
"S.H.I.E.L.D., research the latest developments in AI safety in 2025, 
analyze the top findings, identify contradictions, and generate a 
structured intelligence report."
```

### Execution Flow

```
1. PARSE MISSION
   ├─ Identify task type: Research + Analysis
   ├─ Extract parameters: topic=AI safety, year=2025
   └─ Create project: "AI_Safety_Research_2025"

2. RESEARCH PHASE (ResearchAgent)
   ├─ Execute searches:
   │  ├─ DuckDuckGo: "AI safety 2025 developments"
   │  ├─ Tavily: "AI safety trends 2025"
   │  └─ Get top 10 results
   ├─ Fetch content from top 5 sources
   ├─ Extract key findings
   └─ Store in project memory

3. ANALYSIS PHASE (AnalysisAgent)
   ├─ Analyze findings:
   │  ├─ Identify common themes
   │  ├─ Detect contradictions
   │  ├─ Assess credibility of sources
   │  └─ Extract insights
   ├─ Generate summary statistics
   └─ Organize findings hierarchically

4. REPORT GENERATION
   ├─ Structure findings:
   │  ├─ Executive Summary
   │  ├─ Key Findings
   │  ├─ Source Analysis
   │  ├─ Contradictions & Consensus
   │  ├─ Trends & Patterns
   │  └─ Conclusions
   ├─ Generate markdown report
   └─ Create code artifacts if needed

5. PERSISTENCE
   ├─ Save conversation to database
   ├─ Store all sources with URLs
   ├─ Create embeddings of findings
   ├─ Tag project with metadata
   ├─ Create artifacts directory
   └─ Export report to file

6. OUTPUT TO USER
   ├─ Display summary
   ├─ Show top sources
   ├─ Display contradictions found
   ├─ List files created
   └─ Provide project path
```

### Expected Output

```
═══════════════════════════════════════════════════════════
  RESEARCH COMPLETE: AI Safety 2025
═══════════════════════════════════════════════════════════

📊 FINDINGS SUMMARY
├─ Sources analyzed: 15
├─ Key findings: 7
├─ Contradictions found: 2
└─ Consensus themes: 5

🔑 TOP FINDINGS
1. Alignment research accelerating (12 sources)
2. AI risk frameworks evolving (10 sources)
3. Governance challenges remain (9 sources)
... (more findings)

⚠️ CONTRADICTIONS DETECTED
- Source A: "More regulation needed"
- Source B: "Self-regulation sufficient"

📁 ARTIFACTS CREATED
✓ /projects/AI_Safety_Research_2025/
  ├─ report.md (structured intelligence report)
  ├─ sources.json (all sources and URLs)
  ├─ findings.json (structured findings)
  └─ metadata.yaml (project metadata)

💾 MEMORY SAVED
✓ Conversation saved to database
✓ Embeddings created for semantic search
✓ Project memory stored
✓ Sources indexed

Next: Run 'shield show project AI_Safety_Research_2025' 
to view details or continue research.
═══════════════════════════════════════════════════════════
```

### Future Session Access

```bash
# Next day - Continue research
$ shield memory show AI_Safety_Research_2025

# See previous research
$ shield research AI_Safety_Research_2025 --continue

# Search across all research
$ shield memory search "AI safety alignment"

# Generate new analysis from existing memory
$ shield analyze AI_Safety_Research_2025 --compare-trends
```

---

## 5. Implementation Strategy

### Phase 2a: Database Layer (Week 1)

**Files to create:**
- `shield/database/schema.py` - Database schema
- `shield/database/migrations.py` - Migration system
- `shield/database/connection.py` - Connection pooling
- `shield/database/models.py` - SQLAlchemy models

**Tasks:**
1. Design SQLite schema
2. Create database models
3. Implement migrations
4. Add connection pooling

### Phase 2b: Memory Manager (Week 1)

**Files to create:**
- `shield/memory/memory_manager.py` - Central memory service
- `shield/memory/vector_store.py` - ChromaDB integration
- `shield/memory/conversation_store.py` - Conversation persistence
- `shield/memory/project_store.py` - Project memory

**Tasks:**
1. Implement MemoryManager
2. Integrate ChromaDB
3. Add conversation storage
4. Add project storage

### Phase 2c: File & Directory Tools (Week 2)

**Files to create:**
- `shield/tools/file_tools.py` - File operations
- `shield/tools/directory_tools.py` - Directory operations
- `shield/tools/project_tools.py` - Project scaffolding

**Tasks:**
1. Implement file read/write tools
2. Implement directory tools
3. Implement project creation
4. Add file analysis tools

### Phase 2d: Web Search & Research (Week 2-3)

**Files to create:**
- `shield/tools/web_search_tools.py` - Search integration
- `shield/agents/research_agent.py` - Research agent
- `shield/agents/analysis_agent.py` - Analysis agent

**Tasks:**
1. Integrate DuckDuckGo
2. Add Tavily support
3. Implement ResearchAgent
4. Implement AnalysisAgent
5. Create research pipeline

### Phase 2e: Code Generation (Week 3)

**Files to create:**
- `shield/tools/code_tools.py` - Code generation
- `shield/agents/code_agent.py` - Code generation agent

**Tasks:**
1. Implement code generation
2. Create project scaffolding
3. Implement CodeAgent
4. Add validation tools

### Phase 2f: CLI Enhancement (Week 3)

**Updates to:**
- `shield/cli/main.py` - Add mission/research/project commands

**Tasks:**
1. Add `mission` command
2. Add `research` command
3. Add `project` command
4. Add `memory` command
5. Add `report` command

---

## 6. CLI Commands (Phase 2 End State)

```bash
# Research
shield mission "research topic"              # Execute full research mission
shield research "query"                      # Quick research
shield memory show [PROJECT]                 # Show project memory
shield memory search "query"                 # Search across all memories

# Projects
shield project create "name" [--type TYPE]   # Create new project
shield project list                          # List all projects
shield project analyze PATH                  # Analyze project
shield project structure [--type TYPE]       # Show project template

# Files
shield file read PATH                        # Read file with analysis
shield file create PATH [--content CONTENT]  # Create file
shield file analyze PATH                     # Analyze code/document

# Reports
shield report generate [--format FORMAT]     # Generate report
shield report analyze PATH                   # Analyze report

# Task execution
shield execute MISSION_DESCRIPTION          # Execute complex task
```

---

## 7. Success Metrics for Phase 2

✅ **Memory Persistence**
- Conversations survive across sessions
- Project context retrieved accurately
- Semantic search works (find similar findings)

✅ **Research Capability**
- Can search multiple sources
- Fetches and analyzes content
- Detects contradictions
- Generates structured reports

✅ **File Management**
- Can create projects with structure
- Generates files with content
- Organizes artifacts properly

✅ **Code Generation**
- Creates valid Python code
- Scaffolds project structures
- Follows best practices

✅ **First Real Demo**
- Research mission executes end-to-end
- Memory persists across sessions
- Reports are useful and structured
- Files created in organized manner

---

## 8. Data Model Examples

### Research Project Memory

```json
{
  "project_id": "ai_safety_2025",
  "title": "AI Safety 2025 Research",
  "type": "research",
  "created_at": "2026-06-12T10:00:00Z",
  "findings": [
    {
      "title": "Alignment Research Accelerating",
      "sources": [
        {"url": "...", "title": "...", "relevance": 0.95},
        {"url": "...", "title": "...", "relevance": 0.92}
      ],
      "summary": "Multiple sources indicate...",
      "keywords": ["alignment", "safety", "research"]
    }
  ],
  "metadata": {
    "total_sources": 15,
    "contradictions": 2,
    "consensus_themes": 5
  }
}
```

### Project Structure

```
/projects/AI_Safety_Research_2025/
├── memory.json              # Project memory
├── conversations/
│   ├── 2026-06-12.json     # Daily conversation
│   └── 2026-06-13.json
├── reports/
│   └── 2026-06-12_research_report.md
├── sources/
│   └── sources.json         # All collected sources
└── artifacts/
    ├── findings.json
    └── analysis.json
```

---

## Summary

Phase 2 transforms S.H.I.E.L.D. from framework to **operational intelligence platform** with:

✅ **Persistent Memory** - SQLite + ChromaDB for knowledge storage  
✅ **Research Capability** - Multi-source analysis and reporting  
✅ **File Management** - Create, organize, analyze files  
✅ **Code Generation** - Generate and scaffold projects  
✅ **Real Demonstrations** - Execute meaningful end-to-end tasks  

By end of Phase 2, S.H.I.E.L.D. will be **demonstrably useful** for conducting research, creating projects, and performing complex operational tasks.

---

*Last Updated: 2026-06-12*
