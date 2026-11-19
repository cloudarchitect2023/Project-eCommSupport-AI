Skill

Agentic AI

Sub Skill

Introduction

Instruction

Project eCommSupport-AI
 
Objective Build a highly autonomous, production-ready Customer Support Agent for an eCommerce platform. The agent must seamlessly route between querying structured database tables for order fulfillment and unstructured vector databases for company policies, all while adhering to strict guardrails and cost optimizations.
 
System Architecture & Tech Stack
Orchestration OpenAI Python SDK (Tool Calling and Assistant logic).
Structured Data (MySQL) Product catalog, user profiles, and order history.
Tool Execution (MCP Server) A dedicated Python Model Context Protocol (MCP) server exposing database operations as standardized tools.
Unstructured Data (Pinecone) Vector database housing warranty details, return policies, and shipping FAQs.
Memory (Upstash Redis) Serverless Redis for distributed, persistent chat history and session management.
Observability & Evals (LangSmith) Tracing agent steps, evaluating response accuracy, and monitoring token costs.
 
Implementation Milestones

Milestone 1 The MCP Server for Structured Data

Students must isolate their database logic from their LLM orchestration by building an MCP server.
Task Create a local MySQL database with products, customers, and orders tables.
Task Build a Python MCP server (using the mcp SDK or fastmcp) that exposes specific, parameterized tools get_product_details, check_order_status, and place_order.
Constraint Direct SQL execution tools (like Text-to-SQL) are strictly forbidden for security reasons. All database interactions must be parameterized Python functions exposed via MCP.
 
Milestone 2 Advanced RAG with Pinecone

Students must implement and benchmark three different retrieval strategies against a supplied dataset of complex returnwarranty policies.
Simple RAG Standard semantic search using OpenAI text embeddings.
HyDE (Hypothetical Document Embeddings) Prompting the LLM to write a hypothetical answer to the user's query, and embedding that answer to retrieve the actual policy.
Multi-Query Using an LLM to rewrite the user's query into three different semantic variations to maximize vector recall.
Task Compare the retrieval quality of these three approaches for multi-nuanced queries (e.g., Can I return a damaged laptop after 45 days if I bought the extended warranty).
 
Milestone 3 Agent Orchestration & Persistent Memory
Task Connect the OpenAI Agent to both the MCP client (for SQL tools) and the Pinecone retriever tool.
Task Implement persistent conversational memory using Upstash Redis. The agent must successfully recall a user's order number provided three turns prior.
 
Milestone 4 Guardrails & Context Optimization
Guardrails Implement strict input validation to block prompt injections and off-topic queries (e.g., Write me Python code or Who is the president). Ensure the agent gracefully declines.
CostContext Optimization Implement a context-window management strategy. Students must summarize older chat history in Upstash Redis rather than appending infinite tokens. They must also demonstrate model routing (e.g., using gpt-4o-mini for simple RAG and summarization, but escalating to gpt-4o for complex multi-tool reasoning).
 
Milestone 5 Evaluation via LangSmith
Task Create a Golden Dataset of 20 test cases encompassing simple queries, multi-step actions (checking order + asking about returns), and adversarial inputs.
Task Use LangSmith to evaluate the agent's performance, specifically measuring tool-calling accuracy, hallucination rates, and latency.
 
 
Evaluation Rubric
This rubric evaluates students on architectural maturity rather than just achieving a working prototype.
Criteria
Exemplary (90-100%)
Competent (70-89%)
Needs Work (70%)
Solution Approach & Architecture
Seamless integration of the MCP server. Agent routes intelligently between Pinecone and MySQL tools without hallucinating parameters.
MCP server works but agent struggles with complex routing; occasionally calls the wrong tool.
Missing MCP abstraction; raw SQL exposed to LLM, or fails to combine RAG with tool execution.
RAG Implementation & Choice of Techniques
Clear empirical evidence (via LangSmith) showing when HyDE or Multi-Query outperforms Simple RAG. Dynamic fallback implemented.
Implements all three RAG techniques, but lacks deep analysis of which works best for specific query types.
Only implements Simple RAG, or fails to properly chunk and embed the policy documents.
Optimization & Memory
Redis memory implements rolling summaries to cap token limits. Model routing demonstrably saves costs while maintaining accuracy.
Redis memory works but appends indefinitely. Uses a single expensive model for all tasks.
Memory drops between turns. Context window overflows on long conversations.
Guardrails & Security
Parameterized SQL prevents injection. Strong prompt boundaries prevent off-topic jailbreaks. PII is redacted before logging.
Basic guardrails implemented via system prompts, but susceptible to complex prompt injections or leaks minor PII.
No input validation. Agent happily answers off-topic questions or is vulnerable to SQL injection via MCP args.
Evaluations (LangSmith)
Comprehensive golden dataset. Custom evaluators track context precision, tool selection accuracy, and total cost per run.
Basic LangSmith tracing enabled, but lacks custom evaluators or a robust testing dataset.
No observability. Student cannot prove the application's accuracy or token usage objectively.
 