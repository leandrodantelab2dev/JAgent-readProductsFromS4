# Specification: product-master-data-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md` and `intent.md`)
- [x] Bootstrap agent code in `assets/product-master-data-agent/` using instructions from the sap-agent-bootstrap section (invoke from inside `assets/product-master-data-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> Read [guidelines-agent-skills.md](../guidelines-agent-skills.md) before deciding.

No runtime skills are required for this agent. The product master data lookup logic is straightforward enough to be handled entirely via the system prompt and MCP tool calls. No multi-step workflows, approval chains, or complex domain rules apply.

---

## Project-Specific Tasks

### System Prompt & Agent Identity

- [x] Open `assets/product-master-data-agent/app/agent.py` and update the system prompt to define the agent's identity and behaviour:
  - The agent is a **Sales Product Master Data Assistant** for Sales Representatives
  - It answers natural language questions about SAP S/4HANA product master data (product descriptions, categories, units of measure, classification characteristics)
  - It **only** retrieves data via MCP tools — it never fabricates, guesses, or invents product data
  - It responds in plain, business-friendly language — no raw JSON, no field codes without explanation
  - It retains context within a conversation session to handle follow-up questions (e.g., "What category does it belong to?" after an initial product lookup)
  - When a product is not found or a field has no value in SAP, it states this clearly rather than omitting the information silently
  - It never performs any create, update, or delete operations on SAP data — strictly read-only
  - When the SAP API is unavailable, it responds with a clear service unavailability message — never with fabricated data
  - If the query is ambiguous (no product ID or name identifiable), it asks a clarifying question before calling any tool

### Product Master Data Retrieval (REQ-01, REQ-02)

- [x] Implement tool invocation for **basic product data** retrieval using the MCP tool generated from `CE_PRODUCT_0003` (preferred Cloud Edition API):
  - The agent must be able to retrieve: product description, product category, base unit of measure
  - Use the `CE_PRODUCT_0003` MCP tool as the primary tool for product header data
  - Fall back to `API_PRODUCT_SRV` only if `CE_PRODUCT_0003` does not return the required fields
- [x] Ensure the agent extracts the product identifier (product number or name) from the user's natural language query before calling the tool
- [x] Ensure the agent formats the tool response into a clear, human-readable answer (e.g., "Product 1000123 — Description: Industrial Pump, Category: Mechanical Equipment, Base UoM: Each")

### Product Classification Data Retrieval (REQ-04)

- [x] Implement tool invocation for **classification data** retrieval using the MCP tool generated from `API_CLFN_PRODUCT_SRV`:
  - The agent must be able to retrieve classification class assignments and characteristic values for a product
  - Trigger this tool when the user's query mentions classification, characteristics, class, or attributes
- [x] Format classification data in a readable way (e.g., "Product 1000123 — Class: PUMP_TYPE, Characteristic: FLOW_RATE = 500 l/min")

### Conversational Context Retention (REQ-03)

- [x] Verify the agent framework retains prior turn context within a session (standard A2A session handling)
- [x] Add an instruction in the system prompt that the agent should resolve pronouns and implicit references (e.g., "it", "this product", "the same one") using the last product discussed in the session

### Transparent Handling of Missing or Incomplete Data (REQ-05)

- [x] Add system prompt instructions to handle the following cases explicitly:
  - Product not found in SAP → respond: "I could not find product [ID/name] in the SAP system. Please check the product number and try again."
  - Field exists but has no value in SAP → respond: "The [field name] for product [ID] is not maintained in the SAP system."
  - SAP API is unreachable → respond: "I'm unable to retrieve product data at the moment. The SAP system appears to be unavailable. Please try again shortly."

### Response Quality & Format

- [x] Ensure all responses:
  - Are in plain language, avoiding SAP internal codes without explanation
  - Lead with the most relevant information first (direct answer before details)
  - Are concise — no verbose preambles or unnecessary caveats
  - Include the product ID/number in the response for confirmation

---

## API Discovery Results

The following APIs were discovered and downloaded during specification:

| API Name | ORD ID | Spec File | Type |
|---|---|---|---|
| Product (Cloud Edition) | `sap.s4:apiResource:CE_PRODUCT_0003:v3` | `api-specs/CE_PRODUCT_0003.edmx` | OData |
| Product Master | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | `api-specs/API_PRODUCT_SRV.edmx` | OData |
| Product Master incl. Classification | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | `api-specs/API_CLFN_PRODUCT_SRV.edmx` | OData |

### MCP Tool Scope

```
MCP API: sap.s4:apiResource:CE_PRODUCT_0003:v3
MCP tool scope: read-only
Resources in scope: Product, ProductDescription, ProductPlant, ProductValuationAccount
```

```
MCP API: sap.s4:apiResource:API_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_Product, A_ProductDescription, A_ProductBasicText
```

```
MCP API: sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_ClfnProduct, A_ClfnProductClass, A_ClfnProductCharc
```

---

## Business Instrumentation

- [x] Implement business step instrumentation for each milestone from the PRD using structured logging and OpenTelemetry spans:

  | Milestone | ID | Log on Achievement | Log on Miss |
  |---|---|---|---|
  | Query Understanding | M1 | `M1.achieved: query understood — intent=product_lookup, product_ref=<extracted_ref>` | `M1.missed: query could not be interpreted as a product lookup — routing to clarification` |
  | Data Retrieval | M2 | `M2.achieved: product data retrieved — product_id=<id>, api=<api_name>, fields_returned=<count>` | `M2.missed: product data retrieval failed — product_id=<id>, api=<api_name>, error=<error_code>` |
  | Answer Delivery | M3 | `M3.achieved: answer delivered — product_id=<id>, response_length=<chars>` | `M3.missed: answer could not be generated — product_id=<id>, reason=<reason>` |
  | Context Retention | M4 | `M4.achieved: follow-up resolved using session context — session_id=<id>, turn=<turn_number>` | `M4.missed: context not available for follow-up — session_id=<id>, turn=<turn_number>` |
  | Validation | M5 | `M5.achieved: validation passed — test_cases=<count>, pass_rate=<pct>%` | `M5.missed: validation failed — test_cases=<count>, pass_rate=<pct>%, threshold=<threshold>%` |

- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.

- [x] Verify `specification/product-master-data-agent/api-specs/` exists with all three `.edmx` files
- [x] Invoke the `mcp-translation-file` skill to generate MCP translation files for each of the three API specs:
  - `api-specs/CE_PRODUCT_0003.edmx` → ORD ID: `sap.s4:apiResource:CE_PRODUCT_0003:v3`
  - `api-specs/API_PRODUCT_SRV.edmx` → ORD ID: `sap.s4:apiResource:API_PRODUCT_SRV:v1`
  - `api-specs/API_CLFN_PRODUCT_SRV.edmx` → ORD ID: `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1`
- [x] Invoke `setup-solution` skill to register the generated MCP assets in `solution.yaml` and `asset.yaml`
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — NEVER import directly from `sap_cloud_sdk.agentgateway` and NEVER create direct HTTP clients
- [x] Add MCP server dependencies to `asset.yaml` under `requires` — one entry per generated MCP server, using exact ORD IDs from generated assets. See [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for format.
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill (required before tests can run)

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write unit tests in `assets/product-master-data-agent/tests/` — at minimum one per tool:
  - Test: product lookup by product number returns description, category, and UoM
  - Test: product lookup for a non-existent product returns a clear "not found" message
  - Test: classification query returns class and characteristic data
  - Test: follow-up query with implicit product reference resolves correctly using session context
  - Test: API unavailability scenario returns a graceful error message (not fabricated data)
- [x] Write one integration test executing the end-to-end agent flow (mocked LLM + mocked MCP tools)
- [x] Run `pytest` from `assets/product-master-data-agent/` (no args) — if coverage < 70%, add tests
- [x] Run `pytest` again to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/product-master-data-agent/`
