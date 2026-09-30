---
title: Learning Rate Choices
topic: Concepts
source_ids: [custom-llm, mnist, pacman-dqn]
note_id: learning-rate-choices
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Learning Rate Choices

*The learning rates chosen in all three projects and the reasoning behind each.* · Topic: Concepts · Back to [[index]]

## Summary
This page compares the learning rates used in different projects, highlighting the rationale behind the specific values chosen for each task. The choices varied based on resource constraints, training budget, and the specific learning schedule implemented in the respective notebooks.

## Key details
*   The Pac-Man DQN project used a learning rate of `0.0002`, which was doubled from a `0.0001` reference because learning updates were the scarce resource (E1).
*   The Custom LLM Project used a learning rate of `0.001`, which is a peak value because the notebook applies a 100-step warmup followed by cosine decay, meaning the first update uses a multiplier of 1/100 (E2, E3).
*   In the Custom LLM Project, the first update's learning rate was `1e-05`, not the chosen `0.001`, due to the warmup mechanism (E3).
*   The MNIST From Scratch log used a learning rate of `0.5` for 300 epochs with zero randomness (E4).
*   The Pac-Man DQN exploration rate was fixed at `0.10` because the environment already injects randomness, and this rate brought training closer to the `5%` used in evaluation (E1).
*   The learning rate in the Pac-Man DQN project was kept well short of `1e-3` given a `5,000`-transition replay (E1).

## Related notes

- [[Ms Pac-Man DQN]] — 0.0002, doubled from the 0.0001 reference
- [[Custom nanoGPT LLM]] — 0.001 peak with warmup
- [[MNIST From Scratch]] — 0.5 with plain gradient descent

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Pac-Man DQN Project]] — section "My three settings", lines 27-52
- E2: [[Custom LLM Project]] — section "My choices and prediction", lines 20-32
- E3: [[Custom LLM Project]] — section "One real gradient and weight update", lines 190-212
- E4: [[MNIST From Scratch Log]] — section "Class 3 — MNIST from scratch, run log", lines 1-8
