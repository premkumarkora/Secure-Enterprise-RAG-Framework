# Secure Enterprise RAG Framework (Privacy-First Architecture)

## Overview
A reference architecture for a **Zero-Trust Retrieval-Augmented Generation (RAG)** system designed for highly regulated industries (Healthcare, Banking, Government). 

Unlike standard RAG implementations, this framework prioritizes **Data Sovereignty** and **PII Protection** by implementing an "airlock" ingestion strategy: sensitive entities are detected and redacted *before* vectorization, ensuring no PII ever enters the semantic search index or the LLM context window without strict authorization.

## 🏗️ Architecture

This system follows a "Defense in Depth" approach to AI governance.

```mermaid
%%{
  init: {
    'theme': 'base',
    'themeVariables': {
      'primaryColor': '#BB2588',
      'primaryTextColor': '#fff',
      'primaryBorderColor': '#7C0000',
      'lineColor': '#F8F9FA',
      'secondaryColor': '#006100',
      'tertiaryColor': '#fff'
    }
  }
}%%

graph TD
    %% --- Node Styles ---
    classDef security fill:#ff00bf,stroke:#fff,stroke-width:2px,color:#fff;
    classDef ai fill:#00bfff,stroke:#fff,stroke-width:2px,color:#fff;
    classDef db fill:#ffd700,stroke:#333,stroke-width:2px,color:#000;
    classDef standard fill:#333,stroke:#fff,stroke-width:2px,color:#fff;

    %% --- External Nodes ---
    User["End User (Authenticated)"]:::standard -->|Query| API["API Gateway / Orchestrator"]:::standard
    
    %% --- Subgraph 1: Ingestion ---
    subgraph Ingestion ["Ingestion Pipeline (Secure)"]
        direction TB
        Docs["Raw Documents"]:::standard -->|Extract Text| PII_Scan["PII Detector (Microsoft Presidio/BERT)"]
        PII_Scan -->|Detected Entities| PII_Mask["Anonymization Layer"]
        PII_Mask -->|Cleaned Text| Chunker["Semantic Chunker"]:::standard
        Chunker -->|Embed| Embedding_Model["Private Embedding Model"]
        Embedding_Model -->|Vectors + ACL Metadata| VectorDB[("Vector DB with RBAC")]
    end
    
    %% --- Subgraph 2: RAG Loop ---
    subgraph RAG ["Retrieval & Generation (RAG)"]
        direction TB
        API -->|1. Sanitize Query| Guardrail_Input["Input Guardrails"]
        Guardrail_Input -->|2. Search| VectorDB
        VectorDB -->|3. Retrieve Top-K| ReRanker["Cross-Encoder Reranker"]
        ReRanker -->|4. Top-N Context| Context_Window["Context Window"]:::standard
        
        Context_Window -->|5. Assemble Prompt| LLM_Gateway["LLM Gateway (LiteLLM/MLFlow)"]:::standard
        LLM_Gateway -->|6. Generate| LLM["Enterprise LLM (Hosting: On-Prem/Private VPC)"]
        
        LLM -->|7. Raw Response| PII_Deanonymize["De-Anonymization (Optional)"]
        PII_Deanonymize -->|8. Audit Log| Audit["Compliance Audit Log"]
    end

    Audit --> API
    
    %% --- Apply Specific Node Colors ---
    class PII_Scan,PII_Mask,Guardrail_Input,Audit security;
    class LLM,Embedding_Model,ReRanker ai;
    class VectorDB db;
    
    %% --- FORCE DARK MODE FOR SUBGRAPHS ---
    style Ingestion fill:#1a1a1a,stroke:#fff,stroke-width:2px,color:#fff
    style RAG fill:#1a1a1a,stroke:#fff,stroke-width:2px,color:#fff
```
