# CONTENT-API: how to write a content module for the workshop deck

You write one Python module (`content_<x>.py`) that adds slides to a shared `Deck`. A separate script assembles all
modules into one PowerPoint file. Read this file, then `content_open.py` (the style exemplar), then `showcase.py`
(one sample call per layout). Everything is in `<workshop>\01-slides\`.

## 1. Module contract

```python
from __future__ import annotations
from deck_lib import Deck
from facts import F, n, pct, d2, d3      # numbers come from here, never typed by hand

def build(d: Deck) -> None:
    d.cards("P2.1", "Headline as a full sentence", [...], notes="...", minutes=3)
```

* One file, one `build(d)` function, slides added **in plan order**. Put long speaker notes in triple-quoted strings.
* Slide ids are exactly the ids in `slide-plan.md` (`P2.0`, `P2.1`, ...). Do not renumber, skip or add ids. If the plan
  needs another slide, report it instead of inventing an id.
* Do **not** edit `deck_core.py`, `deck_lib.py`, `deck_widgets.py`, `deck_theme.py`, `facts.py`, other modules, the
  plan, or the demo folders. If you need a layout change, build the visual yourself with `d.custom(...)` (section 4) and
  list the request in your report. Put helper functions inside your own module.
* The plan row (id, headline, layout, visual, evidence, note gist) is the brief. Keep the plan's headline unless it
  does not fit on two lines. Keep the plan's layout unless a better native layout exists (say why in the report).

## 2. Voice and slide-writing rules

Audience: data scientists and data engineers, comfortable with Python, SQL and Spark, mostly new to the Azure ML and
Fabric ML specifics. Many are French speakers, so use plain international English and avoid idioms.

**Slides**
* Natural, simple narrative. The headline is a full-sentence takeaway ("MLflow tracks the same four things in both
  platforms"), not a topic ("MLflow"). At most 2 lines; the title shrinks from 30 to 24 pt automatically. Prefer **one
  line (about 60 characters)** on diagram-heavy slides (`arch`, `flow`, `custom`), because a two-line title takes
  space from the picture.
* One idea per slide. At most about 70 words of body text outside tables and code. Card titles: 1 to 4 words. Card
  bodies: at most 20 words. Prefer 3 to 5 items. A picture (arch, flow, chart, table) beats a bullet list. A row of 5
  cards works only with very short bodies (see O3); use 3 to 4 cards otherwise.
* Vary the layout: never more than two slides in a row with the same layout.
* US English spelling. No emojis, no exotic symbols, no em dashes. Use en dashes only for ranges ("09:00 \u2013 09:20").
  No customer names anywhere (the deck is vendor-neutral and the story is "Contoso Fleet").
* **Numbers come from `facts.F`.** Format counts with `n(x)` (12,345). Say "about" for model metrics and scores,
  because they vary by about 0.02 across library versions; counts are exact.
* Flag **previews and deprecations on the slide** (an amber card, an amber pill, or the `source=` line), and again
  in the notes. Anything you cannot verify from the fact sheets or the builders' files is marked `VERIFY` in the notes
  and listed in your `content\VERIFY-<module>.md`.
* Use `source="Microsoft Learn: <topic>, verified 2026-10-18"` (one short line, at most 100 characters) on slides that
  state versions, limits, preview status or dates. Put the full URLs in the notes under `SOURCE:`.
* Code on slides is **copied from the demo folders** (adapt only to shorten). At most 10 lines and 55 characters per
  line next to a side column; full width allows about 14 lines and 90 characters. Name the file with `file=`.
  Highlight languages: `python`, `sql`, `bash`, `yaml`, `json`, `bicep` (comments only), `js`.
* Never put secrets, tenant ids or real subscription ids on a slide. Use `<placeholder>` names.
* Static slides only: no animations, no videos. Build-ups are separate slides only if the plan says so.

**Speaker notes** (the presenter reads these; they also feed the presenter guide)
* Natural spoken English, first person, conversational, short sentences. 120 to 250 words for a content slide, 150 to
  300 for a demo cue slide, 40 to 90 for a quick transition slide. Never fewer than 40 words (the build flags it).
* Open with what to say. Then use these labelled lines, each on its own line, only when useful:
  `DEMO:` what to click or run. `ASK:` a question for the room. `WATCH OUT:` a known trap. `IF SHORT ON TIME:` what to
  cut. `SOURCE:` URLs. `VERIFY:` facts to re-check in the tenant before Friday. `TRANSITION:` the sentence that leads
  to the next slide.
* Define every acronym the first time it appears in a part. Explain, do not just list.
* Do not paste long code or tables in the notes: refer to the file in the demo folder.

## 3. Minutes and the core / optional convention

Every slide gets `minutes=` (float) and, if it can be skipped in the half-day version, `core=False`. A demo cue slide
carries the whole demo's minutes (there are no separate "during the demo" slides).

| Part | Full-day budget (core + optional) | Core target (half-day cut) |
|------|----------------------------------:|---------------------------:|
| O  Opening        | 20  | 16 |
| P1 Fabric vs AML  | 90  | 45 |
| P2 MLOps          | 75  | 30 |
| P3 End-to-end     | 115 | 60 (the Fabric path plus the shared slides) |
| P4 Foundry/agent  | 75  | 45 |
| C  Wrap-up        | 15  | 10 |
| A  Appendix       | 0 (reference, never presented unless asked) | 0 |

`python devbuild.py <module>` prints `core X + optional Y = Z (agenda N)`. Get Z within 2 minutes of N, and core within
5 minutes of the target. Appendix slides use `minutes=0.5, core=False`.

**Exceptions for Part 3 and Part 4 (these override the "cue slide carries the whole demo" sentence above).**

* **P3 is written by two modules.** `content_p3` = P3.0 to P3.14 (intro plus the Fabric path): **55 min (+-2)**, every slide
  `core` except at most two. `content_p3b` = P3.15 to P3.25: **60 min (+-2)** = Azure ML P3.15 to P3.20 (**45 min**) plus bridge
  and wrap-up P3.21 to P3.25 (**15 min**); the Azure ML slides are `core=False` (the half-day cut is Fabric-only); only
  P3.23 (3 min) and P3.25 (2 min) are `core`, so the part's core is about 60. `devbuild.py` prints the module targets.
* In P3 the walk-through slides (P3.5 to P3.14 and P3.16 to P3.20) are shown while the presenter does the live step they
  frame: each carries the minutes of its step (explanation plus live click-through). The two cue slides P3.4 and P3.15 only
  carry 3 and 4 min (what is pre-run, the order of the steps, what to say if it breaks). The run-of-show files of the demo
  folders add up to a few more live minutes than this budget; compress, and say in the notes (`IF SHORT ON TIME:`) what to cut.
* **P4**: the three demo cue slides carry their live minutes: Demo 3a (P4.7) **15**, Demo 3b (P4.8) **20**, Demo 3c (P4.10)
  **15** = 50 live minutes, all `core`. The 15 other slides share the remaining **25** minutes and are `core=False`
  except where the half-day story truly needs them (keep the core within 45 to 55). The notes of each cue say what the
  extended version adds (the demo folder's run-of-show has a longer variant).

## 4. Layout vocabulary

All methods are on `Deck` and accept `notes, minutes, core, takeaway, source, eyebrow` in addition to what is shown.
`takeaway="..."` draws a blue bar at the bottom (one sentence, at most 110 characters): use it on about a third of the
content slides, not all of them. Inline markup in any text: `**bold**` and `` `code` ``.

| Method | Use it for | Arguments (besides `sid, title`) |
|--------|-----------|-----------------------------------|
| `title_slide` | the first slide only | already used by O1 |
| `section` | part divider; also chapter and appendix dividers | `part_no` (digit, or an icon name), `title, subtitle, goals (<=3), when=(time, length), label=None, track_part=None, goals_label=...` |
| `agenda` | timetable | used by O2 |
| `bullets` | 3 to 5 rows of "lead + one line", optional icon, optional picture on the right | `items` = str or `(lead, text, icon)` or dict; `visual=callable(s, x, y, w, h)`, `visual_w=4.9` |
| `cards` | 2 to 6 equal cards, optionally numbered | `items` = dict(title, body, icon, tone); `cols`, `icon_pos` = `top`/`inline`, `numbered`, `max_h`, `min_h`, `title_size`, `body_size`; `body` is a str or a list of str / paragraph dicts |
| `compare` | two panels side by side (4 to 5 short items each) | `left`, `right` = dict(title, sub, icon, tone, items=[str]) |
| `table_slide` | native table, up to 9 rows x 4 columns | `header`, `rows`, `col_w` (relative), `size`, `side` (cards on the right), `tbl=dict(bold_first, zebra, mono_cols, row_tones, align)` |
| `stats` | 2 to 4 big numbers | `items` = dict(value, label, sub, tone), `cols` |
| `callout` | one big statement and up to 3 supporting cards | `statement`, `support=[dict(icon, title, body, tone)]`, `tone`, `size` |
| `flow` | 3 to 6 steps left to right, optional return path (a loop) | `steps` = dict(title, body, icon, tone), `back=dict(label=...)`, `numbered` |
| `arch` | boxes and arrows on a grid (pipelines, architectures) | `nodes` = dict(id, label, sub, icon, col, row, cspan, rspan, tone, h), `edges` = (a, b[, label]) or dict(a, b, label, sa, sb, dash, color), `groups` = dict(label, c0, r0, c1, r1, tone) |
| `stairs` | levels or maturity (any n up to 5) | `steps` = dict(tag, title, body, tone) |
| `timeline` | dated events (3 to 5) | `events` = dict(when, title, body, tone) |
| `chart_slide` | native bar chart (horizontal) with side cards | `cats`, `series` = {name: [values]}, `fmt`, `chart=dict(highlight=index)`, `side` |
| `code_slide` | syntax-highlighted code (+ optional side cards) | `code`, `lang`, `file`, `hl` = 1-based lines to highlight, `side` |
| `demo` | live-demo cue card with a fallback | `steps` = [(text, minutes_label)] (3 to 6), `prebaked` = [str], `notice` = [str], `when`, `where` |
| `recap` | numbered takeaways and a question | `points` = dict(title, body, tone), `question` |
| `discuss` | 2 to 3 discussion prompts | `questions` = str or dict(title, body), `when` |
| `custom` | anything else, drawn with the helpers below | `draw(f)` where `f.s` is the slide and `f.x, f.y, f.w, f.h, f.r, f.b` is the body area in inches |

Layout facts: the slide is 13.333 x 7.5 in; the body area starts at y = 1.55 (one-line title) or 1.85 and ends at 6.78
(6.0 with a takeaway bar, 6.6 with a source line). Tones: `node, paper, azure, amber, success, solid, dark, amber_solid,
muted`. Colors: azure = default and platform, amber = caution / preview / gap, success = good outcome.

**Mappings for plan layouts that are not native:**
* `loop` (a cycle): `flow(..., back=dict(label="..."))`.
* `ladder`: `stairs`. Chapter divider (P1.8 and similar): `section(sid, "git-branch", title, subtitle, goals, when,
  label="CHAPTER", track_part=1)`. Appendix divider: `section("A0", "file-text", ..., label="APPENDIX",
  goals_label="WHAT IS INSIDE", track_part=None)`.
* A comparison with more than 5 rows: `table_slide`.
* A train / gap / valid / test time split, a hierarchy of MLflow objects, a swim-lane: build with `d.custom`.

**Drawing with `custom`** (import from `deck_core`): `text(s, x, y, w, h, [paras], size=, color=, font=, bold=,
align="l|c|r", anchor="t|m|b")`, `box(s, x, y, w, h, tone=, radius=, dash=, filled=)`, `card(s, x, y, w, h, title, body,
icon=, tone=)`, `pill(s, x, y, "Label", tone=)` (returns `(shape, width)`), `label(s, x, y, w, "txt")`, `arrow(s, x1, y1,
x2, y2, color=, dash=)`, `link(s, shape_a, shape_b, "r", "l")` (glued connector), `polyline(s, [(x, y), ...])`,
`add_icon(s, "name", x, y, size, color=)`, `num_badge(s, x, y, "1")`, `est_height(paras, width_in, size=)`, `text_w(str,
font, size, bold)`, constants `MX, CW, PAL, HEAD, BODY, MONO`. Paragraph dicts take `text, size, bold, italic, color,
font, bullet, indent, after, before, align`. Minimum font sizes: 14 pt for body text, 12 pt for captions and diagram
labels, 10.5 pt for edge labels only. Keep at least 0.15 in between shapes; connectors go behind labels.

```python
from deck_core import box, text

def draw(f):
    s = f.s
    x = f.x
    for name, tone in [("train", "azure"), ("gap", "muted"), ("valid", "amber"), ("test", "success")]:
        box(s, x, f.y + 1.0, 2.6, 0.9, tone=tone, name=f"split {name}")
        text(s, x, f.y + 1.0, 2.6, 0.9, [name], size=18, bold=True, align="c", anchor="m")
        x += 2.9
d.custom("P2.9", "Split by time, with a gap, never at random", draw, notes="...", minutes=3)
```

## 5. Icons

Three families, all used through the same call `add_icon(s, "name", x, y, size, color=)` or the `icon=` argument of the
layouts:

* **Generic concepts**: Lucide-style outline icons, six colors (`azure` default, `amber`, `success`, `ink`, `muted`,
  `white`). Examples: `database, workflow, git-branch, flask-conical, scale, shield-check, bot, rocket, repeat`.
* **Named Microsoft products**: official icons, one color, only for the product itself: `microsoft-fabric,
  azure-machine-learning, microsoft-foundry, lakehouse, notebook, data-pipeline, eventhouse, eventstream, data-agent,
  semantic-model, power-bi, experiment, ml-model, one-lake, azure-key-vault, azure-container-registry,
  application-insights, azure-monitor, log-analytics, microsoft-entra-id, github, azure-devops, visual-studio-code`.
* **Text tiles** for products without an official icon: `mlflow, spark, delta, scikit-learn, python, docker, git,
  databricks, sql, kql, yaml, bicep, oidc`.

The library is **still being generated** by another agent. Run `python icons.py` (all names, `+` ready and `-` not
yet generated), `python icons.py fabric model` (search) or `python icons.py --missing`. If a name you want is `-`,
keep it in your code, finish the rest, and re-run: the build prints `LINT ... missing icon` until the file exists.
Never invent a name that `icons.py` does not list, and never use emoji. **Final state must have no missing-icon
warnings.** Use icons to carry meaning (one per card or row), not as decoration.

## 6. Commands (run in `<workshop>\01-slides`, Windows PowerShell 5.1)

```powershell
python devbuild.py content_p2                                              # fast: build, lint, minutes report
powershell -NoProfile -ExecutionPolicy Bypass -File .\check.ps1 content_p2 # build + QA + render + contact sheets + text
python icons.py fabric                                                     # search icon names
```

`check.ps1` writes to `out\dev\<module>\`: `sheet_NN.png` (six slides per sheet, slide ids in the corner), `render\s###.png`
(one image per slide, use it to inspect details), `text.md` (all text and notes), `slide-index.md`, `qa.json`.
**View the sheets and every slide that looks tight**, with the `view` tool. PowerPoint renders them, so what you see is
what the presenter gets. The QA and render steps open PowerPoint through COM in a shared, mutex-protected way (other
authors queue behind you): run `check.ps1` one at a time, never call PowerPoint yourself, never close it, never touch
any other open presentation. Run it every few slides, not once at the end.

Done means: `devbuild` prints `clean: no lint warnings, no problems`; QA says `0 issue(s)`; you looked at every sheet;
no text is cut, overlapping or smaller than 12 pt; every slide has notes; `text.md` has no mojibake (strange
characters), no double spaces and no hand-typed counts that disagree with `facts.F`.

## 7. Facts and sources

* Scenario, names and numbers: `02-demo-data\scenario-contract.md` and `facts.F` (read `facts.py` for attribute names).
* Platform facts (verified 2026-10-18): `00-presenter-guide\fact-sheets\{fabric-ml,aml,fabric-de-rti,foundry-dataagent}.md`.
* The approved storyline and per-slide briefs: `slide-plan.md`.
* Demo folders (`03-...` to `06-...`) are being finished by other agents; read their README, run-of-show,
  `slide-facts.md` / `*-facts-for-slides.md` and code for the parts you cover, and quote them. They may still change a
  little: when a demo file and a fact sheet disagree, say so in your VERIFY file. If a file does not exist yet, rely on
  the contract and fact sheets and mark the point `VERIFY`.
* Shared names: lakehouse `lh_fleet`, experiment and model `fleet-failure-7d`, data agent `da_fleet_recon`, Foundry
  agent `fleet-recon-agent`, Azure ML workspace `mlw-fleet-dev`, compute `cpu-cluster`, environment `env-fleet-sklearn`,
  endpoints `fleet-risk-online` and `fleet-risk-batch`, Fabric workspaces `ws-fleet-dev|test|prod`, notebooks
  `nb_00` to `nb_11`, pipelines `pl_fleet_etl` and `pl_fleet_daily`.
* Do not search the web with a customer name. Public Microsoft Learn is fine for verification.

## 8. Report format (your final message, at most 250 words)

1. Slides written (count) and the `devbuild` minutes line.
2. Deviations from the plan (layout or headline changes, with the reason) and any plan slide you could not write.
3. Requests for framework changes, if any.
4. `VERIFY` items (also saved in `01-slides\content\VERIFY-<module>.md`, one line each: slide id, claim, why uncertain).
5. Confirmation: lint clean, QA 0 issues, sheets viewed.
