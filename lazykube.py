#!/usr/bin/env python3
"""LazyKube - A stylish terminal UI for Kubernetes"""

from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, DataTable, Static, Label, TabbedContent, TabPane, Log
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual import work, on
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Button
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich import box
import asyncio
import subprocess
import json
from datetime import datetime, timezone

# ── Kubernetes client ──────────────────────────────────────────────────────────
try:
    from kubernetes import client, config as k8s_config
    from kubernetes.client.rest import ApiException
    k8s_config.load_kube_config()
    v1   = client.CoreV1Api()
    apps = client.AppsV1Api()
    net  = client.NetworkingV1Api()
    # Eagerly test the connection
    v1.list_namespace(_request_timeout=5)
    K8S_OK = True
    K8S_ERR = None
except Exception as e:
    K8S_OK = False
    K8S_ERR = str(e)
    v1 = apps = net = None


def age(ts) -> str:
    if ts is None:
        return "—"
    delta = datetime.now(timezone.utc) - ts
    s = int(delta.total_seconds())
    if s < 60:    return f"{s}s"
    if s < 3600:  return f"{s//60}m"
    if s < 86400: return f"{s//3600}h"
    return f"{s//86400}d"


def status_color(s: str) -> str:
    s = s.lower()
    if s in ("running", "active", "true", "available", "bound"):
        return "green"
    if s in ("pending", "containercreating", "init"):
        return "yellow"
    if s in ("failed", "error", "crashloopbackoff", "oomkilled", "false"):
        return "red"
    return "white"


# ── Connection Error Screen ────────────────────────────────────────────────────
class ErrorScreen(ModalScreen):
    BINDINGS = [("q", "quit_app", "Quit"), ("r", "retry", "Retry")]

    def __init__(self, error: str):
        super().__init__()
        self._error = error

    def compose(self) -> ComposeResult:
        with Container(id="error-container"):
            yield Static(
                "\n"
                "[bold red]  ✗  Cannot connect to Kubernetes cluster[/]\n\n"
                f"[yellow]Error:[/]  [white]{self._error}[/]\n\n"
                "[bold cyan]What to do:[/]\n\n"
                "  [green]1.[/]  Make sure your cluster is running:\n"
                "       [dim]minikube start[/]   [dim]# local[/]\n"
                "       [dim]kind create cluster[/]\n\n"
                "  [green]2.[/]  Make sure kubeconfig is set up:\n"
                "       [dim]kubectl cluster-info[/]   [dim]# should succeed[/]\n"
                "       [dim]aws eks update-kubeconfig --name <cluster>[/]\n"
                "       [dim]gcloud container clusters get-credentials <cluster>[/]\n\n"
                "  [green]3.[/]  Re-run this app once the cluster is reachable.\n\n"
                "[dim]Press [bold]r[/] to retry connection  |  [bold]q[/] to quit[/]",
                id="error-body",
            )
            with Horizontal(id="error-buttons"):
                yield Button("  Retry", id="btn-retry", variant="success")
                yield Button("  Quit",  id="btn-quit",  variant="error")

    @on(Button.Pressed, "#btn-retry")
    def action_retry(self):
        self.dismiss("retry")

    @on(Button.Pressed, "#btn-quit")
    def action_quit_app(self):
        self.app.exit()


# ── Detail Modal ───────────────────────────────────────────────────────────────
class DetailModal(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Close"), ("q", "dismiss", "Close")]

    def __init__(self, title: str, content: str):
        super().__init__()
        self._title   = title
        self._content = content

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Label(f"  {self._title}  ", id="modal-title")
            yield ScrollableContainer(Static(self._content, id="modal-body"))
            yield Button("Close [ESC]", id="modal-close", variant="primary")

    @on(Button.Pressed, "#modal-close")
    def close(self):
        self.dismiss()


# ── Namespace bar ──────────────────────────────────────────────────────────────
class NamespaceBar(Static):
    namespace = reactive("default")

    def render(self):
        return Text.from_markup(
            f"  [bold cyan]Namespace:[/]  [bold yellow]{self.namespace}[/]  "
            f"  [dim]← → change  |  r refresh  |  / filter  |  Enter details  |  q quit[/]"
        )


# ── Resource tables ────────────────────────────────────────────────────────────
class PodsTable(DataTable):
    def on_mount(self):
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("NAME", "READY", "STATUS", "RESTARTS", "IP", "NODE", "AGE")

    def load(self, namespace: str):
        self.clear()
        if not K8S_OK:
            return
        try:
            pods = v1.list_namespaced_pod(namespace).items
        except ApiException:
            return
        for p in pods:
            cs      = p.status.container_statuses or []
            ready   = sum(1 for c in cs if c.ready)
            total   = len(p.spec.containers)
            restarts= sum(c.restart_count for c in cs)
            st      = p.status.phase or "Unknown"
            # override with container state
            for c in cs:
                if c.state.waiting:
                    st = c.state.waiting.reason or st
                    break
            color = status_color(st)
            self.add_row(
                Text(p.metadata.name, style="bold"),
                Text(f"{ready}/{total}", style="cyan"),
                Text(st, style=color),
                Text(str(restarts), style="red" if restarts > 0 else "white"),
                Text(p.status.pod_ip or "—", style="dim"),
                Text(p.spec.node_name or "—", style="dim"),
                Text(age(p.metadata.creation_timestamp), style="dim"),
            )


class ServicesTable(DataTable):
    def on_mount(self):
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("NAME", "TYPE", "CLUSTER-IP", "EXTERNAL-IP", "PORT(S)", "AGE")

    def load(self, namespace: str):
        self.clear()
        if not K8S_OK:
            return
        try:
            svcs = v1.list_namespaced_service(namespace).items
        except ApiException:
            return
        for s in svcs:
            ports = ", ".join(
                f"{p.port}:{p.node_port}/{p.protocol}" if p.node_port else f"{p.port}/{p.protocol}"
                for p in (s.spec.ports or [])
            )
            ext = s.spec.external_i_ps
            ext_str = ", ".join(ext) if ext else (
                s.status.load_balancer.ingress[0].ip
                if s.status.load_balancer and s.status.load_balancer.ingress
                else "—"
            )
            stype = s.spec.type or "ClusterIP"
            color = {"LoadBalancer": "green", "NodePort": "yellow", "ClusterIP": "cyan"}.get(stype, "white")
            self.add_row(
                Text(s.metadata.name, style="bold"),
                Text(stype, style=color),
                Text(s.spec.cluster_ip or "—"),
                Text(ext_str, style="green" if ext_str != "—" else "dim"),
                Text(ports or "—", style="dim"),
                Text(age(s.metadata.creation_timestamp), style="dim"),
            )


class DeploymentsTable(DataTable):
    def on_mount(self):
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("NAME", "READY", "UP-TO-DATE", "AVAILABLE", "STRATEGY", "AGE")

    def load(self, namespace: str):
        self.clear()
        if not K8S_OK:
            return
        try:
            deps = apps.list_namespaced_deployment(namespace).items
        except ApiException:
            return
        for d in deps:
            s     = d.status
            ready = s.ready_replicas or 0
            total = d.spec.replicas or 0
            color = "green" if ready == total and total > 0 else "yellow" if ready > 0 else "red"
            self.add_row(
                Text(d.metadata.name, style="bold"),
                Text(f"{ready}/{total}", style=color),
                Text(str(s.updated_replicas or 0), style="cyan"),
                Text(str(s.available_replicas or 0), style="green"),
                Text(d.spec.strategy.type or "—", style="dim"),
                Text(age(d.metadata.creation_timestamp), style="dim"),
            )


class IngressTable(DataTable):
    def on_mount(self):
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.add_columns("NAME", "CLASS", "HOSTS", "ADDRESS", "PORTS", "AGE")

    def load(self, namespace: str):
        self.clear()
        if not K8S_OK:
            return
        try:
            ings = net.list_namespaced_ingress(namespace).items
        except ApiException:
            return
        for i in ings:
            rules   = i.spec.rules or []
            hosts   = ", ".join(r.host or "*" for r in rules) or "—"
            cls     = i.spec.ingress_class_name or "—"
            lb      = i.status.load_balancer
            addr    = "—"
            if lb and lb.ingress:
                addr = lb.ingress[0].ip or lb.ingress[0].hostname or "—"
            tls_ports = "80,443" if i.spec.tls else "80"
            self.add_row(
                Text(i.metadata.name, style="bold"),
                Text(cls, style="cyan"),
                Text(hosts, style="yellow"),
                Text(addr, style="green" if addr != "—" else "dim"),
                Text(tls_ports, style="dim"),
                Text(age(i.metadata.creation_timestamp), style="dim"),
            )


# ── Stats sidebar ──────────────────────────────────────────────────────────────
class ClusterStats(Static):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stats = {}

    def update_stats(self, namespace: str):
        if not K8S_OK:
            self._stats = {}
            self.refresh()
            return
        try:
            pods  = v1.list_namespaced_pod(namespace).items
            svcs  = v1.list_namespaced_service(namespace).items
            deps  = apps.list_namespaced_deployment(namespace).items
            nodes = v1.list_node().items
            running = sum(1 for p in pods if p.status.phase == "Running")
            self._stats = {
                "pods":    (running, len(pods)),
                "svcs":    len(svcs),
                "deps":    len(deps),
                "nodes":   len(nodes),
            }
        except Exception:
            self._stats = {}
        self.refresh()

    def render(self):
        if not self._stats:
            err = K8S_ERR if not K8S_OK else "Loading…"
            return Panel(f"[red]{err}[/]", title="[bold]Cluster[/]", border_style="red")

        s = self._stats
        pr, pt = s.get("pods", (0, 0))
        pod_color = "green" if pr == pt else "yellow"

        lines = [
            f"[bold cyan]Pods[/]      [{pod_color}]{pr}/{pt}[/] running",
            f"[bold cyan]Services[/]  [white]{s.get('svcs',0)}[/]",
            f"[bold cyan]Deploys[/]   [white]{s.get('deps',0)}[/]",
            f"[bold cyan]Nodes[/]     [white]{s.get('nodes',0)}[/]",
            "",
            f"[dim]Updated {datetime.now().strftime('%H:%M:%S')}[/]",
        ]
        return Panel("\n".join(lines), title="[bold yellow]⎈ Cluster Stats[/]", border_style="yellow")


# ── Main App ───────────────────────────────────────────────────────────────────
class LazyKube(App):
    CSS = """
    Screen {
        background: #0d1117;
    }
    Header {
        background: #161b22;
        color: #58a6ff;
        text-style: bold;
    }
    Footer {
        background: #161b22;
        color: #8b949e;
    }
    NamespaceBar {
        height: 1;
        background: #21262d;
        color: #c9d1d9;
        padding: 0 1;
    }
    #main-layout {
        layout: horizontal;
        height: 1fr;
    }
    #sidebar {
        width: 28;
        background: #161b22;
        border-right: solid #30363d;
        padding: 1;
    }
    #content {
        width: 1fr;
        background: #0d1117;
    }
    TabbedContent {
        height: 1fr;
    }
    TabPane {
        padding: 0 1;
    }
    DataTable {
        height: 1fr;
        background: #0d1117;
    }
    DataTable > .datatable--header {
        background: #161b22;
        color: #58a6ff;
        text-style: bold;
    }
    DataTable > .datatable--cursor {
        background: #1f6feb;
        color: white;
    }
    DataTable > .datatable--even-row {
        background: #0d1117;
    }
    DataTable > .datatable--odd-row {
        background: #161b22;
    }
    TabbedContent > TabBar {
        background: #161b22;
        border-bottom: solid #30363d;
    }
    Tab {
        color: #8b949e;
    }
    Tab.-active {
        color: #58a6ff;
        text-style: bold;
    }
    /* Modal */
    DetailModal {
        align: center middle;
    }
    /* Error screen */
    ErrorScreen {
        align: center middle;
        background: rgba(0,0,0,0.85);
    }
    #error-container {
        width: 72;
        height: auto;
        background: #161b22;
        border: double #f85149;
        padding: 1 2;
    }
    #error-body {
        color: #c9d1d9;
    }
    #error-buttons {
        height: 3;
        margin-top: 1;
        align: center middle;
    }
    #error-buttons Button {
        margin: 0 1;
        width: 16;
    }
    /* Modal */
    #modal-container {
        width: 80%;
        height: 80%;
        background: #161b22;
        border: solid #58a6ff;
        padding: 1 2;
    }
    #modal-title {
        text-align: center;
        color: #58a6ff;
        text-style: bold;
        background: #21262d;
        margin-bottom: 1;
    }
    #modal-body {
        height: 1fr;
        color: #c9d1d9;
    }
    #modal-close {
        margin-top: 1;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("n", "next_ns", "Next NS"),
        Binding("p", "prev_ns", "Prev NS"),
        Binding("enter", "show_detail", "Detail"),
        Binding("1", "switch_tab('pods')", "Pods"),
        Binding("2", "switch_tab('services')", "Services"),
        Binding("3", "switch_tab('deployments')", "Deployments"),
        Binding("4", "switch_tab('ingress')", "Ingress"),
    ]

    TITLE = "⎈  LazyKube"
    SUB_TITLE = "Kubernetes Terminal UI"

    namespaces: reactive[list] = reactive([])
    ns_index:   reactive[int]  = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header()
        yield NamespaceBar(id="ns-bar")
        with Horizontal(id="main-layout"):
            with Vertical(id="sidebar"):
                yield ClusterStats(id="stats")
            with Vertical(id="content"):
                with TabbedContent(id="tabs"):
                    with TabPane("󰠳  Pods", id="pods"):
                        yield PodsTable(id="pods-table")
                    with TabPane("  Services", id="services"):
                        yield ServicesTable(id="services-table")
                    with TabPane("  Deployments", id="deployments"):
                        yield DeploymentsTable(id="deployments-table")
                    with TabPane("  Ingress", id="ingress"):
                        yield IngressTable(id="ingress-table")
        yield Footer()

    def on_mount(self):
        if not K8S_OK:
            self.push_screen(ErrorScreen(K8S_ERR), self._on_error_dismiss)
        else:
            self.load_namespaces()

    def _on_error_dismiss(self, result):
        if result == "retry":
            # Re-attempt connection
            global K8S_OK, K8S_ERR, v1, apps, net
            try:
                from kubernetes import client, config as k8s_config
                k8s_config.load_kube_config()
                v1   = client.CoreV1Api()
                apps = client.AppsV1Api()
                net  = client.NetworkingV1Api()
                v1.list_namespace(_request_timeout=5)
                K8S_OK  = True
                K8S_ERR = None
                self.load_namespaces()
            except Exception as e:
                K8S_OK  = False
                K8S_ERR = str(e)
                self.push_screen(ErrorScreen(K8S_ERR), self._on_error_dismiss)

    @work(thread=True)
    def load_namespaces(self):
        if not K8S_OK:
            self.call_from_thread(self._set_namespaces, ["default"])
            return
        try:
            nss = [n.metadata.name for n in v1.list_namespace().items]
        except Exception:
            nss = ["default"]
        self.call_from_thread(self._set_namespaces, nss)

    def _set_namespaces(self, nss: list):
        self.namespaces = nss
        self.ns_index   = 0
        self._refresh_all()

    def _current_ns(self) -> str:
        if not self.namespaces:
            return "default"
        return self.namespaces[self.ns_index]

    def _refresh_all(self):
        ns = self._current_ns()
        self.query_one("#ns-bar", NamespaceBar).namespace = ns
        self.query_one("#pods-table",       PodsTable).load(ns)
        self.query_one("#services-table",   ServicesTable).load(ns)
        self.query_one("#deployments-table",DeploymentsTable).load(ns)
        self.query_one("#ingress-table",    IngressTable).load(ns)
        stats = self.query_one("#stats", ClusterStats)
        stats.update_stats(ns)

    def action_refresh(self):
        self._refresh_all()

    def action_next_ns(self):
        if self.namespaces:
            self.ns_index = (self.ns_index + 1) % len(self.namespaces)
            self._refresh_all()

    def action_prev_ns(self):
        if self.namespaces:
            self.ns_index = (self.ns_index - 1) % len(self.namespaces)
            self._refresh_all()

    def action_switch_tab(self, tab: str):
        self.query_one("#tabs", TabbedContent).active = tab

    def action_show_detail(self):
        tabs = self.query_one("#tabs", TabbedContent)
        active = tabs.active
        ns = self._current_ns()

        table_map = {
            "pods":        ("#pods-table",        self._pod_detail),
            "services":    ("#services-table",     self._svc_detail),
            "deployments": ("#deployments-table",  self._dep_detail),
            "ingress":     ("#ingress-table",       self._ing_detail),
        }
        if active not in table_map:
            return
        sel_id, detail_fn = table_map[active]
        table: DataTable = self.query_one(sel_id)
        if table.cursor_row < 0:
            return
        row = table.get_row_at(table.cursor_row)
        name = str(row[0])  # first col is always name
        content = detail_fn(ns, name)
        self.push_screen(DetailModal(f"{active.upper()}  {name}", content))

    # ── detail fetchers ────────────────────────────────────────────────────────
    def _pod_detail(self, ns: str, name: str) -> str:
        try:
            p  = v1.read_namespaced_pod(name, ns)
            cs = p.status.container_statuses or []
            lines = [
                f"[bold cyan]Name:[/]       {p.metadata.name}",
                f"[bold cyan]Namespace:[/]  {p.metadata.namespace}",
                f"[bold cyan]Node:[/]       {p.spec.node_name}",
                f"[bold cyan]IP:[/]         {p.status.pod_ip}",
                f"[bold cyan]Phase:[/]      {p.status.phase}",
                f"[bold cyan]Created:[/]    {p.metadata.creation_timestamp}",
                "",
                "[bold yellow]Containers:[/]",
            ]
            for c in p.spec.containers:
                st = next((x for x in cs if x.name == c.name), None)
                ready = "[green]✓[/]" if st and st.ready else "[red]✗[/]"
                restarts = st.restart_count if st else 0
                lines.append(f"  {ready} [bold]{c.name}[/]  image={c.image}  restarts={restarts}")
            lines += ["", "[bold yellow]Labels:[/]"]
            for k, v_ in (p.metadata.labels or {}).items():
                lines.append(f"  [dim]{k}[/] = {v_}")
            return "\n".join(lines)
        except Exception as e:
            return f"[red]Error: {e}[/]"

    def _svc_detail(self, ns: str, name: str) -> str:
        try:
            s = v1.read_namespaced_service(name, ns)
            ports = "\n".join(
                f"  {p.name or '—'}  {p.port}→{p.target_port}/{p.protocol}"
                for p in (s.spec.ports or [])
            )
            lines = [
                f"[bold cyan]Name:[/]       {s.metadata.name}",
                f"[bold cyan]Namespace:[/]  {s.metadata.namespace}",
                f"[bold cyan]Type:[/]       {s.spec.type}",
                f"[bold cyan]ClusterIP:[/]  {s.spec.cluster_ip}",
                f"[bold cyan]Created:[/]    {s.metadata.creation_timestamp}",
                "",
                "[bold yellow]Ports:[/]",
                ports,
                "",
                "[bold yellow]Selector:[/]",
            ]
            for k, v_ in (s.spec.selector or {}).items():
                lines.append(f"  [dim]{k}[/] = {v_}")
            return "\n".join(lines)
        except Exception as e:
            return f"[red]Error: {e}[/]"

    def _dep_detail(self, ns: str, name: str) -> str:
        try:
            d = apps.read_namespaced_deployment(name, ns)
            s = d.status
            lines = [
                f"[bold cyan]Name:[/]         {d.metadata.name}",
                f"[bold cyan]Namespace:[/]    {d.metadata.namespace}",
                f"[bold cyan]Replicas:[/]     {d.spec.replicas}",
                f"[bold cyan]Ready:[/]        {s.ready_replicas or 0}",
                f"[bold cyan]Available:[/]    {s.available_replicas or 0}",
                f"[bold cyan]Strategy:[/]     {d.spec.strategy.type}",
                f"[bold cyan]Created:[/]      {d.metadata.creation_timestamp}",
                "",
                "[bold yellow]Containers:[/]",
            ]
            for c in d.spec.template.spec.containers:
                lines.append(f"  [bold]{c.name}[/]  image={c.image}")
            lines += ["", "[bold yellow]Labels:[/]"]
            for k, v_ in (d.metadata.labels or {}).items():
                lines.append(f"  [dim]{k}[/] = {v_}")
            return "\n".join(lines)
        except Exception as e:
            return f"[red]Error: {e}[/]"

    def _ing_detail(self, ns: str, name: str) -> str:
        try:
            i = net.read_namespaced_ingress(name, ns)
            lines = [
                f"[bold cyan]Name:[/]       {i.metadata.name}",
                f"[bold cyan]Namespace:[/]  {i.metadata.namespace}",
                f"[bold cyan]Class:[/]      {i.spec.ingress_class_name or '—'}",
                f"[bold cyan]Created:[/]    {i.metadata.creation_timestamp}",
                "",
                "[bold yellow]Rules:[/]",
            ]
            for r in (i.spec.rules or []):
                lines.append(f"  [bold]{r.host or '*'}[/]")
                if r.http:
                    for path in r.http.paths:
                        svc  = path.backend.service
                        lines.append(f"    {path.path}  →  {svc.name}:{svc.port.number}")
            if i.spec.tls:
                lines += ["", "[bold yellow]TLS:[/]"]
                for t in i.spec.tls:
                    lines.append(f"  secret={t.secret_name}  hosts={', '.join(t.hosts or [])}")
            return "\n".join(lines)
        except Exception as e:
            return f"[red]Error: {e}[/]"


def main():
    app = LazyKube()
    app.run()

if __name__ == "__main__":
    main()
