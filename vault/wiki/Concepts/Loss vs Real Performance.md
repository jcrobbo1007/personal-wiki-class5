---
title: Loss vs Real Performance
topic: Concepts
source_ids: [custom-llm, mnist, pacman-dqn]
note_id: loss-vs-real-performance
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Loss vs Real Performance

*Why a falling loss did not guarantee better behaviour in these projects.* · Topic: Concepts · Back to [[index]]

## Summary
This page compares the divergence between training loss metrics and actual performance across different projects. It highlights that loss values are often not the best indicator of play quality, as they can move independently of the observed score. The analysis shows that gains in model performance sometimes stem from factors not explicitly targeted by the training setup.

## Key details
* In the Pac-Man DQN project, the mean update loss rose for the first ~400 games and then settled near 0.11, failing to track the score panel (E1).
* For the Pac-Man DQN project, loss is not the metric that matters because it measures prediction error against a moving target, not play quality (E2).
* In the Custom LLM Project, loss values are small estimates because they are averaged over only 20 training and 20 validation documents, and losses between experiments are not directly comparable (E3).
* In the Custom LLM Project, a gain in score resulted from the model getting better at familiar words in unfamiliar phrasings, which was an unintended side effect (E4).
* For the MNIST From Scratch project, the loss calculation was cross-entropy: negative log of the probability given to the correct label, averaged over 60,000 images (E5).
* The MNIST loss fell from 2.303 (pure guessing) to 0.326 (E5).

## Related notes

- [[Evaluation and Small Samples]] — behaviour has to be measured directly
- [[Deep Q-Networks]] — DQN loss is error against a moving target
- [[Custom nanoGPT LLM]] — coverage improved while pattern learning did not

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Pac-Man DQN Project]] — section "Training curves", lines 126-137
- E2: [[Pac-Man DQN Project]] — section "Reading this against the Class 3 material", lines 227-256
- E3: [[Custom LLM Project]] — section "Loss", lines 107-133
- E4: [[Custom LLM Project]] — section "What the extension actually did — three findings", lines 340-396
- E5: [[MNIST From Scratch Log]] — section "1. Where the model lives in the code", lines 9-18
