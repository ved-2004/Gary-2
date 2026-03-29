# Simulation

This folder contains the interactive store layout editor and shopper simulation.

## What It Does

- Build or load a store layout in the UI.
- Assign products to shelves.
- Run up to 15 LLM shoppers at once using OpenAI.
- Spawn all shoppers immediately or stagger them with randomized startup delays.
- Save run output to `simulation/results.json`.

## Data Inputs

The simulation uses these files outside this folder:

- `../data/customer_profiles.csv`
- `../data/shopping_list.csv`
- `../.env`

`OPENAI_API_KEY` must be set in `../.env` or in your shell environment.

## Setup

From the repo root:

```bash
pip install -r requirements.txt
```

Make sure `../.env` contains:

```env
OPENAI_API_KEY=your_key_here
```

## Run

From the `simulation` folder:

```bash
python main.py
```

Useful flags:

```bash
python main.py --agent-count 15
python main.py --agent-count 15 --spawn-delay-window-seconds 10
python main.py --agent-count 10 --action-cooldown-seconds 2 --max-concurrency 10
python main.py --agent-count 15 --model gpt-5.4 --reasoning-effort none --seed 42
python main.py --model gpt-5.4 --reasoning-effort none
python main.py --max-iterations-per-agent 50
```

Available CLI options:

- `--agent-count`: number of LLM shoppers to spawn, `1-15`
- `--model`: OpenAI model name, default `gpt-5.4`
- `--reasoning-effort`: reasoning override, default `none`
- `--action-cooldown-seconds`: delay between decisions for each active shopper
- `--spawn-delay-window-seconds`: random startup delay window; `0` means spawn all immediately
- `--max-iterations-per-agent`: hard turn limit for each shopper, default `50`
- `--max-concurrency`: max simultaneous OpenAI requests
- `--seed`: optional seed for reproducible shopper selection and spawn jitter

## Basic Flow

1. Run `python main.py`.
2. Load or create a layout.
3. Add at least one `Entrance` shelf and one `Checkout` shelf.
4. Load products or load an existing layout JSON.
5. Switch to `Simulation`.
6. Watch shoppers move, grab items, and check out.
7. Review `simulation/results.json` after the run finishes.

## Notes

- Shopper prompts are stateless per turn. The simulation sends persona, goals, cart state, visible items, and allowed actions each time.
- Movement is not stored as a growing chat history.
- If an LLM response is invalid or an API call fails, that shopper skips the turn and retries on the next cooldown.
- Default behavior is `gpt-5.4` with `--reasoning-effort none`.
- `gpt-5-mini` uses fixed medium reasoning. If you switch to it, remove `--reasoning-effort`.
- Each shopper has a hard 50-iteration budget by default and will become more exit-focused as that limit gets close.
