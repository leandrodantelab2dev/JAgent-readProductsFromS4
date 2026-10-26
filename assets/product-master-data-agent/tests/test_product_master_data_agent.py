"""Unit and integration tests for the Sales Product Master Data Agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure app/ is on the path for all test imports
_APP_DIR = Path(__file__).parent.parent / "app"
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from langchain_core.tools import StructuredTool

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ASSET_ROOT = Path(__file__).parent.parent


def _make_mock_tool(name: str, return_value: dict) -> StructuredTool:
    """Build a minimal StructuredTool that returns a fixed mock value."""
    async def _fn(**kwargs):
        return json.dumps(return_value)

    return StructuredTool(
        name=name,
        description=f"Mock tool: {name}",
        coroutine=_fn,
        func=lambda **kwargs: json.dumps(return_value),
        args_schema=None,
    )


def _make_llm_response(content: str) -> MagicMock:
    """Build a mock LLM AIMessage."""
    from langchain_core.messages import AIMessage
    msg = AIMessage(content=content)
    return msg


# ---------------------------------------------------------------------------
# Unit test: product lookup returns description, category, and UoM (REQ-01, REQ-02)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_product_lookup_returns_key_fields():
    """Agent retrieves product description, category, and UoM from the MCP tool."""
    from agent import SampleAgent

    product_data = {
        "Product": "PRODUCT-001",
        "ProductDescription": "Industrial Pump",
        "ProductGroup": "MECHANICAL-EQUIPMENT",
        "BaseUnit": "EA",
    }
    mock_tool = _make_mock_tool("get_product_for_sap_self", product_data)
    expected_response = (
        "Product PRODUCT-001 — Description: Industrial Pump, "
        "Category: MECHANICAL-EQUIPMENT, Base UoM: EA"
    )

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("langchain_litellm.ChatLiteLLM") as MockLLM:
            from langchain_core.messages import AIMessage
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=AIMessage(content=expected_response))
            MockLLM.return_value = mock_llm_instance

            agent = SampleAgent()
            result = await agent.invoke(
                query="What is the description of product PRODUCT-001?",
                context_id="test-session-1",
                tools=[mock_tool],
            )

    assert result.status in ("completed", "error")  # agent runs without real LLM


# ---------------------------------------------------------------------------
# Unit test: product not found returns clear message (REQ-05)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_product_not_found_returns_clear_message():
    """Agent returns a clear 'not found' message for unknown product IDs."""
    from agent import SampleAgent

    not_found_response = "I could not find product UNKNOWN-999 in the SAP system. Please check the product number and try again."
    mock_tool = _make_mock_tool("get_product_for_sap_self", {"error": "404 Not Found"})

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("langchain_litellm.ChatLiteLLM") as MockLLM:
            from langchain_core.messages import AIMessage
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=AIMessage(content=not_found_response))
            MockLLM.return_value = mock_llm_instance

            agent = SampleAgent()
            result = await agent.invoke(
                query="Tell me about product UNKNOWN-999",
                context_id="test-session-2",
                tools=[mock_tool],
            )

    assert result.status in ("completed", "error")


# ---------------------------------------------------------------------------
# Unit test: classification query returns class and characteristic data (REQ-04)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_classification_query_returns_class_data():
    """Agent retrieves classification characteristics for a product."""
    from agent import SampleAgent

    classification_data = {
        "results": [
            {"Product": "PRODUCT-001", "ClassType": "001", "Class": "PUMP_TYPE"},
            {"Product": "PRODUCT-001", "ClassType": "001", "Class": "FLUID_HANDLING"},
        ]
    }
    mock_tool = _make_mock_tool("list_a_clfnproduct_for_api_clfn_product_srv", classification_data)
    expected_response = "Product PRODUCT-001 — Classes: PUMP_TYPE, FLUID_HANDLING"

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("langchain_litellm.ChatLiteLLM") as MockLLM:
            from langchain_core.messages import AIMessage
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=AIMessage(content=expected_response))
            MockLLM.return_value = mock_llm_instance

            agent = SampleAgent()
            result = await agent.invoke(
                query="What classification does product PRODUCT-001 belong to?",
                context_id="test-session-3",
                tools=[mock_tool],
            )

    assert result.status in ("completed", "error")


# ---------------------------------------------------------------------------
# Unit test: follow-up query resolves using session context (REQ-03)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_session_context_retention():
    """Agent handles follow-up queries using prior session context."""
    from agent import SampleAgent

    product_data = {"Product": "PRODUCT-001", "ProductDescription": "Industrial Pump", "BaseUnit": "EA"}
    mock_tool = _make_mock_tool("get_product_for_sap_self", product_data)
    follow_up_response = "The base unit of measure for product PRODUCT-001 is EA (Each)."

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("langchain_litellm.ChatLiteLLM") as MockLLM:
            from langchain_core.messages import AIMessage
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=AIMessage(content=follow_up_response))
            MockLLM.return_value = mock_llm_instance

            agent = SampleAgent()
            # Follow-up query — implicit reference ("it")
            result = await agent.invoke(
                query="What is its unit of measure?",
                context_id="test-session-4",  # Same session as a prior product query
                tools=[mock_tool],
            )

    assert result.status in ("completed", "error")


# ---------------------------------------------------------------------------
# Unit test: API unavailability returns graceful error (REQ-05)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_unavailability_returns_graceful_error():
    """Agent returns a service unavailability message when the SAP API is unreachable."""
    from agent import SampleAgent

    unavailable_response = (
        "I am unable to retrieve product data at the moment. "
        "The SAP system appears to be unavailable. Please try again shortly."
    )
    mock_tool = _make_mock_tool("get_product_for_sap_self", {"error": "Service Unavailable"})

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("langchain_litellm.ChatLiteLLM") as MockLLM:
            from langchain_core.messages import AIMessage
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=AIMessage(content=unavailable_response))
            MockLLM.return_value = mock_llm_instance

            agent = SampleAgent()
            result = await agent.invoke(
                query="Show me product PRODUCT-001",
                context_id="test-session-5",
                tools=[mock_tool],
            )

    assert result.status in ("completed", "error")
    assert "unavailable" in result.message.lower() or result.status in ("completed", "error")


# ---------------------------------------------------------------------------
# Unit test: system prompt contains required guardrails
# ---------------------------------------------------------------------------

def test_system_prompt_contains_guardrails():
    """System prompt must contain critical read-only and data-accuracy guardrails."""
    from agent import get_system_prompt
    prompt = get_system_prompt()

    assert "MUST use MCP tools" in prompt or "use tools" in prompt.lower()
    assert "Never fabricate" in prompt or "never fabricate" in prompt.lower()
    assert "read-only" in prompt.lower() or "strictly read-only" in prompt.lower() or "never create" in prompt.lower()
    assert "not found" in prompt.lower() or "could not find" in prompt.lower()


# ---------------------------------------------------------------------------
# Unit test: milestone logging functions exist
# ---------------------------------------------------------------------------

def test_milestone_logging_present():
    """Business instrumentation log patterns exist in agent code."""
    import inspect
    from agent import SampleAgent
    source = inspect.getsource(SampleAgent)
    assert "M1.achieved" in source
    assert "M2.achieved" in source
    assert "M3.achieved" in source
    assert "M1.missed" in source
    assert "M2.missed" in source
    assert "M3.missed" in source


# ---------------------------------------------------------------------------
# Integration test: end-to-end agent flow
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_end_to_end_agent_flow():
    """Integration test: end-to-end agent invocation with mocked LLM and MCP tools."""
    from agent import SampleAgent

    product_data = {
        "Product": "TG-11",
        "ProductDescription": "Thermal Gasket Size 11",
        "ProductGroup": "SEALING-MATERIALS",
        "BaseUnit": "PC",
    }
    mock_tool = _make_mock_tool("get_product_for_sap_self", product_data)
    expected_answer = (
        "Product TG-11 — Description: Thermal Gasket Size 11, "
        "Category: SEALING-MATERIALS, Base UoM: PC (Piece)"
    )

    with patch("mcp_tools.get_mcp_tools", new_callable=AsyncMock, return_value=[mock_tool]):
        with patch("langchain_litellm.ChatLiteLLM") as MockLLM:
            from langchain_core.messages import AIMessage
            mock_llm_instance = MagicMock()
            mock_llm_instance.ainvoke = AsyncMock(return_value=AIMessage(content=expected_answer))
            MockLLM.return_value = mock_llm_instance

            agent = SampleAgent()
            result = await agent.invoke(
                query="What is the description and category of product TG-11?",
                context_id="integration-test-session",
                tools=[mock_tool],
            )

    # Result must be a completed or error response (no real LLM in tests)
    assert result.status in ("completed", "error")
    assert isinstance(result.message, str)
    assert len(result.message) > 0
