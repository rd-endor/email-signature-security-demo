# CodeMender Setup & Reference Guide

This document records the complete setup, authentication, and operational guide for **CodeMender** (Google DeepMind's AI-powered autonomous security agent) configured under GCP project `endor-experiments`.

---

## 📌 Environment Details

| Property | Value / Path |
| :--- | :--- |
| **GCP Target Project** | `endor-experiments` |
| **User Account** | `rdhakne@endor.ai` |
| **ADC Quota Project** | `endor-solutions-eng` |
| **ADC Credentials File** | `~/.config/gcloud/application_default_credentials.json` |
| **CodeMender Version** | `0.12.0` |
| **CodeMender Config** | `~/.codemender/config.yaml` |

---

## 🛠️ Step-by-Step Setup Log

### Step 1: Configure gcloud Active Project
Set your `gcloud` CLI context to target the CodeMender experiment project:
```bash
gcloud config set project endor-experiments
```

### Step 2: Authenticate Application Default Credentials (ADC)
CodeMender requires local ADC to interact with backend Gemini Enterprise Agent Platform APIs on Google Cloud (`aiplatform.googleapis.com`):
```bash
gcloud auth application-default login
```

### Step 3: Resolve Quota Project Warning
During ADC setup, `gcloud` attempts to set `endor-experiments` as the billing/quota tracking project, which requires `serviceusage.services.use` permissions. To resolve this warning, route API quota tracking through `endor-solutions-eng`:
```bash
gcloud auth application-default set-quota-project endor-solutions-eng
```

### Step 4: CodeMender CLI (`cm`) Initialization
Initialize the local workspace configuration at `~/.codemender`:
```bash
cm init
```

Verify that all environment checks pass:
```bash
cm init --verify
```

---

## 🔍 Verification Status

Running `cm init --verify` confirms the following passing checks:

```text
🔍 CodeMender Environment Verification
───────────────────────────────────────────────────────
  ✅ Workspace directory    /Users/rdhakne/.codemender
  ✅ Config file            /Users/rdhakne/.codemender/config.yaml
  ✅ Config parsing         Config loaded successfully
  ✅ Server                 https://aiplatform.googleapis.com
  ✅ VCS type               git
───────────────────────────────────────────────────────
  Results: All critical checks passed!
```

---

## 💻 CodeMender CLI Command Reference

### Scanning & Patching
```bash
# Discover security vulnerabilities in the codebase
cm find

# Verify exploitability of findings
cm verify

# Generate and apply security fixes
cm fix
```

### Reporting & Import
```bash
# Query findings and export reports (HTML, JSON, SARIF)
cm report

# Import findings from external SAST tools
cm report import --file findings.json
```

### Session Management
```bash
# List active or previous sessions
cm session list

# Resume an interrupted session
cm session resume <session-id>
```

### Version Control & Utilities
```bash
# Show diff of changes made by CodeMender
cm vcs diff

# Reset workspace back to baseline state
cm vcs reset
```
