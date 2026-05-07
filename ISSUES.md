# Sample Issues for GitHub

Copy these to create issues on your GitHub repository.

---

## Issue 1: Add ConfigMaps and Secrets View

**Title:** Feature: Add ConfigMaps and Secrets tabs

**Description:**
Add support for viewing ConfigMaps and Secrets in the TUI.

**Proposed Implementation:**
- Add new tabs for ConfigMaps and Secrets
- Display key count, namespace, and age
- Add keybinding to view details (similar to describe)
- Mask secret values by default with option to reveal

**Labels:** enhancement, good first issue

---

## Issue 2: Improve Windows Performance

**Title:** Bug: Slow refresh on Windows

**Description:**
On Windows, the refresh rate is noticeably slower compared to Linux/macOS. This affects the user experience when monitoring real-time cluster changes.

**Steps to Reproduce:**
1. Run lazyk8s on Windows
2. Press 'r' to refresh
3. Notice delay compared to Linux

**Expected:** Refresh should be near-instant
**Actual:** 2-3 second delay

**Labels:** bug, windows, performance

---

## Issue 3: Add Namespace Filtering

**Title:** Feature: Filter resources by multiple namespaces

**Description:**
Currently, users can cycle through namespaces one at a time. It would be helpful to:
- Select multiple namespaces to view simultaneously
- Add "all namespaces" option
- Remember last selected namespace(s)

**Labels:** enhancement

---

## Issue 4: Export Resource Details

**Title:** Feature: Export resource details to file

**Description:**
Add ability to export the current view or resource details to a file for sharing or documentation.

**Proposed:**
- Add keybinding (e.g., 'x' for export)
- Support JSON and YAML formats
- Save to current directory with timestamp

**Labels:** enhancement, good first issue

---

## Issue 5: Add Resource Metrics Graph

**Title:** Feature: Visual CPU/Memory usage graphs

**Description:**
Enhance the resource usage view with visual graphs showing CPU and memory trends over time.

**Requirements:**
- Use textual's plotting capabilities
- Show last 5-10 minutes of data
- Color-code by threshold (green/yellow/red)

**Labels:** enhancement, visualization

---

## Issue 6: Improve Error Messages

**Title:** Enhancement: Better error handling and messages

**Description:**
When kubectl commands fail or cluster is unreachable, provide clearer error messages and recovery suggestions.

**Examples:**
- "Cluster unreachable" → "Cannot connect to cluster. Check if kubectl is configured: kubectl cluster-info"
- "Permission denied" → "Insufficient permissions. You may need RBAC access to view this resource."

**Labels:** enhancement, documentation, good first issue

---

**Instructions:**
1. Go to https://github.com/Gowthamhegde/lazyk8s/issues
2. Click "New Issue"
3. Copy the title and description from above
4. Add the suggested labels
5. Submit the issue
