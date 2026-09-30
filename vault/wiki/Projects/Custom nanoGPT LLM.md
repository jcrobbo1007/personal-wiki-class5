---
title: Custom nanoGPT LLM
topic: Projects
source_ids: [custom-llm]
note_id: custom-nanogpt-llm
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Custom nanoGPT LLM

*Class 4 tiny word-level language model: two corpus experiments, 48 fixed evals and the coverage-vs-competence finding.* · Topic: Projects · Back to [[index]]

## Summary
This document details the results of two experiments using the nanoGPT model with word tokens to evaluate vocabulary coverage versus pattern learning. The main finding is that expanding the corpus to target opposites and negation increased vocabulary coverage but did not improve pattern learning, as the model failed on the newly covered cases.

## Key details
* The starter corpus resulted in 20/48 evals correct and 24/48 scorable after training (E1, E4).
* The expanded corpus targeting opposites and negation resulted in 24/48 correct and 29/48 scorable after training (E1, E4).
* The extension bought vocabulary coverage by making five of the six targeted cases go from unscorable to scored (E1).
* The extension bought no pattern learning, as every one of the five newly-scorable cases scored 0 (E1).
* Unrelated transfer cases jumped from 4/8 to 8/8 after the extension (E1).
* Accuracy among scorable cases fell slightly from 83.33% (starter) to 82.76% (expanded) (E4).
* The vocabulary cap of 512 never bound: exp 1 had 133 training types and exp 2 had 398, and every type was retained in both runs (E3).

## Related notes

- [[Embeddings and Attention]] — how the model represents words and uses context
- [[Learning Rate Choices]] — the 0.001 peak with warmup and cosine decay
- [[Loss vs Real Performance]] — validation loss plateaued while eval behaviour told a different story
- [[Evaluation and Small Samples]] — the fixed 48-case eval set and scorability

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Custom LLM Project]] — section "Custom LLM — Class 4 (nanoGPT, word tokens)", lines 1-19
- E2: [[Custom LLM Project]] — section "My choices and prediction", lines 20-32
- E3: [[Custom LLM Project]] — section "My run (both experiments)", lines 77-104
- E4: [[Custom LLM Project]] — section "Four-row comparison", lines 302-315
