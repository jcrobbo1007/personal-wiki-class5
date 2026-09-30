---
title: Deep Q-Networks
topic: Concepts
source_ids: [pacman-dqn]
note_id: deep-q-networks
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Deep Q-Networks

*How the DQN in the Pac-Man project observes, acts, is rewarded and learns.* · Topic: Concepts · Back to [[index]]

## Summary
This page explains the Deep Q-Network (DQN) mechanism used in the Ms. Pac-Man project, detailing what the agent observed, the actions it could take, and how it was rewarded. It also discusses observations regarding the learning process, such as the relationship between loss, score, and evaluation.

## Key details
*   **Observation:** The agent observed four consecutive game screens, each reduced to 84x84 grayscale and stacked, showing where everything is and the direction of movement (E1).
*   **Actions:** Ms. Pac-Man could make 9 actions: no-op, the four directions, and the four diagonals, and the network outputted an estimated future reward for each, normally picking the highest (E1).
*   **Reward:** The reward was the game's own points (pellets, power pellets, ghosts, fruit), and during training, the reward per step was clipped to $[-1, +1]$ (E1).
*   **Learning Update:** The network was nudged toward `reward + 0.99 × (best value of the next screen)`, using a slower-moving copy of the network to supply the target (E1).
*   **Reward Signal Effect:** With clipping, a pellet, a power pellet, and a ghost were all worth the same $+1$ to the learner, and losing a life was worth nothing (`terminal_on_life_loss` is `false`) (E2).
*   **Data Usage:** Replay held 5,000 decisions, sampled in batches of 32, meaning the network only learned from its own most recent play (E2).

## Related notes

- [[Ms Pac-Man DQN]] — the project where this was trained
- [[Exploration vs Exploitation]] — the epsilon setting that decides random versus greedy moves
- [[Loss vs Real Performance]] — DQN loss tracks a moving target, not play quality

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[Pac-Man DQN Project]] — section "What the agent observes, does, and is rewarded for", lines 213-226
- E2: [[Pac-Man DQN Project]] — section "Reading this against the Class 3 material", lines 227-256
