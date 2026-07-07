import time
import os
import re
import collections

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.bar import Bar
from rich import box

ALERT_FILE = "ids_alerts.log"
REFRESH_SEC = 1
TIMELINE_BUCKET_SEC = 5
TIMELINE_BUCKETS = 40
ALERT_FEED_SIZE = 9

console = Console()

SEVERITY_STYLE = {
    "CRITICAL": "bold white on red",
    "HIGH":     "bold red",
    "MEDIUM":   "bold yellow",
    "LOW":      "dim white",
}
SEVERITY_BAR_STYLE = {
    "CRITICAL": "red",
    "HIGH":     "red",
    "MEDIUM":   "yellow",
    "LOW":      "white",
}
SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

# Mapping des types d'attaque vers les étapes de la Kill Chain (Cyber Kill Chain simplifiée)
KILL_CHAIN_STAGES = [
    ("RECONNAISSANCE", ["PORT_SCAN", "WEB_ENUMERATION"]),
    ("INTRUSION",       ["SQL_INJECTION", "XSS_ATTACK", "SSH_BRUTE","FTP_BRUTE", "SENSITIVE_FILE_ACCESS"]),
    ("C2 / BEACONING",  ["C2_BEACON"]),
    ("MOUVEMENT LATÉRAL", ["LATERAL_MOVEMENT"]),
    ("EXFILTRATION",    ["DATA_EXFILTRATION"]),
]


class Aggregator:
    """Conserve l'état en mémoire pour ne jamais relire tout le fichier."""

    def __init__(self):
        self.total = 0
        self.dropped_by_ips = 0   # paquets bloqués car IP déjà bannie (bruit pur, isolé du reste)
        self.type_counts = collections.Counter()
        self.ip_counts = collections.Counter()
        self.severity_counts = collections.Counter()
        self.cred_counts = collections.Counter()
        self.stages_seen = set()
        self.timeline = collections.deque([0] * TIMELINE_BUCKETS, maxlen=TIMELINE_BUCKETS)
        self.recent_alerts = collections.deque(maxlen=ALERT_FEED_SIZE)
        self._bucket_start = None
        self._bucket_count = 0

    def maybe_roll_timeline(self):
        now = time.time()
        if self._bucket_start is None:
            self._bucket_start = now
            return
        if now - self._bucket_start >= TIMELINE_BUCKET_SEC:
            self.timeline.append(self._bucket_count)
            self._bucket_count = 0
            self._bucket_start = now

    def _update_stages(self, attack_type):
        for stage_name, types in KILL_CHAIN_STAGES:
            if attack_type in types:
                self.stages_seen.add(stage_name)

    def ingest(self, line):
        type_match = re.search(r"TYPE:(\w+)", line)
        sev_match = re.search(r"SEV:(\w+)", line)
        src_match = re.search(r"SRC:([0-9.]+)", line)
        cred_match = re.search(r"CREDENTIALS='([^']+)'", line)

        self.total += 1
        self._bucket_count += 1

        attack_type = type_match.group(1) if type_match else "UNKNOWN"
        severity = sev_match.group(1) if sev_match else "LOW"
        src_ip = src_match.group(1) if src_match else "?"

        # Le bruit "déjà banni" est compté à part : il pollue les stats sans représenter
        # une nouvelle menace (c'est exactement le problème d'anti-spam visuel du SIEM d'origine).
        if attack_type == "REPEATED_ATTACK":
            self.dropped_by_ips += 1
            return

        self.type_counts[attack_type] += 1
        self.severity_counts[severity] += 1
        if src_match:
            self.ip_counts[src_ip] += 1
        if cred_match:
            self.cred_counts[cred_match.group(1)] += 1    

        self._update_stages(attack_type)
        self.recent_alerts.append((time.strftime("%H:%M:%S"), attack_type, severity, src_ip))


def render_header(agg):
    status = Text(justify="center")
    status.append(" ENTERPRISE SOC ", style="bold white on dark_blue")
    status.append("  •  ", style="dim")
    status.append("AGGREGATION DASHBOARD", style="bold cyan")
    status.append("  •  ", style="dim")
    if agg.total == 0:
        status.append("RÉSEAU SÉCURISÉ", style="bold green")
    else:
        status.append(f"{agg.total} ÉVÈNEMENTS", style="bold red")
        status.append("  •  ", style="dim")
        status.append(f"🔥 {sum(agg.type_counts.values())} menaces distinctes", style="bold orange3")
        status.append("  •  ", style="dim")
        status.append(f"🧱 {agg.dropped_by_ips} paquets droppés par l'IPS (IP bannies)", style="dim")
    return Panel(Align.center(status), box=box.HEAVY, style="on grey11")


def render_severity_panel(agg):
    table = Table.grid(padding=(0, 1))
    table.add_column(justify="left")
    table.add_column(justify="left", ratio=1)
    table.add_column(justify="right")

    max_count = max(agg.severity_counts.values(), default=1)
    for sev in SEVERITY_ORDER:
        count = agg.severity_counts.get(sev, 0)
        style = SEVERITY_STYLE[sev]
        bar_width = int((count / max_count) * 20) if max_count else 0
        bar = "█" * bar_width + "░" * (20 - bar_width)
        table.add_row(
            Text(sev, style=style),
            Text(bar, style=SEVERITY_BAR_STYLE[sev]),
            Text(str(count), style=style),
        )
    return Panel(table, title="🛡️  Sévérité", border_style="magenta", box=box.ROUNDED)


def render_top_threats(agg):
    table = Table(box=box.SIMPLE_HEAVY, expand=True, show_edge=False)
    table.add_column("Type d'attaque", style="bold")
    table.add_column("Occ.", justify="right")
    table.add_column("", ratio=1)

    if not agg.type_counts:
        return Panel(Text("En attente de données...", style="dim"), title="🔥 Top Menaces", border_style="red")

    max_count = max(agg.type_counts.values())
    for attack, count in agg.type_counts.most_common(6):
        bar_len = int((count / max_count) * 18)
        bar = Text("▇" * bar_len, style="red")
        table.add_row(attack, str(count), bar)
    return Panel(table, title="🔥 Top Menaces (par volume)", border_style="red", box=box.ROUNDED)


def render_top_attackers(agg):
    table = Table(box=box.SIMPLE_HEAVY, expand=True, show_edge=False)
    table.add_column("IP Source", style="bold cyan")
    table.add_column("Paquets", justify="right")
    table.add_column("", ratio=1)

    if not agg.ip_counts:
        return Panel(Text("En attente de données...", style="dim"), title="🎯 Top Attaquants", border_style="cyan")

    max_count = max(agg.ip_counts.values())
    for ip, count in agg.ip_counts.most_common(6):
        bar_len = int((count / max_count) * 18)
        bar = Text("▇" * bar_len, style="bright_cyan")
        table.add_row(ip, str(count), bar)
    return Panel(table, title="🎯 Top Attaquants (IP Sources)", border_style="cyan", box=box.ROUNDED)
def render_top_credentials(agg):
    table = Table(box=box.SIMPLE_HEAVY, expand=True, show_edge=False)
    table.add_column("Identifiants (User:Pass)", style="bold magenta")
    table.add_column("Occ.", justify="right")
    table.add_column("", ratio=1) 

    if not agg.cred_counts:
        return Panel(Text("En attente de captures...", style="dim"), title="🔑 Top Identifiants (Honeypot)", border_style="magenta")

    max_count = max(agg.cred_counts.values())
    # On affiche le top 6 des combinaisons user:pass
    for cred, count in agg.cred_counts.most_common(6):
        bar_len = int((count / max_count) * 15)
        bar = Text("▇" * bar_len, style="bright_magenta")
        table.add_row(cred, str(count), bar)
        
    return Panel(table, title="🔑 Top Identifiants (Honeypot)", border_style="magenta", box=box.ROUNDED)

def render_kill_chain(agg):
    text = Text(justify="left")
    for i, (stage_name, _) in enumerate(KILL_CHAIN_STAGES):
        seen = stage_name in agg.stages_seen
        marker = "●" if seen else "○"
        style = "bold green" if seen else "dim white"
        text.append(f"{marker} ", style=style)
        text.append(stage_name, style=style if seen else "dim")
        if i < len(KILL_CHAIN_STAGES) - 1:
            text.append("   ➔   ", style="dim")
    return Panel(Align.center(text), title="⛓️  Progression de la Kill Chain", border_style="yellow", box=box.ROUNDED)


def render_timeline(agg):
    values = list(agg.timeline)
    max_val = max(values) if any(values) else 1
    sparks = " ▁▂▃▄▅▆▇█"
    line = Text()
    for v in values:
        idx = int((v / max_val) * (len(sparks) - 1)) if max_val else 0
        color = "green" if v == 0 else ("red" if idx >= 6 else "yellow")
        line.append(sparks[idx], style=color)
    subtitle = f"(tranches de {TIMELINE_BUCKET_SEC}s • pic = {max_val} évènements)"
    grid = Table.grid()
    grid.add_row(line)
    grid.add_row(Text(subtitle, style="dim"))
    return Panel(grid, title="📈 Timeline du Trafic Malveillant", border_style="green", box=box.ROUNDED)


def render_alert_feed(agg):
    table = Table(box=box.SIMPLE, expand=True, show_edge=False)
    table.add_column("Heure", style="dim", width=9)
    table.add_column("Type", style="bold")
    table.add_column("Sév.", width=9)
    table.add_column("Source")

    for ts, attack_type, sev, ip in reversed(agg.recent_alerts):
        style = SEVERITY_STYLE.get(sev, "white")
        table.add_row(ts, attack_type, Text(sev, style=style), ip)

    if not agg.recent_alerts:
        return Panel(Text("Aucune alerte récente.", style="dim"), title="📜 Flux d'Alertes en Direct", border_style="white")
    return Panel(table, title="📜 Flux d'Alertes en Direct", border_style="white", box=box.ROUNDED)


def build_layout(agg):
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="killchain", size=3),
        Layout(name="body", ratio=2),
        Layout(name="timeline", size=5),
        Layout(name="feed", size=ALERT_FEED_SIZE + 3),
    )
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )
    layout["left"].split_column(
        Layout(name="severity"),
        Layout(name="threats"),
    )
    layout["right"].split_column(
        Layout(name="attackers"),
        Layout(name="credentials") 
    )

    layout["header"].update(render_header(agg))
    layout["killchain"].update(render_kill_chain(agg))
    layout["severity"].update(render_severity_panel(agg))
    layout["threats"].update(render_top_threats(agg))
    layout["attackers"].update(render_top_attackers(agg))
    layout["credentials"].update(render_top_credentials(agg))
    layout["timeline"].update(render_timeline(agg))
    layout["feed"].update(render_alert_feed(agg))
    return layout


def main():
    console.print("[bold cyan]Initialisation du moteur d'agrégation...[/bold cyan]")
    open(ALERT_FILE, "a").close()

    agg = Aggregator()

    with open(ALERT_FILE, "r") as f, Live(build_layout(agg), console=console, refresh_per_second=4, screen=True) as live:
        while True:
            line = f.readline()
            if line:
                agg.ingest(line)
                continue
            agg.maybe_roll_timeline()
            live.update(build_layout(agg))
            time.sleep(REFRESH_SEC)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Arrêt du dashboard.[/yellow]")
