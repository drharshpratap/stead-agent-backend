# Neosh Synthetic Knowledge Base for Stead Agent

This dataset is fictional and intended only for software testing and RAG demonstrations. It is not verified information about any real company. Do not present its policies, inventory, sample orders, safety details, SKUs, or compliance placeholders as real facts.

## Contents
- `documents/00_company_profile.md`: dataset framing and answer policy
- `documents/01_product_catalogue.md`: 10 product families and variants
- `documents/02_customer_policies.md`: fictional delivery, returns, warranty, payment, cancellation, support policies
- `documents/03_safety_and_handling.md`: conservative product handling and safety guidance
- `documents/04_compliance_register.md`: explicit missing/pending evidence and fictional placeholders
- `documents/05_inventory_snapshots.md`: historical synthetic inventory snapshot
- `documents/06_sample_orders.md`: sample order states for status and workflow questions
- `documents/07_faq_and_abstention.md`: FAQs and expected abstention cases
- `documents/08_rag_test_questions.md`: test questions across supported and unsupported topics
- `documents/09_expanded_test_records.md`: larger corpus for chunking/retrieval experiments

## Recommended RAG behavior
1. Search the dataset for each product/customer question.
2. Return a small set of relevant passages with source filenames.
3. Treat the synthetic inventory snapshot as historical, not live.
4. Do not treat `DEMO-COMP-*` as real certificates.
5. If the evidence is missing, stale, contradictory, or insufficient, abstain.
6. Do not combine unrelated passages to make unsupported claims.

## First integration
Put the `documents/` folder under your Stead Agent project, then create an indexing script and a separate retrieval module. Keep the agent's tool as a thin wrapper around the retrieval module.
