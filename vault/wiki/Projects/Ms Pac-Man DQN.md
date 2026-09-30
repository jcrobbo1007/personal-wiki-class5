---
title: Ms Pac-Man DQN
topic: Projects
source_ids: [pacman-dqn]
note_id: ms-pac-man-dqn
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Ms Pac-Man DQN

*Class 3 reinforcement-learning run: settings, before/after scores and what the gain really was.* · Topic: Projects · Back to [[index]]

## Summary
This page documents the training and evaluation of a Deep Q-Network (DQN) agent for Ms. Pac-Man using the class notebook with three chosen settings. The mean evaluation score rose on all five paired seeds, which supports the direction of the gain, but five games estimate its size poorly, and the training log shows the gain came from scoring faster rather than surviving longer.

## Key details
* The mean score improved from 492.0 for the untrained network to 876.0 after 1,000 training games, a change of +384.0 (E1, E4).
* The improvement was observed across five paired evaluation games using the same seeds, with all 5 seeds showing improvement (E1, E4).
* The training utilized 1,000 episodes, resulting in 596,589 total decisions and 148,898 learning updates (E3).
* The exploration rate was set to `0.10` for all 1,000 games, fixed with no decay after a 1,000-decision random warm-up; a lower rate was defensible partly because sticky actions already add randomness (E2).
* The learning rate was set to `0.0002`, which was doubled from the reference because learning updates were the scarce resource (E2).
* Elapsed time was 12:48 (46,108 s), but that includes about 11.5 h with the laptop asleep; actual training was roughly 1:16 (E3).
* The evaluation used a 3,000-decision cap and 5% exploration, comparing before and after the 1,000 episodes of training (E4).

## Related notes

- [[Deep Q-Networks]] — the algorithm this project trained
- [[Exploration vs Exploitation]] — why exploration was set to 0.10 and held constant
- [[Learning Rate Choices]] — why the rate was doubled to 0.0002
- [[Evaluation and Small Samples]] — what five paired games can and cannot prove

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Pac-Man DQN Project]] — section "Ms. Pac-Man DQN — Class 3", lines 1-13
- E2: [[Pac-Man DQN Project]] — section "My three settings", lines 27-52
- E3: [[Pac-Man DQN Project]] — section "What actually ran", lines 83-103
- E4: [[Pac-Man DQN Project]] — section "Evaluation: all five games, before and after", lines 104-125
