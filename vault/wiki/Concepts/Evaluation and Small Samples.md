---
title: Evaluation and Small Samples
topic: Concepts
source_ids: [custom-llm, mnist, pacman-dqn]
note_id: evaluation-and-small-samples
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Evaluation and Small Samples

*How each project was evaluated and how much a small eval set can prove.* · Topic: Concepts · Back to [[index]]

## Summary
This page details the evaluation designs used in various projects and discusses the statistical limitations of small sample evaluations. It highlights that evaluation results are context-dependent and that loss metrics do not always correlate with play quality.

## Key details
* For the Pac-Man DQN project, evaluation involved running five games before and after training using the same seeds, 5% exploration, and a 3,000-decision cap (E1).
* The baseline for the Pac-Man evaluation was an untrained network, not a random-action agent (E1).
* The mean Pac-Man score went from 492.0 to 876.0 (+384.0) across the five games; mean decisions per game went from 589.0 to 712.2 (E1).
* Evaluation is considered a decision rather than a number, and while paired evaluations show a supported direction (5 out of 5 seeds improved), the magnitude is uncertain due to small sample size (E2).
* The reward signal suggests the agent learned the policy described by the rewards, as losing a life is worth nothing, and rewards heavily favor collecting things soon (E2).
* In the Custom LLM project, scoring for fixed 48-case language evals is based on the highest probability among four single-word choices (E3).
* In the Custom LLM project, the trained model scored 16/16 on starter patterns but 0/24 on extension challenges in both experiments (E4).
* The MNIST From Scratch model achieved 91.0% accuracy on training data and 91.5% on a test set of 10,000 unseen digits (E5).

## Related notes

- [[Ms Pac-Man DQN]] — five paired seeds before and after training
- [[Custom nanoGPT LLM]] — 48 fixed language cases
- [[MNIST From Scratch]] — 10,000 held-out test digits
- [[Loss vs Real Performance]] — why evaluation beats reading a loss curve

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Pac-Man DQN Project]] — section "Evaluation: all five games, before and after", lines 104-125
- E2: [[Pac-Man DQN Project]] — section "Reading this against the Class 3 material", lines 227-256
- E3: [[Custom LLM Project]] — section "The fixed 48-case language evals", lines 293-301
- E4: [[Custom LLM Project]] — section "By group", lines 316-323
- E5: [[MNIST From Scratch Log]] — section "2. Accuracy", lines 19-24
