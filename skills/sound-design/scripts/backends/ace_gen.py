"""ACE-Step 1.5 driver (free, local, MIT). Runs INSIDE the ACE-Step checkout's own environment:

  uv run --project <ACE_DIR> python ace_gen.py <request.json>

music.py writes the request and calls this; you normally don't run it by hand.
request: {"ace_dir": "...", "out_dir": "...", "name": "score", "n": 2, "seed": 1000,
          "task": "text2music" | "repaint", "caption": "...", "duration": 43, "bpm": 120, "keyscale": "D major",
          "timesignature": "4", "lm": "auto" | "none" | "acestep-5Hz-lm-0.6B" | "acestep-5Hz-lm-1.7B", "offload": bool,
          "dit": "acestep-v15-turbo", "steps": 8, "src_audio": "...", "repaint_start": 24, "repaint_end": 29}
Prints one JSON line per output: {"path": ..., "seed": ...}
"""
import json
import os
import sys
import time

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
if sys.platform == "darwin":
    os.environ.setdefault("ACESTEP_LM_BACKEND", "mlx")
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")


def ram() -> float:
    try:
        import psutil
        return psutil.virtual_memory().total / 2 ** 30
    except Exception:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2 ** 30


def main():
    req = json.load(open(sys.argv[1]))
    ace = req["ace_dir"]
    sys.path.insert(0, ace)
    from acestep.api.model_download import ensure_model_downloaded
    from acestep.api.server_utils import get_model_name
    from acestep.handler import AceStepHandler
    from acestep.inference import GenerationConfig, GenerationParams, generate_music
    from acestep.llm_inference import LLMHandler

    ckpt = os.path.join(ace, "checkpoints")
    os.makedirs(ckpt, exist_ok=True)
    dit_name = req.get("dit", "acestep-v15-turbo")
    t0 = time.time()
    ensure_model_downloaded(get_model_name(dit_name), ckpt)
    ensure_model_downloaded("vae", ckpt)
    lm = req.get("lm", "auto")
    ram_gb = ram()
    if lm == "auto":  # DiT + 0.6B planner peaked at ~20 GB on Apple Silicon: only plan when there's room
        lm = "acestep-5Hz-lm-0.6B" if ram_gb >= 24 else "none"
    offload = bool(req.get("offload", lm != "none" and ram_gb < 24))
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(project_root=ace, config_path=dit_name, device="auto", offload_to_cpu=offload)
    if not ok:
        sys.exit(f"ACE-Step DiT failed to load: {msg}")
    llm = LLMHandler()
    if lm and lm != "none":
        ensure_model_downloaded(get_model_name(lm), ckpt)
        backend = "mlx" if sys.platform == "darwin" else os.environ.get("ACESTEP_LM_BACKEND", "pt")
        msg, ok = llm.initialize(checkpoint_dir=ckpt, lm_model_path=lm, backend=backend, device="auto",
                                 offload_to_cpu=offload)
        if not ok:
            print(f"warning: LM failed to load ({msg}); continuing DiT-only", file=sys.stderr)
    print(f"[ace] models ready in {time.time() - t0:.0f}s (lm={lm}, offload={offload}, ram={ram_gb:.0f} GB)",
          file=sys.stderr)

    task = req.get("task", "text2music")
    kw = dict(task_type=task, caption=req["caption"], instrumental=True, lyrics="[Instrumental]",
              duration=float(req.get("duration", 30)), inference_steps=int(req.get("steps", 8)),
              thinking=bool(lm and lm != "none"))
    if "turbo" in dit_name:
        kw["shift"] = 3.0
    if req.get("bpm"):
        kw["bpm"] = int(round(req["bpm"]))
    if req.get("keyscale"):
        kw["keyscale"] = req["keyscale"]
    if req.get("timesignature"):
        kw["timesignature"] = str(req["timesignature"])
    if task == "repaint":
        kw |= dict(src_audio=req["src_audio"], repainting_start=float(req["repaint_start"]),
                   repainting_end=float(req["repaint_end"]), chunk_mask_mode="explicit",
                   repaint_strength=float(req.get("strength", 0.5)))
        kw.pop("duration")
    n = int(req.get("n", 1))
    seeds = [int(req.get("seed", 1000)) + k * 7919 for k in range(n)]
    os.makedirs(req["out_dir"], exist_ok=True)
    for k, seed in enumerate(seeds):  # one at a time: batch_size > 1 doubles memory on a 16 GB Mac
        t1 = time.time()
        params = GenerationParams(seed=seed, **kw)
        cfg = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[seed], audio_format="wav")
        res = generate_music(dit, llm, params, cfg, save_dir=req["out_dir"])
        if not res.success:
            hint = (" Out of GPU memory: retry with --lm none." if "out of memory" in str(res.error).lower() else "")
            print(f"ACE_ERROR: {str(res.error)[:400]}{hint}", file=sys.stderr)
            sys.exit(1)
        for au in res.audios:
            print(json.dumps({"path": au["path"], "seed": seed, "secs": round(time.time() - t1, 1)}), flush=True)


if __name__ == "__main__":
    main()
