# Sales Product Master Data AI Agent

An AI agent that enables Sales Representatives to ask natural language questions about product master data from SAP S/4HANA Public Cloud Edition and receive instant, accurate answers.

## Business challenge

Sales Representatives spend too much time navigating complex SAP S/4HANA screens to find basic product master data — such as product descriptions, categories, and units of measure. This slows them down during customer interactions and reduces selling time. An AI agent will allow them to ask questions in plain language and get instant, accurate answers directly from SAP S/4HANA Public Cloud.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to retrieve product information | 5 minutes | Under 30 seconds | — | Product Master Data Lookup (Lead to Cash) | user |

## Key Milestones

1. **Query Understanding** — Agent receives and correctly interprets a natural language product question from a Sales Representative.
2. **Data Retrieval** — Agent calls the relevant SAP S/4HANA product master data API and retrieves accurate product information.
3. **Answer Delivery** — Agent formats and returns a clear, readable answer to the Sales Representative.
4. **Context Retention** — Agent handles follow-up questions within the same conversation using prior context.
5. **Validation** — Agent is tested with representative Sales Rep queries and confirmed to return accurate data consistently.

## Business Architecture (RBA)

### End-to-End Process

Lead to Cash Standard B2B

### Process Hierarchy

```
Lead to Cash Standard B2B (E2E)
└── Plan to Optimize Marketing and Sales
    └── Plan prices and promotions (BPS-359_002)
        └── Plan and define sales prices
```

### Summary

Sales Representatives querying product master data maps to the Lead to Cash Standard B2B process, specifically the "Plan prices and promotions" sub-process, where SAP S/4HANA Cloud Public Edition provides the Sales Price Planning and Definition capability.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Webhook API ORD ID | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------ | ------------------- | ---- | ------------------- |
| Retrieve basic product details (description, category, unit of measure) | SAP S/4HANA Cloud Public Edition — Product Master API | `sap.s4:apiResource:API_PRODUCT_SRV:v1` | — | — | — | — | No | MCP translation file must be generated from API spec |
| Retrieve product with extended classification data | SAP S/4HANA Cloud Public Edition — Product Master incl. Classification | `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1` | — | — | — | — | No | OData API available; MCP translation file required |
| Retrieve latest product data (Cloud edition API) | SAP S/4HANA Cloud Public Edition — Product (CE) | `sap.s4:apiResource:CE_PRODUCT_0003:v3` | — | — | — | — | No | Preferred Cloud Edition API; MCP translation file required |
| Sales price planning and definition | SAP S/4HANA Cloud Public Edition — Sales Price Planning (SC1044) | `sap.s4:apiResource:SALESPRICE_0001:v1` | — | — | — | — | No | Out of initial scope; can be added in future iterations |

### Key findings

- SAP S/4HANA Cloud Public Edition provides all required product master data via standard OData APIs — no custom data source development needed.
- No pre-built MCP servers exist for these APIs in the customer landscape; MCP translation files must be generated from the API specifications during the specification phase.
- The "Pricing service" and "Sales Price and Discount List" APIs are marked unavailable in this landscape and must not be used.
- The primary APIs for the agent are `API_PRODUCT_SRV` (product master) and `CE_PRODUCT_0003` (Cloud Edition product — preferred).
- The solution is a pure AI Agent pattern: no fixed workflow is required as the agent reasons dynamically over natural language queries.
- Sales pricing data (`SALESPRICE_0001`) is available but out of scope for the initial version; it can be added in a future iteration.

## Recommendations

### Natural Language Product Master Data Agent for Sales

#### Executive Summary

A Python AI agent that answers product questions via S/4HANA APIs.

#### Recommended Solution

A pro-code Python AI agent (A2A protocol) integrated with SAP S/4HANA Cloud Public Edition product master data APIs via MCP tool calls. The agent accepts natural language questions from Sales Representatives, translates them into API calls, and returns clear, formatted answers — all without the Sales Rep needing to navigate SAP directly.

#### Problem Statement

Sales Representatives must navigate complex SAP S/4HANA screens to retrieve basic product information, causing delays during customer interactions and reducing productive selling time.

#### Affected User Roles

- Sales Representatives

#### Important factors

##### Reduces time-to-answer for product queries
Sales Reps can get product information in under 30 seconds by typing a plain-language question, eliminating the need to navigate multiple SAP screens.

##### Uses standard SAP APIs — no custom data layer required
All required product master data is available through standard SAP S/4HANA Cloud Public Edition OData APIs, keeping the solution maintainable and aligned with SAP best practices.

##### Extensible for future data domains
The agent architecture can easily be extended to cover pricing, stock availability, or product classifications in future iterations without redesigning the core.

#### Potential risks

##### MCP translation file generation required
No pre-built MCP servers exist for the target APIs. MCP translation files must be generated during the specification phase, adding a one-time setup step.

##### Data quality dependency
The accuracy of agent answers depends on the quality and completeness of product master data maintained in SAP S/4HANA. Incomplete records will result in incomplete answers.

#### Recommended solution category

AI Agent

#### Intent fit
90%
