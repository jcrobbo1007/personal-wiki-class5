---
title: MNIST From Scratch
topic: Projects
source_ids: [mnist]
note_id: mnist-from-scratch
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# MNIST From Scratch

*Class 3 single-layer digit classifier in NumPy: 91.5% test accuracy and a collapse under pixel shifts.* · Topic: Projects · Back to [[index]]

## Summary
This page documents the results of an MNIST from scratch implementation, focusing on the model's performance, parameter structure, and observed errors. It was trained with the notebook's own settings (300 epochs, learning rate 0.5, zero-initialised weights, no randomness), so the numbers are exactly repeatable (E1).

## Key details
* The model used 7,850 parameters, consisting of $W = \text{np.zeros}((784, 10))$ and $b = \text{np.zeros}(10)$ (E2).
* The loss function used was cross-entropy, `loss = -np.mean(np.log(probs[np.arange(len(y_train)), y_train] + 1e-9))`: the negative log of the probability given to the correct label, averaged over 60,000 images (E2).
* The loss fell from $2.303$ ($\ln 10$, pure guessing) to $0.326$ (E2).
* Training accuracy was $91.0\%$, and the test accuracy on 10,000 unseen digits was $91.5\%$, with 854 errors (E3).
* Three specific mistakes noted were: Image #2044 (2 $\rightarrow$ 7 with 99.6% confidence), Image #565 (4 $\rightarrow$ 9 with 83% confidence), and Image #340 (5 $\rightarrow$ 3 with 79% confidence) (E4).
* A common thread in mistakes is that the distinguishing feature is one small region of the stroke, which the model cannot look at because it sums all 784 pixels at once (E4).

## Related notes

- [[Translation Sensitivity]] — the shift experiment that exposed the model's main limitation
- [[Learning Rate Choices]] — trained with a learning rate of 0.5
- [[Loss vs Real Performance]] — loss fell to 0.326 yet the model still failed on shifted digits

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[MNIST From Scratch Log]] — section "Class 3 — MNIST from scratch, run log", lines 1-8
- E2: [[MNIST From Scratch Log]] — section "1. Where the model lives in the code", lines 9-18
- E3: [[MNIST From Scratch Log]] — section "2. Accuracy", lines 19-24
- E4: [[MNIST From Scratch Log]] — section "3. Three mistakes", lines 25-39
