"""
LLM-powered Column Description Generator
- Generates semantic column descriptions and metadata per table
- Integrates with Phoenix tracing if enabled
- Designed for batch, low-cost, deterministic enrichment
"""
from __future__ import annotations

import json
import logging
import os
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.config import settings
from app.core.phoenix_config import PhoenixTracer
from .models import DatabaseSchema, TableSchema, DatabaseConnection

logger = logging.getLogger(__name__)


def _safe_str_type(t: Any) -> str:
    try:
        return str(t)
    except Exception:
        return type(t).__name__


class ColumnDescriptionGenerator:
    """Generates per-column semantic descriptions and metadata using an LLM.

    Output fields per column:
      - llm_description: str
      - semantic_role: str (e.g., identifier, date, amount, categorical, status)
      - sensitivity: str (e.g., pii, phi, confidential, public)
      - unit: Optional[str] (e.g., INR, USD, percentage, days)
      - aliases: List[str]
      - business_rules: List[str]
      - quality_notes: List[str]
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        tracer: Optional[PhoenixTracer] = None,
        enabled: Optional[bool] = None,
    ) -> None:
        self.llm = llm
        self.tracer = tracer or PhoenixTracer()
        # Feature flag with safe defaults
        if enabled is None:
            enabled_env = os.getenv("ENABLE_LLM_COLUMN_ENRICHMENT", "true").lower()
            self.enabled = getattr(settings, "ENABLE_LLM_COLUMN_ENRICHMENT", enabled_env in ("1", "true", "yes"))
        else:
            self.enabled = enabled

    async def enrich_and_apply(self, schema: DatabaseSchema, connection_id: str) -> DatabaseSchema:
        """Run enrichment for each table and mutate schema in-place to add metadata to columns.
        Returns the same schema reference for convenience.
        """
        if not self.enabled:
            logger.info("LLM column enrichment disabled by feature flag")
            return schema

        for table in schema.tables:
            try:
                await self._enrich_table_columns(schema, table, connection_id)
            except Exception as e:
                logger.warning(f"Column enrichment failed for table {table.table_name}: {e}")
        return schema

    async def _enrich_table_columns(self, schema: DatabaseSchema, table: TableSchema, connection_id: str) -> None:
        """Generate enrichment JSON for a single table and attach to each column dict."""
        if not table.columns:
            return

        sys_prompt = (
            "You are a senior data modeler. Given a database table and its columns, "
            "produce a compact JSON object that enriches each column with semantic information. "
            "Only output JSON, no explanation."
        )

        # Build concise table context
        cols_summary = [
            {
                "name": c.get("name") or c.get("column_name") or "",
                "type": _safe_str_type(c.get("type") or c.get("data_type") or ""),
                "nullable": bool(c.get("nullable", c.get("is_nullable", True))),
                "comment": c.get("comment") or "",
            }
            for c in table.columns
        ]

        fk_summary: List[str] = []
        try:
            for fk in getattr(table, "foreign_keys", []) or []:
                # SQLAlchemy inspector returns dicts for FK, normalize
                src_cols = fk.get("constrained_columns") or []
                tgt_table = fk.get("referred_table") or fk.get("referred_table_name") or ""
                tgt_cols = fk.get("referred_columns") or []
                if src_cols and tgt_table:
                    fk_summary.append(f"{','.join(src_cols)} -> {tgt_table}.{','.join(tgt_cols)}")
        except Exception:
            pass

        user_instructions = {
            "database": schema.database_name,
            "table": table.table_name,
            "primary_keys": getattr(table, "primary_keys", []) or [],
            "foreign_keys": fk_summary,
            "columns": cols_summary,
            "output_schema": {
                "<column_name>": {
                    "llm_description": "string",
                    "semantic_role": "identifier|date|amount|categorical|status|text|flag|metric|dimension",
                    "sensitivity": "pii|phi|confidential|public|none",
                    "unit": "string|null",
                    "aliases": ["string", "..."],
                    "business_rules": ["string", "..."],
                    "quality_notes": ["string", "..."]
                }
            },
            "requirements": [
                "Be terse and factual.",
                "Prefer domain-agnostic roles unless clear.",
                "Do not invent units without clear hints.",
                "If unsure, set unit to null and sensitivity to 'none'.",
                "Output valid JSON without comments or markdown fences.",
            ],
        }

        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=json.dumps(user_instructions, ensure_ascii=False)),
        ]

        # Trace with Phoenix if available
        span_cm = self.tracer.trace_context_template_operation_cm(
            operation="column_enrichment",
            connection_id=connection_id,
            table=table.table_name,
        )

        with span_cm:
            resp = await self.llm.ainvoke(messages)  # type: ignore[attr-defined]
            content: str = getattr(resp, "content", "") or ""

        enrichment = self._parse_json(content)
        if not isinstance(enrichment, dict):
            logger.warning(f"Enrichment returned non-dict for table {table.table_name}")
            return

        # Apply per-column
        col_index = {c.get("name") or c.get("column_name"): c for c in table.columns}
        for col_name, meta in enrichment.items():
            target = col_index.get(col_name)
            if not target or not isinstance(meta, dict):
                continue
            # Merge fields, preserving existing keys
            target.setdefault("llm_description", meta.get("llm_description"))
            target.setdefault("semantic_role", meta.get("semantic_role"))
            target.setdefault("sensitivity", meta.get("sensitivity"))
            target.setdefault("unit", meta.get("unit"))
            # Normalize list-like fields
            aliases = meta.get("aliases") or []
            if isinstance(aliases, str):
                aliases = [aliases]
            business_rules = meta.get("business_rules") or []
            if isinstance(business_rules, str):
                business_rules = [business_rules]
            quality_notes = meta.get("quality_notes") or []
            if isinstance(quality_notes, str):
                quality_notes = [quality_notes]
            target.setdefault("aliases", aliases)
            target.setdefault("business_rules", business_rules)
            target.setdefault("quality_notes", quality_notes)

    def _parse_json(self, text: str) -> Any:
        """Extract and parse JSON from an LLM response reliably."""
        text = (text or "").strip()
        if not text:
            return {}
        # Try raw
        try:
            return json.loads(text)
        except Exception:
            pass
        # Try fenced code blocks
        try:
            if "```" in text:
                fence_split = text.split("```")
                # choose the largest JSON-looking block
                candidates = sorted((s for s in fence_split if s.strip()), key=len, reverse=True)
                for c in candidates:
                    c = c.strip()
                    if c.lower().startswith("json"):
                        c = c[4:].strip()
                    try:
                        return json.loads(c)
                    except Exception:
                        continue
        except Exception:
            pass
        # Fallback: attempt to find first { .. } span
        try:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start : end + 1])
        except Exception:
            pass
        return {}
