"""Quick manual check of the whole pipeline from the terminal (uses the real API)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from doctor_agent.memory import Memory
from doctor_agent.orchestrator import DoctorAgentSystem

QUESTIONS = sys.argv[1:] or [
    "What causes acne?",
    "Apa saja gejala bronkitis?",
    "Bagaimana cara mengobatinya?",
    "Apa obat untuk diabetes tipe 2?",
]

system = DoctorAgentSystem()
memory = Memory()
total = 0.0
for q in QUESTIONS:
    r = system.ask(q, memory)
    total += r.cost
    print("=" * 90)
    print("Q:", q)
    for s in r.steps:
        print(f"  [{s.agent:10}] {s.action:45} {s.seconds:5.1f}s ${s.cost:.4f}  {s.detail[:150]}")
    conf = f"{r.confidence:.2f}" if r.confidence is not None else "-"
    print(f"-> intent={r.intent} confidence={conf} escalated={r.escalated} revised={r.revised} "
          f"attempts={r.attempts} {r.seconds:.1f}s ${r.cost:.4f}")
    print("A:", r.answer[:700])
print("=" * 90)
print(f"memory summary: {memory.summary!r}")
print(f"TOTAL COST: ${total:.4f}")
