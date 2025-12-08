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
    %% --- Styles for "Apple Liquid" Effect ---
    classDef liquidStart fill:#000000,stroke:#333,stroke-width:4px,color:#fff,rx:20,ry:20,shadow:10px;
    classDef liquidAgent fill:#8E2DE2,stroke:#4A00E0,stroke-width:2px,color:#fff,rx:15,ry:15,stroke-dasharray: 0;
    classDef liquidModel fill:#F80759,stroke:#BC4E9C,stroke-width:2px,color:#fff,rx:15,ry:15;
    classDef liquidData fill:#00F260,stroke:#0575E6,stroke-width:2px,color:#000,rx:10,ry:10;
    classDef liquidAction fill:#fff,stroke:#333,stroke-width:1px,color:#000,rx:5,ry:5,stroke-dasharray: 5 5;

    %% --- The Diagram Content ---
    subgraph " "
        direction TB
        
        Input([📄 Claims Documents]) :::liquidStart
        
        subgraph Orchestration [" 🧠 Multi-Agent Orchestrator "]
            direction TB
            Router{{" 🚦 Router Agent "}}:::liquidAgent
            
            subgraph Specialist_Agents [" Specialist Agents (CrewAI) "]
                Policy[(" 📜 Policy RAG \n (Vector DB) ")]:::liquidData
                Fraud[(" 🕵️ Fraud Detection \n (Anomaly Model) ")]:::liquidData
                Medical[(" 🏥 Medical Encoder \n (Fine-Tuned Llama) ")]:::liquidModel
            end
        end

        LLM[" 🔮 AWS Bedrock \n (Claude 3.5 Sonnet) "]:::liquidModel
        Decision{{" ✅ Decision Engine "}}:::liquidAgent
        Output([🚀 Approved/Rejected]) :::liquidStart

    end

    %% --- Connections ---
    Input -->|Ingest PDF/Img| Router
    Router -- "Context Retrieval" --> Policy
    Router -- "Risk Analysis" --> Fraud
    Router -- "Entity Extraction" --> Medical
    
    Policy & Fraud & Medical -.->|Aggregated Context| LLM
    LLM ==>|Reasoning Trace| Decision
    Decision -->|JSON Payload| Output

    %% --- Link Styling ---
    linkStyle 0,1,2,3,4,5,6,7 stroke-width:3px,fill:none,stroke:url(#gradient);
```
