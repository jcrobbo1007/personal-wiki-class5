---
title: Embeddings and Attention
topic: Concepts
source_ids: [custom-llm]
note_id: embeddings-and-attention
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Embeddings and Attention

*How the Class 4 model turned words into vectors and used earlier context.* · Topic: Concepts · Back to [[index]]

## Summary
Embeddings represent words as 64-number vectors, which learn meaning through contextual training rather than explicit dictionaries. Attention mechanisms allow tokens to focus on earlier context, which is crucial for tasks like next-token prediction. However, the embedding space did not capture which antonym goes with which: it grouped every antonym-slot word together.

## Key details
* A word is traced from text to an ID, and then to a 64-number vector (embedding) (E1).
* The learned meaning of a word resides in the substantial movement of its embedding vector after training, not in a dictionary (E1).
* For the prefix `the customer`, the untrained next-token distribution was nearly flat, while the trained distribution concentrated on verbs a customer plausibly performs (E2).
* Attention mechanisms allow a token to attend to earlier tokens and itself, but cannot look forward (causal mask) (E3).
* In the embedding space `quiet`'s nearest neighbours are `green` (0.692), `noisy` (0.682) and `hot` (0.678): training pushed every word used in the antonym slot into one neighbourhood because they share the same contexts (E4).
* The model learned which words fill the antonym slot, not which word pairs with which: the same "slot, not pairing" conclusion the eval probabilities give (E4).

## Related notes

- [[Custom nanoGPT LLM]] — the model these were traced in
- [[Translation Sensitivity]] — contrast: MNIST had no shared learned features at all

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Custom LLM Project]] — section "One word traced: text → ID → 64-number vector", lines 169-189
- E2: [[Custom LLM Project]] — section "Next-token probabilities for the same prefix", lines 213-229
- E3: [[Custom LLM Project]] — section "How attention uses earlier context", lines 230-246
- E4: [[Custom LLM Project]] — section "The embedding space, and why opposites failed", lines 247-274
