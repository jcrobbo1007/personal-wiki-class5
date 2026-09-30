# Ask-mode evidence — What learning rate did I use for the MNIST model?

| | |
|---|---|
| Mode | ask (standalone, no chat history) |
| Execution | local |
| Model | `gemma4:e2b` |
| Internet reachable during run | False |
| Run at | 2026-09-30T10:32:26 |
| Model called | True |
| Response time | 21.88 s wall (1592 prompt tokens, 18 output tokens) |

## Retrieved passages

**[S1]** `vault/raw/MNIST From Scratch Log.md` — Class 3 — MNIST from scratch, run log > 1. Where the model lives in the code — lines 9-17 — score 8.45

> ## 1. Where the model lives in the code
>
> | Piece | Line |
> |---|---|
> | Weights | `W = np.zeros((784, 10))` and `b = np.zeros(10)` — 7,840 + 10 = **7,850 parameters** |
> | Loss | `loss = -np.mean(np.log(probs[np.arange(len(y_train)), y_train] + 1e-9))` — cross-entropy: negative log of the probability given to the correct label, averaged over 60,000 images |
> | Update step | `W -= learning_rate * (X_train.T @ grad)` and `b -= learning_rate * grad.sum(axis=0)` — subtract a small multiple of the gradient |
>
> Loss falls 2.303 (= ln 10, pure guessing) → 0.326.

**[S2]** `vault/raw/MNIST From Scratch Log.md` — Class 3 — MNIST from scratch, run log — lines 1-7 — score 8.28

> # Class 3 — MNIST from scratch, run log
>
> Notebook: `pepealonso95/mnist-from-scratch` (Colab badge link in the repo README).
> Reproduced top to bottom with the notebook's own settings: 300 epochs, learning rate 0.5,
> weights initialised to zero, no randomness — so the numbers below are exactly repeatable.
>
> Published write-up (artifact): https://claude.ai/code/artifact/36e603a6-08c4-4ac1-bc44-baf5918b45e8

**[S3]** `vault/raw/MNIST From Scratch Log.md` — Class 3 — MNIST from scratch, run log > 4. Shift experiment — lines 40-57 — score 6.42

> ## 4. Shift experiment
>
> | Shift | Accuracy |
> |---|---|
> | 0 px | 91.5% |
> | 1 px | 85.6% |
> | 2 px | 65.7% |
> | 3 px | 43.3% |
> | 4 px | 23.2% |
> | 5 px | 11.5% (chance = 10%) |
>
> The limitation: one weight per *pixel position*. The model never learned what a 3 looks
> like — it learned which coordinates in a 28×28 box tend to be lit, given MNIST's centring.
> Move the ink and every weight points at the wrong place. Drawing each column of `W` back
> out as a 28×28 image shows blurry fixed stencils, which is the whole explanation.
>
> This is the argument for convolutions (Class 4): learn small local patterns and look for
> them anywhere in the image.

**[S4]** `vault/raw/Custom LLM Project.md` — Custom LLM — Class 4 (nanoGPT, word tokens) > Evidence > One real gradient and weight update — lines 208-211 — score 4.44

> The learning rate here is **1e-05, not the 0.001 I chose**, because the notebook warms up
> over the first `min(100, steps/10)` = 100 steps: at step 0 the multiplier is 1/100. This is
> the concrete reason LEARNING_RATE is a peak and not a constant. Repeat this arithmetic
> 111,872 times per step, 3,000 times, and the loss falls from 4.93 to 0.68.

**[S5]** `vault/raw/Custom LLM Project.md` — Custom LLM — Class 4 (nanoGPT, word tokens) > Evidence > One real gradient and weight update — lines 190-210 — score 4.24

> ### One real gradient and weight update
>
> From `first_update` in [inspection.json](results/exp1-starter/inspection.json), captured at
> **step 0**, coordinate 0 of `customer`'s embedding:
>
> ```
> before   = -0.057591915130615234
> gradient =  0.0006925859488546848
> lr       =  0.00001            (1e-05, not 0.001 — see below)
> after    = -0.05760190635919571
> ```
>
> Change = −0.000009991. The gradient says "increasing this number would increase the loss",
> so the optimiser moves it *down*. The size is `lr × 1` ≈ 1e-05 rather than
> `lr × gradient` ≈ 7e-09, because **AdamW normalises by the running magnitude of the
> gradient** — at the very first step the ratio of gradient to its own RMS is ≈ 1, so the step
> is essentially the full learning rate in whichever direction reduces loss.
>
> The learning rate here is **1e-05, not the 0.001 I chose**, because the notebook warms up
> over the first `min(100, …


## Gemma's answer (verbatim)

> The learning rate used for the MNIST model was 0.5 [S2].

## Citations

- [S2] `vault/raw/MNIST From Scratch Log.md` — Class 3 — MNIST from scratch, run log — lines 1-7

## Automatic checks

- Citation check: **cited**

## Assessment

_To be written after reading the cited passages against the answer._
