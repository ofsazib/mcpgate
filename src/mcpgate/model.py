"""Normalized data models for MCP server snapshots and lint findings."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolInfo(BaseModel):
    """A tool definition as advertised by an MCP server."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None


class ResourceInfo(BaseModel):
    """A resource definition as advertised by an MCP server."""

    uri: str
    name: str = ""
    description: str = ""
    mime_type: str | None = None


class PromptInfo(BaseModel):
    """A prompt template definition as advertised by an MCP server."""

    name: str
    description: str = ""
    arguments: list[str] = Field(default_factory=list)


class Finding(BaseModel):
    """A single lint finding produced by a rule."""

    code: str
    severity: str  # "error" | "warning" | "info"
    message: str
    source: str  # e.g. "tools/search"


class ServerSnapshot(BaseModel):
    """Full definition snapshot of an MCP server, taken over the protocol."""

    server_name: str = ""
    server_version: str = ""
    protocol_version: str = ""
    instructions: str = ""
    capabilities: list[str] = Field(default_factory=list)
    tools: list[ToolInfo] = Field(default_factory=list)
    resources: list[ResourceInfo] = Field(default_factory=list)
    prompts: list[PromptInfo] = Field(default_factory=list)
    latency_ms: float = 0.0
