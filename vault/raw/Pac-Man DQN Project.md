# Ms. Pac-Man DQN — Class 3

Training a Deep Q-Network to play Ms. Pac-Man with the class notebook, three chosen
hyperparameters, and the notebook's own before/after evaluation.

**Headline:** mean score over five evaluation games went from **492.0** (untrained network) to
**876.0** after 1,000 training games — a change of **+384.0**. The comparison is paired — the
same five seeds on the same maze, before and after — and all 5 of 5 seeds improved; a one-sided
sign test puts that at p ≈ 0.031, so this is evidence the trained agent is better on these five
starts. But the per-seed gains range from +70 to +810, so five games estimate the *size* of the
improvement (+384) poorly. The training log also says the gain came from scoring faster, not
from surviving longer.

## Run it yourself

1. Clone this repo. The notebook is `pacman_dqn.ipynb`, unchanged from
   [pepealonso95/pacman-dqn](https://github.com/pepealonso95/pacman-dqn) (commit `d1b9e9d`)
   except for the three settings in section 1 and the two deviations noted below.
2. Open it with a Python 3.11–3.13 kernel (local Jupyter/VS Code) or in
   [Colab](https://colab.research.google.com/github/pepealonso95/pacman-dqn/blob/main/pacman_dqn.ipynb).
   Keep `pacman_player.py` next to the notebook for local popup playback.
3. Run All. Setup installs its own packages and picks CUDA / MPS / CPU automatically.
4. Results land in a fresh `pacman_runs/<timestamp>/` folder plus a ZIP.
5. Optional: `python analysis/analyze_run.py` regenerates the post-run chart and statistics
   from `results/` (see [Extra analysis](#extra-analysis-added-after-the-run)).

## My three settings

| Setting | Value | Why |
|---|---|---|
| Exploration | `0.10` | Half the notebook's 0.20 default, still inside the usual 0.1–0.2 band. It stays fixed at 10% for all 1,000 games after the 1,000-decision random warm-up — there is no decay. A lower rate is defensible partly because the environment already injects randomness: `sticky_action_probability` is 0.25 ([`results/config.json`](results/config.json)), so on every emulator frame there is a 25% chance the previous joystick input repeats instead of the chosen one, even for a fully greedy policy. It also brings training closer to the 5% used in evaluation — a 5-point gap instead of 15. |
| Episodes | `1000` | Chosen from a measured 5-game timing probe on this laptop's CPU, which put 1,000 games at roughly one to one-and-a-half hours of compute — the largest budget that fitted one sitting. More games means more learning updates (updates ≈ (decisions − 1,000) ÷ 4), and 1,000 games also gives 40 intermediate checkpoints and GIFs, one every 25 games. |
| Learning rate | `0.0002` | Doubled from the 0.0001 reference because the scarce resource was learning updates, not environment steps, and kept well short of 1e-3 given a 5,000-transition replay. |

The three settings were chosen in discussion with an AI assistant (Claude Code), which measured
throughput and laid out the trade-offs; the kickoff prompt and submission checklist used for that
are in [`process/`](process).

**Deviations from the stock notebook.**
- `SHOW_POPUPS = False` (the cell after section 2), because the notebook ran in the background
  with no desktop to show the Tk popup. Inline GIFs are unaffected.
- Executed with `jupyter nbconvert --to notebook --execute --inplace` instead of the Run All
  button. Same cells, same order, outputs kept in the committed notebook.

Nothing else in the notebook changed. The evaluation block is untouched: seeds
`[101, 202, 303, 404, 505]`, 5% evaluation exploration, 3,000-decision cap, `SEED = 42`
(confirmed in [`results/config.json`](results/config.json)).

**Also disclosed:** before choosing the settings, a 5-game timing probe ran on a separate copy of
the notebook (default exploration and learning rate) purely to measure speed. Its outputs are not
used anywhere in this write-up and are not in the repo. There was no other run.

## Prediction, then observation

**Before seeing any output of the run I expected** — written while training was at game 38 of
1,000, and committed on its own in [`PREDICTION.md`](PREDICTION.md) (commit `20db02b`):

> I expect a modest improvement in mean score, coming mainly from surviving longer — fewer
> immediate deaths, more pellets collected incidentally — rather than from anything resembling
> ghost avoidance. I expect loss to fall early and then drift upward as Q-values grow,
> decoupling from score. I expect the 25-game rolling mean to improve fastest in the first few
> hundred episodes and then flatten, because the 5,000-transition replay holds only about eight
> games, so the network keeps relearning from a narrow, recent slice of its own play. I expect
> decisions per game to rise off ~650 but not to approach the 3,000 cap; cap hits should stay
> rare. And I expect the five-game spread to be wide enough that the before/after means may
> overlap, so improvement should be judged on the per-game scores and on decisions-per-game,
> not on the mean alone.

**What actually happened**, claim by claim:

| Predicted | Observed | Verdict |
|---|---|---|
| Modest improvement, mainly from surviving longer | Evaluation mean 492.0 → 876.0. But training games did **not** get longer: 566.9 decisions per game in games 1–100, 578.1 in games 901–1000. Points per decision rose instead, 1.073 → 1.227. | Improvement: yes. Mechanism: **wrong** |
| Loss falls early, then drifts up as Q-values grow, decoupled from score | Loss never fell. The 100-game mean rose from 0.064 to a peak of 0.138 around game 397, then settled near 0.11. It did decouple from score: loss more than doubled through games 1–400 (0.0639 → 0.1372 by block) while the block mean score rose only from 608.3 to 699.7, and loss dropped in games 401–500 while score peaked. | Rise and decoupling: yes. Early fall: **wrong** |
| 25-game rolling mean improves fastest early, then flattens | 598.8 at game 25 → peak 1,037.2 at game 460 → 662.8 at game 1,000. The last 200 games trend −39.0 points per 100 games (95% CI −130.8 to +52.8): flat. The rise was slow and noisy rather than fast. | Flattening: yes. "Fastest early": **not really** |
| Decisions per game rise but stay far from the cap; cap hits rare | Zero of 1,000 training games hit the cap; the longest was 1,349 decisions. But there was no rise. | Cap: yes. Rise: **wrong** |
| Five-game spreads overlap, so judge per-game scores | Read unpaired, the ranges overlap (before 320–800, after 520–1,130). But the design is paired, and seed by seed all 5 of 5 improved (one-sided sign test p ≈ 0.031). The spread still limits the size estimate: per-seed gains run from +70 to +810. | **Right** that the mean alone is the wrong read — and the paired comparison is clearer than I expected |

The disagreement worth the paragraph: I expected the agent to learn to **survive**, and it learned
to **score faster** instead. The reason is in the learning rule (see
[Reading this against the Class 3 material](#reading-this-against-the-class-3-material)).

## What actually ran

| | |
|---|---|
| Status | `completed` (from `training_summary.json`) |
| Episodes requested / completed | 1000 / 1000 |
| Total decisions | 596,589 |
| Learning updates | 148,898 |
| Elapsed | 12:48 (46,108 s) — **includes about 11.5 h with the laptop asleep**; roughly 1:16 of actual training (see below) |
| Hardware | `cpu`, Windows-11-10.0.26200-SP0, Python 3.13.14 (CPU: Intel Core Ultra 7 258V, 4 torch threads) |
| Key package versions | torch 2.14.0, gymnasium 1.3.0, ale-py 0.11.2 |

The laptop went to sleep (Windows Modern Standby) during the run. The process
simply paused; no decisions or updates happened while asleep, so learning is unaffected — but
the notebook's clock kept counting. `training.csv` shows the three gaps: 71.6 min before game
284, 63.7 min before game 444 and 557.4 min before game 445 (11.54 h in total). Summing only the
normal-length games gives about 75.8 minutes of awake training time. Those two figures are
calculated from `training.csv` by [`analysis/analyze_run.py`](analysis/analyze_run.py), not
recorded by the notebook; the CPU model and thread count come from Windows and the notebook code,
not from `config.json`.

## Evaluation: all five games, before and after

Same five seeds (101, 202, 303, 404, 505), 5% exploration, 3,000-decision cap, before and
after. The baseline is an **untrained network**, not a random-action agent. Scores are raw game
points; training rewards are clipped to [−1, +1].

| Game (seed) | Before (untrained) | After (1,000 episodes) | Change | Decisions before → after |
|---|---|---|---|---|
| 1 (101) | 350 | 520 | +170 | 560 → 534 |
| 2 (202) | 500 | 990 | +490 | 597 → 659 |
| 3 (303) | 320 | 1130 | +810 | 614 → 916 |
| 4 (404) | 800 | 870 | +70 | 640 → 708 |
| 5 (505) | 490 | 870 | +380 | 534 → 744 |
| **Mean** | **492.0** | **876.0** | **+384.0** | 589.0 → 712.2 |

Full data: [`results/comparison.json`](results/comparison.json).
Time-limited games before / after: 0 / 0.

Note that the evaluation games did run longer on average, unlike the training games. Evaluation
plays with half the random moves (5% vs 10%), which may explain some of that, but four of the
five games got longer and one got shorter, which is too few to settle it.

## Training curves

![Training dashboard](results/training_dashboard.png)

- **Raw training score (left):** each game is very noisy (the standard deviation within each
  100-game block is 323.4 to 534.1 points). The 25-game average climbs slowly to its highest point
  around game 460, then moves up and down for the rest of the run without a clear direction.
- **Mean update loss (middle):** rises for the first ~400 games, then settles near 0.11. It does
  not track the score panel.
- **Training exploration (right):** 100% random for the warm-up, then flat at 10% for every
  game — no decay, by design.

## Extra analysis (added after the run)

The dashboard's 25-game line is too jumpy to answer "is it still improving?", so this chart uses
100-game windows. It is **not produced by the notebook**: it was made after the run by
[`analysis/analyze_run.py`](analysis/analyze_run.py) from the committed `results/training.csv`,
which also writes every derived number in this README to
[`results/derived_stats.json`](results/derived_stats.json).

![Plateau curves](results/plateau_curves.png)

| Games | Mean score | Mean decisions | Longest game | Time-limited | Points per decision | Mean loss |
|---|---|---|---|---|---|---|
| 1–100 | 608.3 | 566.9 | 1,202 | 0 | 1.073 | 0.0639 |
| 101–200 | 683.6 | 591.3 | 1,051 | 0 | 1.156 | 0.1093 |
| 201–300 | 650.9 | 590.6 | 1,160 | 0 | 1.102 | 0.1303 |
| 301–400 | 699.7 | 591.7 | 1,164 | 0 | 1.182 | 0.1372 |
| 401–500 | 812.2 | 615.8 | 1,288 | 0 | 1.319 | 0.1168 |
| 501–600 | 759.0 | 623.2 | 1,184 | 0 | 1.218 | 0.1165 |
| 601–700 | 741.8 | 586.2 | 1,040 | 0 | 1.265 | 0.1233 |
| 701–800 | 730.8 | 608.4 | 1,349 | 0 | 1.201 | 0.1117 |
| 801–900 | 736.3 | 613.8 | 1,154 | 0 | 1.200 | 0.1131 |
| 901–1000 | 709.2 | 578.1 | 1,131 | 0 | 1.227 | 0.1121 |

**Was the score still climbing at game 1,000?** No. The 100-game mean rose from 608.3 to 812.2
by game 500, then stayed between 702.0 and 840.0 and ended at 709.2. Its approximate 95% band
(±73.9 at game 1,000) overlaps across the whole second half. This is a **plateau, not
convergence**: the notebook's one-game check on seed 101 every 25 games still swung from 90 to
1,360 points after game 500 ([`results/demo_scores.json`](results/demo_scores.json)), so the
policy kept changing — it just stopped getting better on average.

**Did games get longer?** No. Mean decisions per game stayed between 566.9 and 623.2 in every
block, only 22 of 1,000 games reached 1,000 decisions, and none came near the 3,000 cap. Longer
games do score more (correlation 0.746 between a game's score and its length), but the typical
game never got longer. What changed was points per decision, which peaked at 1.349 around game
525 and then settled near 1.2.

## Gameplay

The GIFs show only the first 20 seconds of game time at 4× speed; the scores in the tables cover
whole games. All intermediate GIFs, every 25 games, are in [`results/demos/`](results/demos).
GitHub's notebook viewer does not display the notebook's inline GIF outputs (it shows
`<IPython.core.display.Image object>` in their place); they play inline when the notebook is
opened in Jupyter or VS Code, and the same files are embedded below.

**Untrained baseline** (seed 101, full game 350 points)

![Untrained](results/demos/episode_0000.gif)

It wanders with no visible purpose: the on-screen score sits at 320 for a long stretch of the
second half of the clip, and it loses a life just before the clip ends.

**After 500 episodes** (same seed 101, notebook's one-game check: 510 points)

![After 500 episodes](results/demos/episode_0500.gif)

**After 1,000 episodes** (same seed 101, one-game check: 520 points)

![After 1,000 episodes](results/demos/episode_1000.gif)

Through the clip their on-screen scores stay close to the untrained agent's, and both lose a life
*earlier* in the clip than the untrained agent did — at 1,000 episodes it runs straight into the
cyan ghost. Neither shows any sign of steering away from ghosts. On this one seed and this short
excerpt, trained play looks much like untrained play; the gains show up over whole games and
across seeds, not here.

**Best trained game** (best of the five evaluation games — seed 303, 1,130 points — first 20
seconds at 4× speed)

![Best trained](results/demos/final_best.gif)

It eats a power pellet about two-thirds of the way through the clip. For most of the time the
ghosts are blue the score does not move, and then jumps by 200 at the very end of the clip —
consistent with catching one blue ghost. One clip can't tell whether that was pursuit or luck;
the flat score while ghosts were edible suggests it isn't hunting them.

## What the agent observes, does, and is rewarded for

- **Observation:** four consecutive game screens, each reduced to 84×84 grayscale and stacked.
  One frame shows where everything is; four frames also show which way it's moving.
- **Actions:** the joystick moves Ms. Pac-Man can make (9 in this environment: no-op, the four
  directions and the four diagonals). The network outputs an estimated future reward for each
  one and normally picks the highest.
- **Reward:** the game's own points — pellets, power pellets, ghosts, fruit. During training the
  reward per step is clipped to [−1, +1] so a single big score can't dominate an update; the
  scores reported above are unclipped game points.
- **Learning:** the network is nudged toward `reward + 0.99 × (best value of the next screen)`,
  with a slower-moving copy of the network supplying that target. One decision advances four
  emulator frames; one update happens every four decisions after 1,000 warm-up decisions.

## Reading this against the Class 3 material

- **The agent learned the policy its rewards describe, not the one I had in mind.** With
  clipping, a pellet, a power pellet and a ghost are all worth the same +1 to the learner, and
  losing a life is worth nothing: `terminal_on_life_loss` is `false`, so after a death the target
  still includes the value of the next screen. With a 0.99 discount, rewards more than a few
  hundred decisions away barely count. So the reward signal pays for collecting things soon and
  hardly charges for dying. That is exactly the pattern in the log: points per decision up, game
  length flat.
- **Loss is not the metric that matters.** The middle panel measures prediction error against a
  target that moves as the network's own estimates grow, not play quality. Here loss rose while
  score improved slightly, and fell while score peaked — the two moved independently, so a falling
  (or rising) loss curve would have told me nothing about play.
- **Evaluation is a decision, not a number.** Five games at 5% exploration with fixed seeds is
  a small comparison. Because it is paired, the direction is supported — 5 of 5 seeds improved,
  one-sided sign test p ≈ 0.031 — but the magnitude is not: per-seed gains of +70 to +810 mean
  the +384 average could be well off. Five seeds on one maze are not a random sample of anything,
  so the result is about these starts, not Ms. Pac-Man in general. And evaluation plays with less
  randomness than training did, so evaluation (876.0) and training (709.2 in the last 100 games)
  are measuring different things.
- **"Held-out" is the wrong word for this evaluation.** The notebook seeds training game *n*
  with `42 + n`, so 5 of the 1,000 training games (0.5%) — games 59, 160, 261, 362 and 463 — used
  the evaluation seeds. That overlap is small, and those games did not replay the evaluation
  games anyway: the seed fixes only the starting state, while sticky actions and random
  exploration make every trajectory diverge. The real limit is that every game, in training and
  evaluation, is the same first maze, so nothing here tests generalization to an unseen level.
- **The data is the product.** Replay holds 5,000 decisions — fewer than ten games at this run's
  roughly 600 decisions per game — sampled in batches of 32, so the network only ever learns from
  its own most recent play.

## One limitation I observed

**The agent never learned to survive.** Mean game length in training was 566.9 decisions in the
first 100 games and 578.1 in the last 100, and none of the 1,000 games reached the time limit
([`results/training.csv`](results/training.csv)). The GIF after 1,000 episodes shows it
losing a life by running straight into a ghost inside the first 20 seconds, and the same one-game
check on seed 101 scored anywhere from 90 to 1,360 points after game 500. Whatever it learned,
it did not include getting out of a ghost's way, and its play on the same starting position was
still unstable at the end.

## Next experiment

Change **`REPLAY_CAPACITY`** from `5000` to `25000`, holding exploration 0.10, learning rate
0.0002 and 1,000 episodes fixed, because the plateau from about game 500 and the unstable
one-game checks fit a network that only ever learns from its last few games. At about 600
decisions per game, 25,000 decisions is roughly 40 games of memory. By the notebook's own formula
that is about 841 MiB of pixels, well within this laptop's 31.5 GB.

This changes one of the notebook's fixed settings, so that run would be declared as a deliberate
change and its evaluation mean would not be comparable on the class leaderboard. It will also be
slower per update, since each batch is sampled from a copy of the whole replay memory. **If the
100-game mean and points per decision keep rising past game 500 and the seed-101 checks swing
less, the narrow replay was holding it back. If it plateaus at a similar level around the same
point, the limit is elsewhere** — most likely the reward signal described above, which a bigger
memory does not change.

The experiment I would actually want is **ending the episode on life loss**, so the agent is
charged for dying and the reward-structure explanation is tested directly. It isn't the proposal
because it isn't a setting: `make_env()` builds the evaluation environment as well as the
training one, so flipping `terminal_on_life_loss` would change what is measured (evaluation games
would stop at the first death) as well as what is learned. Doing it properly needs separate
training and evaluation environments — a code change to the notebook, not a hyperparameter.

## Evidence and files

| | |
|---|---|
| Executed notebook (outputs intact) | [`pacman_dqn.ipynb`](pacman_dqn.ipynb) |
| Prediction, committed before any output was seen | [`PREDICTION.md`](PREDICTION.md) |
| Settings, hardware, package versions | [`results/config.json`](results/config.json) |
| Per-episode training log | [`results/training.csv`](results/training.csv) |
| Run summary | [`results/training_summary.json`](results/training_summary.json) |
| Before/after scores | [`results/comparison.json`](results/comparison.json) |
| Untrained scores alone | [`results/baseline.json`](results/baseline.json) |
| One-game check every 25 games | [`results/demo_scores.json`](results/demo_scores.json) |
| Training dashboard | [`results/training_dashboard.png`](results/training_dashboard.png) |
| GIFs (untrained, every 25 games, best trained) | [`results/demos/`](results/demos) |
| Post-run chart and derived statistics | [`results/plateau_curves.png`](results/plateau_curves.png), [`results/derived_stats.json`](results/derived_stats.json), made by [`analysis/analyze_run.py`](analysis/analyze_run.py) |

Model checkpoints (`untrained.pt`, `episode_*.pt`, `trained.pt`) are kept in the local run ZIP
(`pacman_runs/20260914_211025_163335.zip`), not in this repo, to keep it small.
