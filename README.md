# ⎈ lazyk8s

A stylish, interactive Kubernetes TUI — see everything in your cluster without running individual `kubectl` commands.

![lazyk8s demo](https://raw.githubusercontent.com/Gowthamhegde/lazyk8s/main/demo.png)

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/Gowthamhegde/lazyk8s/main/install.sh | bash
```

Then run:

```bash
lazyk8s
```

## Requirements

- `python3`
- `kubectl` (configured and pointing at a cluster)
- Works with **minikube**, **kind**, **EKS**, **GKE**, **AKS** — any kubectl context

## Features

| Tab | What you see |
|---|---|
| 📦 Pods | Status, restarts, age, node — color-coded |
| 🖥 Nodes | Status, version, IP |
| 🚀 Deployments | Ready ratio, availability |
| 🌐 Services | Type color-coded (LoadBalancer / NodePort / ClusterIP) |
| 🔗 Contexts | All kubectl contexts, active one highlighted |
| ⚡ Events | Sorted by time, warnings in red |

## Keybindings

| Key | Action |
|---|---|
| `l` | View logs for selected pod |
| `d` | Describe selected resource |
| `c` | Switch kubectl context |
| `n` | Cycle namespaces |
| `e` | Jump to Events tab |
| `t` | Resource usage (`kubectl top`) |
| `/` | Live search / filter |
| `r` | Refresh |
| `q` | Quit |

## Uninstall

```bash
rm ~/.local/bin/lazyk8s
```
