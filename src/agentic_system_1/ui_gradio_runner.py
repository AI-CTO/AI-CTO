"""
Gradio UI that mirrors your terminal backend WITHOUT duplicating backend prompts.

- Chat shows ONLY user inputs and agent replies printed by your backend (like in terminal).
- All other prints go to the "Backend console" box.
- Panels reflect State live (product, scores, and product_score/scoren scatter).
- Visualization appears as soon as product_score/scoren exists (e.g., after your analysis step).
- Process runs continuously like terminal: auto-starts s1 on load, auto-routes between nodes.
- Only one control remains: the Send button (Enter works too).

Run:
  pip install gradio plotly python-dotenv
  python ui_gradio_runner.py

If your project path differs, set env AITO_ROOT to your repo root or edit PROJECT_ROOT below.
"""

import os
import sys
import json
import queue
import threading
from typing import Any, Dict, List
from contextlib import redirect_stdout, redirect_stderr

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

# ---- Locate and import your backend ----------------------------------------
PROJECT_ROOT = os.environ.get("AITO_ROOT", "/Users/erikstandard/Desktop/AI-CTO")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "src", "agentic_system_1") # uusi
os.makedirs(OUTPUT_DIR, exist_ok=True)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

_BACKEND_IMPORT_ERRORS: List[str] = []
backend = None
for mod_name in (
    "src.agentic_system_1.agentic_sysyem_test",
    "agentic_system_1.agentic_sysyem_test",
):
    try:
        backend = __import__(mod_name, fromlist=["*"])
        break
    except Exception as e:
        _BACKEND_IMPORT_ERRORS.append(f"{mod_name}: {e}")

if backend is None:
    raise ImportError("Could not import backend module. Tried: " + "".join(_BACKEND_IMPORT_ERRORS))

# Pull backend refs (NO prompt strings here)
start_node = backend.start_node
s1_node = backend.s1_node
s2_node = backend.s2_node
s3_node = backend.s3_node
s4_node = backend.s4_node
decide_routing = backend.decide_routing

# ---------------- Terminal adapter (capture prints + feed input) -------------
class QueueWriter:
    """A file-like writer that pushes text chunks into a queue as they arrive."""
    def __init__(self, q: queue.Queue):
        self.q = q
    def write(self, s: str) -> int:
        if s:
            self.q.put(s)
        return len(s)
    def flush(self):
        pass

class NodeRunner:
    """Runs a backend node in a thread, capturing prints and providing input()."""
    def __init__(self):
        self.thread: threading.Thread | None = None
        self.input_q: queue.Queue[str] = queue.Queue()
        self.log_q: queue.Queue[str] = queue.Queue()
        self.running = False
        self.last_returned_state: Dict[str, Any] | None = None

    def _fake_input(self, prompt: str = "") -> str:
        # Show prompt text if present (to console area only)
        if prompt:
            self.log_q.put(str(prompt))
        # Block until UI provides input
        return self.input_q.get()

    def start(self, func, state: Dict[str, Any]):
        if self.running:
            return
        self.running = True
        self.last_returned_state = None

        def _target():
            import builtins
            orig_input = builtins.input
            try:
                builtins.input = self._fake_input
                with redirect_stdout(QueueWriter(self.log_q)), redirect_stderr(QueueWriter(self.log_q)):
                    ret = func(state)
                self.last_returned_state = ret
            except Exception as e:
                self.log_q.put(f"[runner error] {e}")
            finally:
                builtins.input = orig_input
                self.running = False

        self.thread = threading.Thread(target=_target, daemon=False)
        self.thread.start()

    def send(self, text: str):
        self.input_q.put(text)

    def drain_logs(self) -> str:
        chunks: List[str] = []
        try:
            while True:
                chunks.append(self.log_q.get_nowait())
        except queue.Empty:
            pass
        return "".join(chunks)

# ----------------- Global runtime (avoid gr.State pickling issues) -----------
RUNNER: NodeRunner | None = None   # holds thread + queues (not deepcopyable)
CURRENT_STATE: Dict[str, Any] | None = None  # backend state dict (live)
ACTIVE_NODE: str = "idle"          # label for UI
CHAT_VERSION = 0
LAST_CHAT_VERSION = -1

# ---- Persistence for visualization (history + saving) ----------------------
OUTPUT_DIR = os.environ.get("AITO_OUTPUT", os.path.join(PROJECT_ROOT, "outputs"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Koko istunnon pistehistoria (kuten karvalakkiversiossa)
HISTORY: List[Dict[str, float]] = []
LAST_SAVED_SIG = None

def _sanitize_filename(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-", "_")).rstrip()

# ----------------- UI helpers ------------------------------------------------
import plotly.graph_objects as go
import gradio as gr

def init_state() -> Dict[str, Any]:
    st = start_node({})  # prints "--- Start node ---"
    # Patch types from start_node (your start_node uses type objects as placeholders)
    if isinstance(st.get("topic"), type):
        st["topic"] = "General Question"
    if isinstance(st.get("next_node"), type):
        st["next_node"] = 2
    # Ensure product is a dict, not <class 'dict'>
    if not isinstance(st.get("product"), dict):
        st["product"] = {}
    # Safe defaults
    st.setdefault("messages", [])
    st.setdefault("explanation", [])
    st.setdefault("agent_scores", [])
    st.setdefault("product_ranking", {})
    st.setdefault("need_for_referation", {})
    st.setdefault("product_ranking", {})
    #st.setdefault("product_scoren", {})
    return st

# Lines we consider as agent replies for the Chat area
AGENT_PREFIXES = (
    "Bot_S1:",
    "Question Agent:",
    "Question Agent :",
    "Bot_S1 :",
)

def parse_agent_replies(log_text: str) -> List[str]:
    replies: List[str] = []
    for ln in (log_text or "").splitlines():
        s = ln.strip()
        if any(s.startswith(p) for p in AGENT_PREFIXES):
            # strip the known prefix
            for p in AGENT_PREFIXES:
                if s.startswith(p):
                    s = s[len(p):].strip()
                    break
            if s:
                replies.append(s)
    return replies


# ---- Diff-aware caches to avoid unnecessary rerenders ----
LAST_PLOT_SIG = None
LAST_PLOT_FIG = None
LAST_CHAT_LEN = 0
LAST_CONF_TEXT = ""
LAST_FILL_TEXT = ""
LAST_PRODUCT_JSON = ""
LAST_SCORES_JSON = ""
LAST_RAW_JSON = ""
LAST_ACTIVE_NODE = ""

# def _plot_signature(state: dict):
#     data = (state or {}).get("product_ranking") or {}
#     if not isinstance(data, dict):
#         return None
#     items = []
#     for label, v in sorted(data.items()):
#         if isinstance(v, dict):
#             items.append((str(label), v.get("x"), v.get("y"), v.get("impact")))
#     return tuple(items)
def _plot_signature(state: dict):
    # HUOM: käytetään nyt product_ranking (kuten backendisi asettaa)
    data = (state or {}).get("product_ranking") or {}
    if not isinstance(data, dict):
        return None

    # ✅ FLAT-muoto: {'business_novelty_rank': 0..100, 'customer_novelty_rank': 0..100, 'impact_rank': 0..100}
    if all(k in data for k in ("business_novelty_rank", "customer_novelty_rank", "impact_rank")):
        try:
            return (
                "flat",
                float(data.get("business_novelty_rank")),
                float(data.get("customer_novelty_rank")),
                float(data.get("impact_rank", 0.0)),
            )
        except Exception:
            return None

    # ✅ NESTED-muoto: {'A': {...}, 'B': {...}}
    items = []
    for label, v in sorted(data.items()):
        if isinstance(v, dict):
            x = v.get("business_novelty_rank") or v.get("Business Novelty")
            y = v.get("customer_novelty_rank") or v.get("Customer Novelty")
            imp = v.get("impact_rank") or v.get("impact") or 0.0
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                items.append((str(label), float(x), float(y), float(imp)))
    return tuple(items) if items else None

def build_scatter(state: Dict[str, Any]) -> go.Figure:
    # Jos historiassa on pisteitä, piirretään koko historia
    if HISTORY:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=[d["BN_Rank"] for d in HISTORY],
            y=[d["CN_Rank"] for d in HISTORY],
            mode="markers+text",
            text=[d["Name"] for d in HISTORY],
            textposition="top center",
            marker=dict(
                size=[8 + 12 * max(0, min(1, (d["Impact_Rank"] / 100))) for d in HISTORY],
                color=[d["Impact_Rank"] for d in HISTORY],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="impact")
            ),
            hovertemplate="<b>%{text}</b><br>Business Novelty=%{x:.1f}"
                          "<br>Customer Novelty=%{y:.1f}"
                          "<br>Impact=%{marker.color:.1f}<extra></extra>"
        ))
        fig.update_layout(
            title="Form Score History (Business Novelty vs Customer Novelty)",
            template="plotly_white", height=460,
            xaxis_title="Business Novelty", yaxis_title="Customer Novelty",
            xaxis=dict(range=[0, 100]),
            yaxis=dict(range=[0, 100]),
            uirevision="stay"
        )
        return fig

    # Muuten näytetään tämänhetkisen staten pisteet (flat tai nested)
    data = (state or {}).get("product_ranking") or {}
    xs, ys, labels, impacts = [], [], [], []
    if isinstance(data, dict):
        nested_found = False
        for label, v in data.items():
            if isinstance(v, dict):
                x = v.get("business_novelty_rank") or v.get("Business Novelty")
                y = v.get("customer_novelty_rank") or v.get("Customer Novelty")
                imp = v.get("impact_rank") or v.get("impact")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                    nested_found = True
                    labels.append(str(label))
                    xs.append(float(x)); ys.append(float(y)); impacts.append(float(imp or 0.0))
        if not nested_found:
            x = data.get("business_novelty_rank") or data.get("Business Novelty")
            y = data.get("customer_novelty_rank") or data.get("Customer Novelty")
            imp = data.get("impact_rank") or data.get("impact")
            if isinstance(x, (int, float)) and isinstance(y, (int, float)):
                labels.append("score")
                xs.append(float(x)); ys.append(float(y)); impacts.append(float(imp or 0.0))

    fig = go.Figure()
    if labels:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(
                size=[8 + 12 * max(0, min(1, i/100)) for i in impacts],
                color=impacts, colorscale="Viridis", showscale=True,
                colorbar=dict(title="impact")
            ),
            text=labels,
            hovertemplate="<b>%{text}</b><br>Business Novelty=%{x:.1f}"
                          "<br>Customer Novelty=%{y:.1f}"
                          "<br>Impact=%{marker.color:.1f}<extra></extra>"
        ))
        fig.update_layout(
            title="Form Score (Business Novelty vs Customer Novelty, color=impact)",
            template="plotly_white", height=460,
            xaxis_title="Business Novelty", yaxis_title="Customer Novelty",
            xaxis=dict(range=[0, 100]),
            yaxis=dict(range=[0, 100]),
            uirevision="stay"
        )
    else:
        fig.update_layout(
            title="Form visualization (no scores yet)",
            template="plotly_white", height=420,
            xaxis_title="Business Novelty", yaxis_title="Customer Novelty",
            xaxis=dict(range=[0, 100]),
            yaxis=dict(range=[0, 100]),
            uirevision="stay"
        )
    return fig

def update_history_and_maybe_save(state: Dict[str, Any], fig: go.Figure):
    """Päivitä HISTORY ja tallenna CSV + HTML (+PNG jos kaleido)."""
    global HISTORY, LAST_SAVED_SIG, OUTPUT_DIR

    score = (state or {}).get("product_ranking") or {}
    if not isinstance(score, dict):
        return

    appended = False
    # Flat-muoto
    if all(k in score for k in ("business_novelty_rank", "customer_novelty_rank", "impact_rank")):
        x = score.get("business_novelty_rank"); y = score.get("customer_novelty_rank"); imp = score.get("impact_rank")
        if isinstance(x,(int,float)) and isinstance(y,(int,float)):
            name = (state.get("product") or {}).get("company_name") \
                   or (state.get("product") or {}).get("product_name") \
                   or f"Item {len(HISTORY)+1}"
            HISTORY.append({"Name": str(name), "BN_Rank": float(x), "CN_Rank": float(y), "Impact_Rank": float(imp or 0.0)})
            appended = True
    else:
        # Nested: useampi rivi
        for label, v in score.items():
            if isinstance(v, dict):
                x = v.get("business_novelty_rank") or v.get("Business Novelty")
                y = v.get("customer_novelty_rank") or v.get("Customer Novelty")
                imp = v.get("impact_rank") or v.get("impact")
                if isinstance(x,(int,float)) and isinstance(y,(int,float)):
                    HISTORY.append({"Name": str(label), "BN_Rank": float(x), "CN_Rank": float(y), "Impact_Rank": float(imp or 0.0)})
                    appended = True

    if not appended:
        return

    # Allekirjoitus: koko historian sisältö (estää duplikaatit)
    sig = tuple((d["Name"], d["BN_Rank"], d["CN_Rank"], d["Impact_Rank"]) for d in HISTORY)
    if sig == LAST_SAVED_SIG:
        return
    LAST_SAVED_SIG = sig

    # CSV (append viimeisin rivi)
    try:
        import csv
        csv_path = os.path.join(OUTPUT_DIR, "product_scores_history.csv")
        write_header = not os.path.exists(csv_path)
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Name","BN_Rank","CN_Rank","Impact_Rank"])
            if write_header:
                w.writeheader()
            w.writerow(HISTORY[-1])
    except Exception:
        pass

    # HTML-plot historyn perusteella
    try:
        hist_fig = go.Figure()
        hist_fig.add_trace(go.Scatter(
            x=[d["BN_Rank"] for d in HISTORY],
            y=[d["CN_Rank"] for d in HISTORY],
            mode="markers+text",
            text=[d["Name"] for d in HISTORY],
            textposition="top center",
            marker=dict(
                size=[8 + 12 * max(0, min(1, (d["Impact_Rank"]/100))) for d in HISTORY],
                color=[d["Impact_Rank"] for d in HISTORY],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="impact")
            ),
            hovertemplate="<b>%{text}</b><br>BN=%{x:.1f}<br>CN=%{y:.1f}<br>Impact=%{marker.color:.1f}<extra></extra>"
        ))
        hist_fig.update_layout(
            title="Form Score History",
            template="plotly_white", height=460,
            xaxis_title="Business Novelty", yaxis_title="Customer Novelty",
            xaxis=dict(range=[0, 100]),
            yaxis=dict(range=[0, 100]),
        )
        html_path = os.path.join(OUTPUT_DIR, "product_scores_scatter.html")
        hist_fig.write_html(html_path, include_plotlyjs="cdn", full_html=True)
    except Exception:
        pass

    # PNG (vain jos kaleido on asennettu)
    try:
        import plotly.io as pio
        png_path = os.path.join(OUTPUT_DIR, "product_scores_scatter.png")
        pio.write_image(hist_fig, png_path, scale=2, width=900, height=600)
    except Exception:
        pass

def confidence_sum(agent_scores: List[Any]) -> float:
    from typing import Any, List
    import math
    vals = []
    for it in (agent_scores or []):
        if isinstance(it, (int,float)):
            vals.append(float(it))
        elif isinstance(it, dict) and isinstance(it.get("score"), (int,float)):
            vals.append(float(it["score"]))
    if not vals:
        return 0.0
    # skaalataan 0–1, kerrotaan yhteen ja palautetaan prosenttina
    prod = math.prod(v/100.0 for v in vals)
    return round(prod * 100, 2)


def ui_safe(obj: Any) -> str:
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    except Exception:
        return str(obj)


def refresh_panels():
    st = CURRENT_STATE or {}
    fig = build_scatter(st)
    conf = confidence_sum(st.get("agent_scores", []))
    product = st.get("product") if isinstance(st.get("product"), dict) else {}
    total = len(product)
    filled = sum(1 for v in product.values() if v not in (None, ""))
    fill_pct = 0 if total == 0 else round(100.0 * filled / total, 1)
    return fig, f"Confidence sum: {conf}", f"Fields filled: {filled}/{total} ({fill_pct}%)", \
           ui_safe(product), ui_safe(st.get("agent_scores", [])), ui_safe(st)

# ----------------- Gradio app -----------------------------------------------
with gr.Blocks(title="Agentic Runner (backend-driven)", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# AI_CTO_v2.0")

    # Hidden states for chat messages and console accumulation
    chat_msgs = gr.State([])     # list[dict]
    console_state = gr.State("") # str

    with gr.Row():
        with gr.Column(scale=6):
            chatbot = gr.Chatbot(label="Chat", type="messages", height=460)
            with gr.Row():
                #user_in = gr.Textbox(placeholder="Type here and press Enter or Send", show_label=False)
                with gr.Column(scale=22):
                    user_in = gr.Textbox(
                        placeholder="Type here and press Enter or Send",
                        show_label=False,
                        lines=2,
                        max_lines=4,
                        container=False,
                    )
                with gr.Column(scale=2,):
                    send_btn = gr.Button("Send")
            active_md = gr.Markdown("Active node: idle")
            console = gr.Textbox(label="Console", interactive=False, lines=16)
        with gr.Column(scale=6):
            plot = gr.Plot(label="Visualization")
            with gr.Row():
                conf_md = gr.Markdown("Confidence sum: 0.0")
                fill_md = gr.Markdown("Fields filled: 0/0 (0%)")
            product_code = gr.Code(language="json", label="Form")
            scores_code = gr.Code(language="json", label="SPP Agent Scores']")
            raw_state = gr.Code(language="json", label="Process Information")

    # ---- Runtime loop: auto-start on load, periodic tick to mirror terminal --
    def on_load():
        global RUNNER, CURRENT_STATE, ACTIVE_NODE
        CURRENT_STATE = init_state()
        RUNNER = NodeRunner()
        RUNNER.start(s1_node, CURRENT_STATE)
        ACTIVE_NODE = "s1"
        logs = RUNNER.drain_logs()
        init_replies = parse_agent_replies(logs)
        init_msgs = [{"role": "assistant", "content": r} for r in init_replies]
        fig, conf, fill, prod, scores, raw = refresh_panels()

        return init_msgs, init_msgs, "Active node: s1", logs, fig, conf, fill, prod, scores, raw

    demo.load(
    on_load,
    inputs=[],
    outputs=[chatbot, chat_msgs, active_md, console, plot, conf_md, fill_md, product_code, scores_code, raw_state],
    )

    # def route_if_finished(msgs: List[dict]) -> List[dict]:
    #     """If current node ended, start the next node and capture any immediate prints."""
    #     global RUNNER, CURRENT_STATE, ACTIVE_NODE
    #     if RUNNER and (not RUNNER.running) and RUNNER.last_returned_state is not None:
    #         CURRENT_STATE = RUNNER.last_returned_state
    #         nxt = decide_routing(CURRENT_STATE)
    #         if nxt == "s2":
    #             RUNNER = NodeRunner(); RUNNER.start(s2_node, CURRENT_STATE); ACTIVE_NODE = "s2"
    #         elif nxt == "s3":
    #             RUNNER = NodeRunner(); RUNNER.start(s3_node, CURRENT_STATE); ACTIVE_NODE = "s3"
    #         elif nxt == "s4":
    #             RUNNER = NodeRunner(); RUNNER.start(s4_node, CURRENT_STATE); ACTIVE_NODE = "s4"
    #         else:
    #             ACTIVE_NODE = "idle"
    #         # Flush any synchronous prints from newly started node
    #         extra = RUNNER.drain_logs() if RUNNER else ""
    #         for ans in parse_agent_replies(extra):
    #             msgs.append({"role": "assistant", "content": ans})
    #         return msgs, extra
    #     return msgs, ""
    import threading
    SAVE_LOCK = threading.Lock()
    def route_if_finished(msgs: List[dict]):
        global RUNNER, CURRENT_STATE, ACTIVE_NODE, CHAT_VERSION
        if RUNNER and (not RUNNER.running) and RUNNER.last_returned_state is not None:
            # nosta viimeisin state
            CURRENT_STATE = RUNNER.last_returned_state
             # ⬇️ TÄRKEIN LISÄYS: tallennetaan kuva+historia heti (riippumatta tickeistä)
            try:
                snap = json.loads(json.dumps(CURRENT_STATE, default=str))  # syväkopio
                if (snap.get("product_ranking") or {}):                    # onko pisteitä?
                    with SAVE_LOCK:
                        fig_now = build_scatter(snap)
                        update_history_and_maybe_save(snap, fig_now)       # tallentaa CSV/HTML/PNG
            except Exception:
                pass  # hiljennä UI:sta

            # 🔁 jos juuri ajettiin s4 valmiiksi, aloita alusta (vastaa backendin s4->start -reunaa)
            if ACTIVE_NODE == "s4" or CURRENT_STATE.get("finished"):
                CURRENT_STATE = init_state()
                RUNNER = NodeRunner()
                RUNNER.start(s1_node, CURRENT_STATE)
                ACTIVE_NODE = "s1"
                extra = RUNNER.drain_logs()
                for ans in parse_agent_replies(extra):
                    msgs.append({"role": "assistant", "content": ans})
                    CHAT_VERSION += 1  
                return msgs, extra

            # muussa tapauksessa käytä normaalia reititystä
            nxt = decide_routing(CURRENT_STATE)
            if nxt == "s2":
                RUNNER = NodeRunner(); RUNNER.start(s2_node, CURRENT_STATE); ACTIVE_NODE = "s2"
            elif nxt == "s3":
                RUNNER = NodeRunner(); RUNNER.start(s3_node, CURRENT_STATE); ACTIVE_NODE = "s3"
            elif nxt == "s4":
                RUNNER = NodeRunner(); RUNNER.start(s4_node, CURRENT_STATE); ACTIVE_NODE = "s4"
            else:
                ACTIVE_NODE = "idle"

            extra = RUNNER.drain_logs() if RUNNER else ""
            for ans in parse_agent_replies(extra):
                msgs.append({"role": "assistant", "content": ans})
            return msgs, extra

        return msgs, ""


    # def tick_fast(msgs: List[dict], console_accum: str):
    #     """Fast loop: chat + console + routing only. Avoids touching metrics/plot to prevent flicker."""
    #     global LAST_CHAT_LEN, LAST_ACTIVE_NODE

    #     logs = RUNNER.drain_logs() if RUNNER else ""
    #     for ans in parse_agent_replies(logs):
    #         msgs.append({"role": "assistant", "content": ans})

    #     msgs, extra = route_if_finished(msgs)
    #     if extra:
    #         logs += extra

    #     if logs:
    #         console_accum = console_accum + logs
    #         console_out = console_accum
    #     else:
    #         console_out = gr.update()

    #     # chat updates only if length changed
    #     if len(msgs) != LAST_CHAT_LEN:
    #         chat_out = msgs
    #         chat_state_out = msgs
    #         LAST_CHAT_LEN = len(msgs)
    #     else:
    #         chat_out = gr.update()
    #         chat_state_out = gr.update()

    #     active_val = f"Active node: {ACTIVE_NODE}"
    #     if active_val != LAST_ACTIVE_NODE:
    #         active_out = active_val
    #         LAST_ACTIVE_NODE = active_val
    #     else:
    #         active_out = gr.update()

    #     # Do not touch plot/metrics in fast loop → return no-op updates
    #     noop = gr.update()
    #     return (
    #         chat_out,         # chatbot
    #         chat_state_out,   # chat_msgs state
    #         console_accum,    # console_state state (keep full buffer)
    #         active_out,       # active_md
    #         console_out,      # console textbox
    #         noop,             # plot
    #         noop,             # conf_md
    #         noop,             # fill_md
    #         noop,             # product_code
    #         noop,             # scores_code
    #         noop,             # raw_state
    #     )
    def reflect_chat(msgs: list[dict]):
        return msgs

    chat_msgs.change(
        reflect_chat,
        inputs=chat_msgs,
        outputs=chatbot,
)
    
    def tick_fast(msgs: List[dict], console_accum: str):
        global LAST_ACTIVE_NODE, CHAT_VERSION, LAST_CHAT_VERSION

        changed = False
        logs = RUNNER.drain_logs() if RUNNER else ""

        # uudet agenttirepliikit
        replies = parse_agent_replies(logs)
        if replies:
            for r in replies:
                msgs.append({"role": "assistant", "content": r})
            CHAT_VERSION += 1                 # ⬅️ vain kun oikeasti lisättiin viestejä
            changed = True

        # reititys ja mahdolliset synkroniset tulosteet
        msgs, extra = route_if_finished(msgs)
        if extra:
            logs += extra
            # huom: route_if_finished jo appends msgs, joten versio nostetaan siellä tarvittaessa

        # console päivittyy vain jos uutta tuli
        if logs:
            console_accum = console_accum + logs
            console_out = console_accum
        else:
            console_out = gr.update()

        # chat päivitys vain jos versio muuttui
        if CHAT_VERSION != LAST_CHAT_VERSION:
            chat_out = msgs
            chat_state_out = msgs
            LAST_CHAT_VERSION = CHAT_VERSION
        else:
            chat_out = gr.update()
            chat_state_out = gr.update()

        active_val = f"Active node: {ACTIVE_NODE}"
        active_out = active_val if active_val != LAST_ACTIVE_NODE else gr.update()
        LAST_ACTIVE_NODE = active_val

        noop = gr.update()
        return (
            msgs,            # chat_msgs (state)  ← vain tämä, ei Chatbotia
            console_accum,   # console_state
            active_out,      # active_md
            console_out,     # console
            noop,            # plot
            noop,            # conf_md
            noop,            # fill_md
            noop,            # product_code
            noop,            # scores_code
            noop,            # raw_state
        )

    def tick_slow():
        """Slow loop: metrics + plot only, with diff-aware caches to eliminate flicker."""
        global LAST_PLOT_SIG, LAST_PLOT_FIG
        global LAST_CONF_TEXT, LAST_FILL_TEXT, LAST_PRODUCT_JSON, LAST_SCORES_JSON, LAST_RAW_JSON

        st = CURRENT_STATE or {}
        # Plot signature
        sig = _plot_signature(st)
        # if sig != LAST_PLOT_SIG:
        #     LAST_PLOT_SIG = sig
        #     LAST_PLOT_FIG = build_scatter(st)
        #     plot_out = LAST_PLOT_FIG
        # else:
        #     plot_out = gr.update()
        if sig != LAST_PLOT_SIG:
            LAST_PLOT_SIG = sig
            LAST_PLOT_FIG = build_scatter(st)
            # Tallenna historia + visualisaatio vain kun näkymä muuttuu
            try:
                update_history_and_maybe_save(st, LAST_PLOT_FIG)
            except Exception:
                pass
            plot_out = LAST_PLOT_FIG
        else:
            plot_out = gr.update()
        try:
        # jos LAST_PLOT_FIG on None, rakenna kertaluonteinen fig
            update_history_and_maybe_save(st, LAST_PLOT_FIG if LAST_PLOT_FIG else build_scatter(st))
        except Exception:
            pass
            # Confidence sum
        conf_val = f"Confidence sum: {confidence_sum(st.get('agent_scores', []))}"
        conf_out = conf_val if conf_val != LAST_CONF_TEXT else gr.update()
        LAST_CONF_TEXT = conf_val

        # Fill status
        product = st.get("product") if isinstance(st.get("product"), dict) else {}
        total = len(product)
        filled = sum(1 for v in product.values() if v not in (None, ""))
        fill_val = f"Fields filled: {filled}/{total} ({0 if total==0 else round(100.0*filled/total,1)}%)"
        fill_out = fill_val if fill_val != LAST_FILL_TEXT else gr.update()
        LAST_FILL_TEXT = fill_val

        # JSON panels
        product_json = ui_safe(product)
        scores_json  = ui_safe(st.get("agent_scores", []))
        raw_json     = ui_safe(st)

        prod_out  = product_json if product_json != LAST_PRODUCT_JSON else gr.update()
        score_out = scores_json  if scores_json  != LAST_SCORES_JSON  else gr.update()
        raw_out   = raw_json     if raw_json     != LAST_RAW_JSON     else gr.update()

        LAST_PRODUCT_JSON = product_json
        LAST_SCORES_JSON  = scores_json
        LAST_RAW_JSON     = raw_json

        # Return only the slow outputs, but need to align with full outputs list → return updates for others
        noop = gr.update()
        return (
            gr.update(),  # console_state
            gr.update(),  # active_md
            gr.update(),  # console
            plot_out,     # plot
            conf_out,     # conf_md
            fill_out,     # fill_md
            prod_out,     # product_code
            score_out,    # scores_code
            raw_out,      # raw_state
        )
    # Two timers: fast for chat/console (low-latency), slow for metrics/plot (fewer rerenders)
    fast_timer = gr.Timer(0.4) #visible argumentti ei ole olemassa 
    fast_timer.tick(
        tick_fast,
        inputs=[chat_msgs, console_state],
        outputs=[chat_msgs, console_state, active_md, console, plot, conf_md, fill_md, product_code, scores_code, raw_state],
    )

    slow_timer = gr.Timer(1.8) #visible argumenttia ei ole olemassa
    slow_timer.tick(
        tick_slow,
        inputs=[],
        outputs=[console_state, active_md, console, plot, conf_md, fill_md, product_code, scores_code, raw_state],
    )

    def do_send(msg: str, msgs: List[dict]):
        """Append user's message and feed it to input(); clearing textbox. Logs handled by timer."""
        global RUNNER, CURRENT_STATE, ACTIVE_NODE, CHAT_VERSION
        if msg:
            msgs = msgs + [{"role": "user", "content": msg}]
            CHAT_VERSION += 1
            if RUNNER and RUNNER.running:
                RUNNER.send(msg)
        return msgs, msgs, ""

    send_btn.click(
        do_send,
        inputs=[user_in, chat_msgs],
        outputs=[chatbot, chat_msgs, user_in],
    )
    user_in.submit(
        do_send,
        inputs=[user_in, chat_msgs],
        outputs=[chatbot, chat_msgs, user_in],
    )

if __name__ == "__main__":
    demo.launch()
