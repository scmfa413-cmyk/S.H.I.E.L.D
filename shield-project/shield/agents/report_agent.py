"""
Report Agent for S.H.I.E.L.D.

Generates structured intelligence reports from research findings.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json

from shield.agents.base import Agent
from shield.core.logger import get_logger
from shield.tools.base import get_tool_registry
from shield.memory import get_memory, get_vector_store

logger = get_logger(__name__)


class ReportAgent(Agent):
    """
    Intelligence report generation agent.
    
    Capabilities:
    - Structure findings into reports
    - Format for different outputs (markdown, JSON, etc.)
    - Cite sources properly
    - Generate executive summaries
    - Create visual hierarchies
    """
    
    def __init__(self):
        super().__init__(
            name="ReportAgent",
            role="Report Generator",
            description="Generates structured intelligence reports",
        )
        self.registry = get_tool_registry()
        self.memory = get_memory()
        self.vector_store = get_vector_store()
    
    async def generate_report(
        self,
        topic: str,
        findings: Dict[str, Any],
        sources: List[Dict[str, Any]],
        project_id: Optional[str] = None,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Generate intelligence report.
        
        Args:
            topic: Report topic
            findings: Research findings
            sources: Source information
            project_id: Project to save to
            format: Output format (markdown, json)
        
        Returns:
            Report data with file path
        """
        logger.info(f"Generating report: {topic}")
        
        # Generate report content
        if format == "markdown":
            content = self._generate_markdown_report(topic, findings, sources)
        else:
            content = self._generate_json_report(topic, findings, sources)
        
        # Save to file
        file_path = await self._save_report(
            topic,
            content,
            project_id,
            format
        )
        
        return {
            "topic": topic,
            "format": format,
            "file_path": str(file_path),
            "size_bytes": file_path.stat().st_size,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def _generate_markdown_report(
        self,
        topic: str,
        findings: Dict[str, Any],
        sources: List[Dict[str, Any]],
    ) -> str:
        """Generate markdown-formatted report"""
        
        report = []
        
        # Title
        report.append(f"# Intelligence Report: {topic}")
        report.append("")
        
        # Metadata
        report.append("## Report Metadata")
        report.append(f"- **Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        report.append(f"- **Topic:** {topic}")
        report.append(f"- **Sources Analyzed:** {findings.get('sources_analyzed', 0)}")
        report.append(f"- **Content Fetched:** {findings.get('content_fetched', 0)}")
        report.append("")
        
        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        report.append(f"This report contains findings on **{topic}** gathered from "
                     f"{findings.get('sources_analyzed', 0)} sources. "
                     f"The research identified key themes and patterns that are detailed below.")
        report.append("")
        
        # Key Themes
        report.append("## Key Themes Identified")
        report.append("")
        themes = findings.get("top_themes", [])
        if themes:
            for i, theme in enumerate(themes, 1):
                report.append(f"{i}. **{theme.title()}**")
        else:
            report.append("- No themes identified")
        report.append("")
        
        # Sources
        report.append("## Sources")
        report.append("")
        report.append("| Title | URL | Source |")
        report.append("|-------|-----|--------|")
        
        for source in sources[:20]:  # Max 20 sources in table
            title = source.get("title", "")[:50]  # Truncate title
            url = source.get("url", "")
            source_type = source.get("source", "web")
            report.append(f"| {title} | [{url[:40]}...](url) | {source_type} |")
        
        if len(sources) > 20:
            report.append(f"| ... and {len(sources) - 20} more sources ... |")
        
        report.append("")
        
        # Methodology
        report.append("## Research Methodology")
        report.append("")
        report.append("This report was generated using S.H.I.E.L.D. Intelligence Platform")
        report.append("through the following process:")
        report.append("")
        report.append("1. **Source Discovery** - Web search using multiple engines")
        report.append("2. **Content Analysis** - Fetching and analyzing page content")
        report.append("3. **Pattern Identification** - Finding common themes")
        report.append("4. **Insight Generation** - Synthesizing findings")
        report.append("5. **Report Generation** - Structuring results")
        report.append("")
        
        # Conclusions
        report.append("## Conclusions")
        report.append("")
        report.append(f"Based on analysis of {findings.get('sources_analyzed', 0)} sources:")
        report.append("")
        report.append("- Multiple perspectives on the topic were identified")
        report.append("- Key themes show consistent patterns across sources")
        report.append("- Further research recommended in specific areas")
        report.append("")
        
        # Footer
        report.append("---")
        report.append("")
        report.append("**Report Generated by:** S.H.I.E.L.D. Intelligence Platform")
        report.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        report.append("**Classification:** Unclassified")
        
        return "\n".join(report)
    
    def _generate_json_report(
        self,
        topic: str,
        findings: Dict[str, Any],
        sources: List[Dict[str, Any]],
    ) -> str:
        """Generate JSON-formatted report"""
        
        report = {
            "metadata": {
                "topic": topic,
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0",
            },
            "summary": {
                "sources_analyzed": findings.get("sources_analyzed", 0),
                "content_fetched": findings.get("content_fetched", 0),
                "total_size_kb": findings.get("total_size_kb", 0),
            },
            "findings": {
                "themes": findings.get("top_themes", []),
                "unique_sources": findings.get("unique_sources", 0),
            },
            "sources": sources[:20],
            "methodology": [
                "Source Discovery",
                "Content Analysis",
                "Pattern Identification",
                "Insight Generation",
                "Report Generation",
            ],
        }
        
        return json.dumps(report, indent=2)
    
    async def _save_report(
        self,
        topic: str,
        content: str,
        project_id: Optional[str],
        format: str,
    ) -> Path:
        """Save report to file"""
        
        # Determine file path
        if project_id:
            # Save to project
            from shield.core.config import Config
            config = Config.get()
            project_dir = Path(config.core.data_dir) / "projects" / topic.lower().replace(" ", "_")
        else:
            # Save to default reports directory
            from shield.core.config import Config
            config = Config.get()
            project_dir = Path(config.core.data_dir) / "reports"
        
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create report directory
        report_dir = project_dir / "reports"
        report_dir.mkdir(exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        extension = "md" if format == "markdown" else "json"
        filename = f"report_{timestamp}.{extension}"
        
        file_path = report_dir / filename
        
        # Write file
        write_tool = self.registry.get_tool("write_file")
        if write_tool:
            result = await write_tool.execute(
                file_path=str(file_path),
                content=content
            )
            if result.status.value == "success":
                logger.info(f"Report saved: {file_path}")
        else:
            # Fallback
            file_path.write_text(content, encoding="utf-8")
            logger.info(f"Report saved: {file_path}")
        
        return file_path


# Convenience factory
_report_agent_instance: Optional[ReportAgent] = None


def get_report_agent() -> ReportAgent:
    """Get or create report agent"""
    global _report_agent_instance
    if _report_agent_instance is None:
        _report_agent_instance = ReportAgent()
    return _report_agent_instance
