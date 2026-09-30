# Class 3 — MNIST from scratch, run log

Notebook: `pepealonso95/mnist-from-scratch` (Colab badge link in the repo README).
Reproduced top to bottom with the notebook's own settings: 300 epochs, learning rate 0.5,
weights initialised to zero, no randomness — so the numbers below are exactly repeatable.

Published write-up (artifact): https://claude.ai/code/artifact/36e603a6-08c4-4ac1-bc44-baf5918b45e8

## 1. Where the model lives in the code

| Piece | Line |
|---|---|
| Weights | `W = np.zeros((784, 10))` and `b = np.zeros(10)` — 7,840 + 10 = **7,850 parameters** |
| Loss | `loss = -np.mean(np.log(probs[np.arange(len(y_train)), y_train] + 1e-9))` — cross-entropy: negative log of the probability given to the correct label, averaged over 60,000 images |
| Update step | `W -= learning_rate * (X_train.T @ grad)` and `b -= learning_rate * grad.sum(axis=0)` — subtract a small multiple of the gradient |

Loss falls 2.303 (= ln 10, pure guessing) → 0.326.

## 2. Accuracy

- Train: **91.0%**
- Test (10,000 unseen digits): **91.5%** — 854 wrong
- The 0.5 pt gap is the good case: it learned a pattern rather than memorising.

## 3. Three mistakes

| Image | True → said | Confidence | Why it's hard |
|---|---|---|---|
| #2044 | 2 → 7 | 99.6% | Written flat — long horizontal top bar, one straight diagonal, no bottom-left curl. Pixel for pixel it is a 7 with a foot. A *confident* error. |
| #565 | 4 → 9 | 83% | The two top strokes touch, closing the gap that is the only thing separating a 4 from a 9. |
| #340 | 5 → 3 | 79% | One flowing curve, no flat top bar; the ink lands where a 3's two bowls would be. |

Common thread: the distinguishing feature is one small region of the stroke, and the model
cannot look at a region — it sums all 784 pixels at once, so a few decisive pixels get
outvoted by the hundreds the two digits share.

Top confusions across the 854 errors: 9→4 (42), 2→8 (40), 5→3 (38), 4→9 (36), 7→9 (34), 5→8 (30).
Roughly symmetric, which points at genuine shape overlap rather than a systematic bug.

## 4. Shift experiment

| Shift | Accuracy |
|---|---|
| 0 px | 91.5% |
| 1 px | 85.6% |
| 2 px | 65.7% |
| 3 px | 43.3% |
| 4 px | 23.2% |
| 5 px | 11.5% (chance = 10%) |

The limitation: one weight per *pixel position*. The model never learned what a 3 looks
like — it learned which coordinates in a 28×28 box tend to be lit, given MNIST's centring.
Move the ink and every weight points at the wrong place. Drawing each column of `W` back
out as a 28×28 image shows blurry fixed stencils, which is the whole explanation.

This is the argument for convolutions (Class 4): learn small local patterns and look for
them anywhere in the image.

## Note on reproducing it

Colab is the intended route. Run locally/in a sandbox and the notebook's MNIST download
(`storage.googleapis.com`) may be blocked; the same data can be rebuilt from the
`mnielsen/neural-networks-and-deep-learning` mirror (`data/mnist.pkl.gz`, values are /256,
train = first 50k + validation 10k) into the `x_train/y_train/x_test/y_test` npz the
notebook expects. Numbers match the README exactly either way.
