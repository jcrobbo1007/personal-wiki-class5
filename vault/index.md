# Jack's AI Course Wiki

Personal notes from *From Zero to AI Agents* (Berkeley Haas, fall 2026), built from my own
project write-ups. Start with a project, follow its links into the concepts, and use
each note's **Sources** list to get back to the original text in `raw/`.

## Projects

One note per course project: what was built, the settings chosen and the headline result.

- [[Ms Pac-Man DQN]] — Class 3 reinforcement-learning run: settings, before/after scores and what the gain really was.
- [[Custom nanoGPT LLM]] — Class 4 tiny word-level language model: two corpus experiments, 48 fixed evals and the coverage-vs-competence finding.
- [[MNIST From Scratch]] — Class 3 single-layer digit classifier in NumPy: 91.5% test accuracy and a collapse under pixel shifts.

## Concepts

Ideas that recur across projects, each tied back to where it showed up.

- [[Deep Q-Networks]] — How the DQN in the Pac-Man project observes, acts, is rewarded and learns.
- [[Exploration vs Exploitation]] — The fixed 10% exploration choice in the Pac-Man run and its cost.
- [[Learning Rate Choices]] — The learning rates chosen in all three projects and the reasoning behind each.
- [[Evaluation and Small Samples]] — How each project was evaluated and how much a small eval set can prove.
- [[Loss vs Real Performance]] — Why a falling loss did not guarantee better behaviour in these projects.
- [[Embeddings and Attention]] — How the Class 4 model turned words into vectors and used earlier context.
- [[Translation Sensitivity]] — Why the MNIST model failed when digits moved a few pixels, and the case for convolutions.

## Original sources

Unchanged originals. Every wiki note cites these.

- [[Custom LLM Project]] — Custom nanoGPT LLM project README (Class 4)
- [[MNIST From Scratch Log]] — MNIST from scratch run log (Class 3)
- [[Pac-Man DQN Project]] — Ms. Pac-Man DQN project README (Class 3)
