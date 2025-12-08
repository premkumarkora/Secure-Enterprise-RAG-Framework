graph TD
    %% Styling
    classDef security fill:#f9f,stroke:#333,stroke-width:2px;
    classDef ai fill:#ccf,stroke:#333,stroke-width:2px;
    classDef db fill:#ff9,stroke:#333,stroke-width:2px;

    User[End User (Authenticated)] -->|Query| API[API Gateway / Orchestrator]
    
    subgraph "Ingestion Pipeline (Secure)"
        Docs[Raw Documents] -->|Extract Text| PII_Scan[PII Detector (Microsoft Presidio/BERT)]
        PII_Scan -->|Detected Entities| PII_Mask[Anonymization Layer]
        PII_Mask -->|Cleaned Text| Chunker[Semantic Chunker]
        Chunker -->|Embed| Embedding_Model[Private Embedding Model]
        Embedding_Model -->|Vectors + ACL Metadata| VectorDB[(Vector DB with RBAC)]
    end

    subgraph "Retrieval & Generation (RAG)"
        API -->|1. Sanitize Query| Guardrail_Input[Input Guardrails]
        Guardrail_Input -->|2. Search| VectorDB
        VectorDB -->|3. Retrieve Top-K| ReRanker[Cross-Encoder Reranker]
        ReRanker -->|4. Top-N Context| Context_Window
        
        Context_Window -->|5. Assemble Prompt| LLM_Gateway[LLM Gateway (LiteLLM/MLFlow)]
        LLM_Gateway -->|6. Generate| LLM[Enterprise LLM (Hosting: On-Prem/Private VPC)]
        
        LLM -->|7. Raw Response| PII_Deanonymize[De-Anonymization (Optional)]
        PII_Deanonymize -->|8. Audit Log| Audit[Compliance Audit Log]
    end

    Audit --> API
    
    class PII_Scan,PII_Mask,Guardrail_Input,Audit security;
    class LLM,Embedding_Model,ReRanker ai;
    class VectorDB db;
