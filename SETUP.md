# SunnysApartment — animated, self-generating GitHub profile

One **stdlib-only** Python script pulls live stats from GitHub's GraphQL API and
renders `dark_mode.svg` + `light_mode.svg` itself. A daily Action reruns it and
commits the SVGs. Nothing third-party renders your profile at page-load time.

On top of the plain neofetch idea: your photo as an ASCII portrait, a type-in
boot animation, a live language bar, a live contribution heatmap, uptime from
your real GitHub join date, and an Arabic/RTL accent.

---

## The 7 files — all of them go in the repo

```
README.md                      the <picture> tag that swaps dark/light
update_profile.py              the generator (edit your details here)
dark_mode.svg                  placeholder; the Action overwrites it
light_mode.svg                 placeholder; the Action overwrites it
.github/workflows/update.yml   runs the generator daily
tools/make_portrait.py         optional: rebake the ASCII art from a new photo
SETUP.md                       this file
```

Only `update_profile.py` needs editing. `tools/make_portrait.py` is optional and
never runs in CI — the ASCII art is baked into `update_profile.py` as the `ART`
constant, which is what keeps the generator dependency-free.

---

## Setup

### 1. Create the repo
New **public** repo named exactly `SunnysApartment` — GitHub shows a "special
repository ✨" note when the name matches your username. Don't add a README.

```bash
cd ~/Downloads && unzip SunnysApartment-profile.zip && cd SunnysApartment
git init -b main
git add .
git commit -m "profile"
git remote add origin https://github.com/SunnysApartment/SunnysApartment.git
git push -u origin main
```

Push the **contents** — `README.md` must sit at the repo root, not nested in a
`SunnysApartment/` folder.

### 2. Let Actions write to the repo
**Settings → Actions → General → Workflow permissions → Read and write
permissions → Save.**

Do not skip this. The workflow declares `permissions: contents: write`, but that
only works if the repository default allows it. If this is left on read-only,
the run fails at `git push` with a 403.

### 3. Add `ACCESS_TOKEN` (needed for line-of-code counts)
The built-in `GITHUB_TOKEN` covers repos, stars, commits, followers, languages
and the heatmap. The LOC walk reads commit history across your repos and wants a
real PAT.

- GitHub → Settings → Developer settings → **Personal access tokens (classic)** →
  Generate new (classic) → scope **`repo`** (or `public_repo` for public-only).
- Profile repo → Settings → Secrets and variables → Actions → **New repository
  secret** → name `ACCESS_TOKEN`, paste the token.

Skip it and everything else still renders; LOC just stays at `—`.

### 4. Run it once
**Actions** tab → enable workflows if prompted → **Update profile** → *Run
workflow*. It commits fresh SVGs. Refresh your profile.

The first run can take several minutes: the LOC step pages through your commit
history across ~48 repos.

### 5. Set your real contact details
In `update_profile.py`, the `FIELDS` dict near the top:

```python
email="you@example.com",      # <- yours
linkedin="in/your-handle",    # <- yours
```

`host`, `role`, `ide`, `real`, `focus`, `os` are prefilled from your public
profile — adjust to taste. Commit; that push re-triggers the workflow.

---

## Before the first successful run

The shipped `dark_mode.svg` / `light_mode.svg` show `—` for every statistic and
"awaiting first sync" for uptime and languages. That is intentional: this render
is public the moment you push, so it must never display numbers that aren't
really yours. Real values appear after step 4.

---

## Customizing

- **Colours** — `PALETTES`. `art` is the portrait, `g1`/`g2` the name gradient,
  `hm` the 5-step heatmap ramp (currently your Orbit blues).
- **Portrait** — swap the photo and rebake, then paste the output between the
  `ART = r"""` triple quotes:
  ```bash
  pip install pillow
  python tools/make_portrait.py newphoto.jpg --width 44
  ```
  `--width` controls detail; `--contrast` / `--gamma` control how bold the face reads.
- **Arabic accent** — the `ARABIC` constant. Change it or set it to `""`.
- **Animation** — line stagger is `0.3 + i*0.06`s in `render()`; footer fades in at `1.9s`.
- **Test locally** — `python update_profile.py` (no token → the `—` fallback).
  Note that cairosvg and most rasterizers show the *pre-animation* frame; the
  motion only plays in a browser and on GitHub.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Run fails at `git push` (403) | Step 2 — workflow permissions |
| Stats all `—` after a green run | `ACCESS_TOKEN` missing or wrong scope |
| LOC is `—` but other stats work | Expected without `ACCESS_TOKEN` (step 3) |
| Broken image on profile | Workflow hasn't run yet — step 4 |
| Arabic text renders as boxes | Viewer lacks an Arabic font; set `ARABIC = ""` |
