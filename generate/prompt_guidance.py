"""Shared instructions derived from CLAUDE.md / AGENTS.md for LLM prompts.

Loads the actual contents of project documentation files and extracts
sections relevant for automated spider generation, so the LLM gets the
same rich context that interactive Claude sessions receive.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_file_safe(path: Path) -> str:
    """Read a file, returning empty string on failure."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        logger.debug("Could not read %s: %s", path, exc)
        return ""


def _build_system_instructions() -> str:
    """Build rich system instructions from project documentation.

    Loads CLAUDE.md plus supporting docs (extractors.md, callbacks.md)
    and extracts sections relevant to automated spider config generation.
    Sections that only apply to interactive CLI sessions (greetings,
    allowed tools, CLI reference) are excluded to save tokens.
    """
    claude_md = _read_file_safe(_PROJECT_ROOT / "CLAUDE.md")
    extractors_md = _read_file_safe(_PROJECT_ROOT / "docs" / "extractors.md")
    callbacks_md = _read_file_safe(_PROJECT_ROOT / "docs" / "callbacks.md")

    # If files are available, build rich context
    if claude_md:
        sections = _extract_relevant_sections(claude_md)
        parts = [
            "You are ScrapAI, an expert web scraping engineer that generates spider configurations.\n",
            "# ScrapAI Spider Generation Guide\n",
            "The following instructions are from the project's documentation. "
            "Follow them precisely when generating spider configs.\n",
        ]
        parts.append(sections)

        if extractors_md:
            parts.append("\n# Extractor Reference\n")
            parts.append(extractors_md)

        if callbacks_md:
            parts.append("\n# Callbacks & Custom Fields Reference\n")
            parts.append(callbacks_md)

        parts.append("\n")
        return "\n".join(parts)

    # Fallback: minimal instructions if files are missing
    return _FALLBACK_INSTRUCTIONS


def _extract_relevant_sections(claude_md: str) -> str:
    """Extract sections from CLAUDE.md relevant to spider generation.

    Includes:
    - What is ScrapAI / Big Picture / Phase overview
    - Spider Naming Convention
    - Phase 2: Rule Generation & Extraction Testing
    - Phase 3: Prepare Spider Configuration
    - Settings Quick Reference
    - Named Callbacks & Custom Fields

    Excludes (interactive-only):
    - On Greeting
    - Allowed Tools / Forbidden
    - Environment setup
    - CLI Reference (crawl/show/export/queue/db commands)
    - What Agent Can Modify
    """
    lines = claude_md.split("\n")
    result_lines: list[str] = []
    include = False
    skip_until_next_h2 = False

    # Sections to include (matched by heading text)
    include_headings = {
        "## What is ScrapAI?",
        "### The Big Picture",
        "### Your Workflow: Phase 1-4",
        "## Spider Naming Convention",
        "### Phase 2: Rule Generation & Extraction Testing",
        "### Phase 3: Prepare Spider Configuration",
        "## Settings Quick Reference",
        "## Named Callbacks & Custom Fields",
    }

    # Sections to skip (matched by heading text)
    skip_headings = {
        "### On Greeting",
        "## Allowed Tools",
        "## Environment",
        "## CLI Reference",
        "### Setup",
        "### Projects",
        "### Spiders",
        "### Crawling",
        "### Show",
        "### Health Check",
        "### Export",
        "### Queue",
        "### Database",
        "## What Agent Can Modify",
        "## ⚠️ CRITICAL RULES - READ FIRST",
        "### Phase 1: Analysis & Section Documentation",
        "### Phase 4: Execution & Verification",
    }

    for line in lines:
        stripped = line.strip()

        # Check if this line is a heading we want to include
        if any(stripped.startswith(h) for h in include_headings):
            include = True
            skip_until_next_h2 = False
            result_lines.append(line)
            continue

        # Check if this line is a heading we want to skip
        if any(stripped.startswith(h) for h in skip_headings):
            include = False
            skip_until_next_h2 = True
            continue

        # Check for any new top-level heading (##) that isn't in our lists
        if stripped.startswith("## ") and skip_until_next_h2:
            # Unknown section - skip it too
            continue

        if include:
            result_lines.append(line)

    return "\n".join(result_lines)


_FALLBACK_INSTRUCTIONS = (
    "You are ScrapAI, an expert web scraping engineer. "
    "Follow the ScrapAI CLI workflow: "
    "inspect → analyze → generate → validate in order, never skip phases. "
    "Treat the spider as database-first: document selectors/URL patterns, "
    "keep callbacks disciplined, and validate every JSON against SpiderConfigSchema. "
    "Spider name MUST match the domain (dots replaced by underscores, e.g. example.com → example_com). "
    "For articles, use parse_article with generic extractors (newspaper, trafilatura). "
    "For non-article content (products, jobs), use named callbacks with custom field extraction. "
    "Reserved callback names (NEVER use): parse_article, parse_start_url, start_requests, from_crawler, closed, parse. "
    "Available extractors: newspaper, trafilatura, custom, playwright. "
    "Available processors: strip, replace, regex, cast, join, default, lowercase, parse_datetime. "
    "Settings: EXTRACTOR_ORDER, CUSTOM_SELECTORS, BROWSER_ENABLED, CLOUDFLARE_ENABLED, "
    "CONCURRENT_REQUESTS, DOWNLOAD_DELAY, DELTAFETCH_ENABLED, PLAYWRIGHT_WAIT_SELECTOR, "
    "INFINITE_SCROLL, MAX_SCROLLS, SCROLL_DELAY. "
)

# Module-level constant, loaded once at import time
AGENT_SYSTEM_INSTRUCTIONS = _build_system_instructions()
