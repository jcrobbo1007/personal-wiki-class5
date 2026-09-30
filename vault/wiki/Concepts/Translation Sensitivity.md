---
title: Translation Sensitivity
topic: Concepts
source_ids: [mnist]
note_id: translation-sensitivity
generated_by: gemma4:e2b
generated_on: 2026-09-30
reviewed: true
---

# Translation Sensitivity

*Why the MNIST model failed when digits moved a few pixels, and the case for convolutions.* · Topic: Concepts · Back to [[index]]

## Summary
This page explains the results of a shift experiment on the MNIST model and identifies the cause of translation sensitivity. The experiment showed that shifting the input pixels drastically reduced accuracy, indicating the model learned pixel positions rather than actual shapes. The log presents this as the argument for convolutions, which learn small local patterns and look for them anywhere in the image.

## Key details
* The shift experiment showed accuracy dropping from 91.5% at 0 px shift to 23.2% at 4 px and 11.5% at 5 px, where chance is 10% (E2).
* The limitation of the model is that it has one weight per pixel position, meaning it learned which coordinates tend to be lit given MNIST's centering (E2).
* Moving the ink makes every weight point at the wrong place; drawing each column of $W$ back out as a 28×28 image shows blurry fixed stencils, which explains the failure (E2).
* The common thread in mistakes is that the distinguishing feature is one small region of the stroke, and the model sums all 784 pixels at once (E1).
* Top confusions across the 854 errors included 9→4 (42), 2→8 (40), 5→3 (38), 4→9 (36), 7→9 (34), and 5→8 (30) (E1).

## Related notes

- [[MNIST From Scratch]] — the model that was tested
- [[Embeddings and Attention]] — learned representations as the alternative to fixed per-pixel weights

## Sources

Excerpt labels (E1, E2, …) in the details above refer to:

- E1: [[MNIST From Scratch Log]] — section "3. Three mistakes", lines 25-39
- E2: [[MNIST From Scratch Log]] — section "4. Shift experiment", lines 40-58
