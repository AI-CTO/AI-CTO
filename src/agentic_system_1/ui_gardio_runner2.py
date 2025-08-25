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
    raise ImportError("Could not import backend module. Tried:" + "".join(_BACKEND_IMPORT_ERRORS))

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

        self.thread = threading.Thread(target=_target, daemon=True)
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
    st.setdefault("product_score", {})
    st.setdefault("product_scoren", {})
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

def _plot_signature(state: dict):
    data = (state or {}).get("product_score") or (state or {}).get("product_scoren") or {}
    if not isinstance(data, dict):
        return None
    items = []
    for label, v in sorted(data.items()):
        if isinstance(v, dict):
            items.append((str(label), v.get("x"), v.get("y"), v.get("impact")))
    return tuple(items)

def build_scatter(state: Dict[str, Any]) -> go.Figure:
    data = (state or {}).get("product_score") or (state or {}).get("product_scoren") or {}
    xs, ys, labels, impacts = [], [], [], []
    if isinstance(data, dict):
        for label, v in data.items():
            if isinstance(v, dict):
                x, y, imp = v.get("x"), v.get("y"), v.get("impact")
                if isinstance(x, (int, float)) and isinstance(y, (int, float)) and isinstance(imp, (int, float)):
                    labels.append(str(label))
                    xs.append(float(x)); ys.append(float(y)); impacts.append(float(imp))
    fig = go.Figure()
    if labels:
        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(
                size=[8 + 12 * max(0, min(1, i)) for i in impacts],
                color=impacts, colorscale="Viridis", showscale=True,
                colorbar=dict(title="impact")
            ),
            text=labels,
            hovertemplate="<b>%{text}</b><br>x=%{x:.3f}<br>y=%{y:.3f}<br>impact=%{marker.color:.3f}<extra></extra>"
        ))
        fig.update_layout(
            title="Product Score (x/y, color=impact)",
            template="plotly_white", height=460,
            xaxis_title="x", yaxis_title="y",
            uirevision="stay",
            transition={'duration': 0}
        )
    else:
        fig.update_layout(
            title="Product Score (no data yet)",
            template="plotly_white", height=420,
            xaxis_title="x", yaxis_title="y",
            uirevision="stay",
            transition={'duration': 0}
        )
    return fig


def confidence_sum(agent_scores: List[Any]) -> float:
    total = 0.0
    for it in (agent_scores or []):
        if isinstance(it, (int,float)):
            total += float(it)
        elif isinstance(it, dict) and isinstance(it.get("score"), (int,float)):
            total += float(it["score"])
    return round(total, 2)


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
    gr.Markdown("# Agentic UI — Backend-driven runner (no prompts in UI)")

    # Hidden states for chat messages and console accumulation
    chat_msgs = gr.State([])     # list[dict]
    console_state = gr.State("") # str

    with gr.Row():
        with gr.Column(scale=6):
            chatbot = gr.Chatbot(label="Chat", type="messages")
            with gr.Row():
                user_in = gr.Textbox(placeholder="Type here and press Enter or Send", show_label=False)
                send_btn = gr.Button("Send")
            active_md = gr.Markdown("Active node: idle")
            console = gr.Textbox(label="Backend console (all prints)", interactive=False, lines=16)
        with gr.Column(scale=6):
            plot = gr.Plot(label="Product Score")
            with gr.Row():
                conf_md = gr.Markdown("Confidence sum: 0.0")
                fill_md = gr.Markdown("Fields filled: 0/0 (0%)")
            product_code = gr.Code(language="json", label="state['product']")
            scores_code = gr.Code(language="json", label="state['agent_scores']")
            raw_state = gr.Code(language="json", label="raw state")

    # ---- Runtime loop: auto-start on load, periodic tick to mirror terminal --
    def on_load():
        global RUNNER, CURRENT_STATE, ACTIVE_NODE
        CURRENT_STATE = init_state()
        RUNNER = NodeRunner()
        RUNNER.start(s1_node, CURRENT_STATE)
        ACTIVE_NODE = "s1"
        logs = RUNNER.drain_logs()
        fig, conf, fill, prod, scores, raw = refresh_panels()
        return [], [], "Active node: s1", logs, fig, conf, fill, prod, scores, raw

    demo.load(
        on_load,
        inputs=[],
        outputs=[chatbot, chat_msgs, active_md, console, plot, conf_md, fill_md, product_code, scores_code, raw_state],
    )

    def route_if_finished(msgs: List[dict]) -> List[dict]:
        """If current node ended, start the next node and capture any immediate prints."""
        global RUNNER, CURRENT_STATE, ACTIVE_NODE
        if RUNNER and (not RUNNER.running) and RUNNER.last_returned_state is not None:
            CURRENT_STATE = RUNNER.last_returned_state
            nxt = decide_routing(CURRENT_STATE)
            if nxt == "s2":
                RUNNER = NodeRunner(); RUNNER.start(s2_node, CURRENT_STATE); ACTIVE_NODE = "s2"
            elif nxt == "s3":
                RUNNER = NodeRunner(); RUNNER.start(s3_node, CURRENT_STATE); ACTIVE_NODE = "s3"
            elif nxt == "s4":
                RUNNER = NodeRunner(); RUNNER.start(s4_node, CURRENT_STATE); ACTIVE_NODE = "s4"
            else:
                ACTIVE_NODE = "idle"
            # Flush any synchronous prints from newly started node
            extra = RUNNER.drain_logs() if RUNNER else ""
            for ans in parse_agent_replies(extra):
                msgs.append({"role": "assistant", "content": ans})
            return msgs, extra
        return msgs, ""

    def tick(msgs: List[dict], console_accum: str):
        """Periodic update: drain logs, append agent replies to chat, auto-route, update panels with minimal rerenders."""
        global LAST_PLOT_SIG, LAST_PLOT_FIG, LAST_CHAT_LEN
        global LAST_CONF_TEXT, LAST_FILL_TEXT, LAST_PRODUCT_JSON, LAST_SCORES_JSON, LAST_RAW_JSON, LAST_ACTIVE_NODE

        logs = RUNNER.drain_logs() if RUNNER else ""
        added = False
        for ans in parse_agent_replies(logs):
            msgs.append({"role": "assistant", "content": ans})
            added = True

        msgs, extra = route_if_finished(msgs)
        if extra:
            logs += extra
            added = True

        console_changed = bool(logs)
        if console_changed:
            console_accum = console_accum + logs

        st = CURRENT_STATE or {}
        conf_val = f"Confidence sum: {confidence_sum(st.get('agent_scores', []))}"

        product = st.get("product") if isinstance(st.get("product"), dict) else {}
        total = len(product)
        filled = sum(1 for v in product.values() if v not in (None, ""))
        fill_val = f"Fields filled: {filled}/{total} ({0 if total==0 else round(100.0*filled/total,1)}%)"

        product_json = ui_safe(product)
        scores_json  = ui_safe(st.get("agent_scores", []))
        raw_json     = ui_safe(st)
        active_val   = f"Active node: {ACTIVE_NODE}"

        sig = _plot_signature(st)
        if sig != LAST_PLOT_SIG:
            LAST_PLOT_SIG = sig
            LAST_PLOT_FIG = build_scatter(st)
            plot_out = LAST_PLOT_FIG
        else:
            plot_out = gr.update()

        if len(msgs) != LAST_CHAT_LEN:
            chat_out = msgs
            chat_state_out = msgs
            LAST_CHAT_LEN = len(msgs)
        else:
            chat_out = gr.update()
            chat_state_out = gr.update()

        console_out = (console_accum if console_changed else gr.update())

        conf_out  = (conf_val  if conf_val  != LAST_CONF_TEXT  else gr.update())
        fill_out  = (fill_val  if fill_val  != LAST_FILL_TEXT  else gr.update())
        prod_out  = (product_json if product_json != LAST_PRODUCT_JSON else gr.update())
        score_out = (scores_json  if scores_json  != LAST_SCORES_JSON  else gr.update())
        raw_out   = (raw_json     if raw_json     != LAST_RAW_JSON     else gr.update())
        active_out= (active_val   if active_val   != LAST_ACTIVE_NODE  else gr.update())

        LAST_CONF_TEXT   = conf_val
        LAST_FILL_TEXT   = fill_val
        LAST_PRODUCT_JSON= product_json
        LAST_SCORES_JSON = scores_json
        LAST_RAW_JSON    = raw_json
        LAST_ACTIVE_NODE = active_val

        return (
            chat_out,
            chat_state_out,
            console_accum,
            active_out,
            console_out,
            plot_out,
            conf_out,
            fill_out,
            prod_out,
            score_out,
            raw_out,
        )
    timer = gr.Timer(1.0)
    timer.tick(
        tick,
        inputs=[chat_msgs, console_state],
        outputs=[chatbot, chat_msgs, console_state, active_md, console, plot, conf_md, fill_md, product_code, scores_code, raw_state],
    )

    def do_send(msg: str, msgs: List[dict]):
        """Append user's message and feed it to input(); clearing textbox. Logs handled by timer."""
        global RUNNER
        if msg:
            msgs = msgs + [{"role": "user", "content": msg}]
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