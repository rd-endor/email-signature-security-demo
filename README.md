# ✉️ Email Signature Studio

A full-stack email signature generator featuring a **Node.js (React + Vite + Tailwind CSS)** frontend, a **Python (FastAPI + SQLite)** backend, user authentication, credit card tokenization & vault, live multi-template rendering, and 1-click rich-text export for Gmail, Apple Mail, and Outlook.

---

## 🌟 Key Features

- **🎨 Multi-Template Email Signature Engine**:
  - *Modern Horizon*: Sleek horizontal layout with accent bar, headshot, logo, and inline social badges.
  - *Corporate Classic*: High-compatibility 2-column layout with vertical divider.
  - *Minimalist Clean*: Text-focused, clean typography for everyday emails.
  - *Branded Card*: Framed card format with header logo and call-to-action button.
  - *Compact Pro*: Single-line compact style optimized for mobile reply chains.
- **🔐 User Authentication & Strong Passwords**:
  - Username & password sign-up and sign-in with PBKDF2 cryptographic hashing and JWT session tokens.
  - Enforced strong password policy (8+ chars, uppercase, lowercase, numbers, special characters) with real-time UI strength meter.
  - Built-in Nginx reverse-proxy rate limiting (20 req/sec API, 10 req/min auth endpoints) with HTTP 429 throttling to protect against automated credential stuffing and DoS bots.
  - Hard limit of 100 total user accounts enforced on the signup endpoint for demo isolation.
- **💳 Credit Card Tokenization & Vault**:
  - PCI DSS-compliant tokenization vault (`tok_<brand>_<hash>`).
  - Card number Luhn algorithm validation & brand detection (Visa, Mastercard, Amex, Discover).
  - Safe masked storage (only token, brand, expiry, and `last4` are stored).
- **💾 Cloud/Database Persistence**:
  - Save, edit, duplicate, browse, and delete custom signatures backed by **SQLite** via SQLAlchemy.
- **🖼️ Logo & Branding Integration**:
  - Preloaded repository assets (`endor-labs-logo-2.png`, `endor-labs-logo-ss.png`).
  - Custom logo and avatar upload capability.
- **📋 1-Click Export**:
  - **Copy Rich Signature**: Direct rich-text clipboard copy for instant pasting into Gmail, Outlook, or Apple Mail.
  - **Copy Raw HTML**: For CMS or email tool templates.
  - **Download HTML File**: Standalone `.html` file export.
- **📱 Live Simulated Email Client**:
  - Real-time preview with Gmail and Outlook mock composer windows, plus desktop/mobile view toggle.

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── Dockerfile           # Backend container definition
│   ├── auth.py              # PBKDF2 password hashing & JWT token handling
│   ├── database.py          # SQLite engine & session setup
│   ├── main.py              # FastAPI app, CORS, routes & static mounts
│   ├── models.py            # SQLAlchemy models (User, Signature, PaymentMethod)
│   ├── requirements.txt     # Python backend dependencies
│   ├── schemas.py           # Pydantic request/response models & password rules
│   ├── static/              # Served static files (logos & user uploads)
│   ├── test_api.py          # Automated API test suite
│   └── tokenization.py      # Luhn check, card brand detector & token vault
├── frontend/
│   ├── Dockerfile           # Multi-stage frontend container (Node build -> Nginx)
│   ├── nginx.conf           # Nginx reverse proxy configuration
│   ├── index.html           # HTML entry point
│   ├── package.json         # Node.js dependencies (React, Vite, Tailwind)
│   ├── vite.config.js       # Vite configuration with API proxy
│   └── src/
│       ├── api/             # Axios API client (Auth, Signatures, Payments, Logos)
│       ├── components/      # UI components (Header, BillingModal, Auth, Preview)
│       ├── context/         # AuthContext state management
│       ├── templates/       # Bulletproof HTML signature generators
│       └── types/           # Template definitions & color palettes
├── docker-compose.yml       # Multi-container orchestration (Backend + Frontend)
├── deploy-gke.sh            # GKE automated build, push & deployment script
├── endor-labs-logo-2.png    # Logo asset
├── endor-labs-logo-ss.png   # Square/Compact logo asset
├── k8s/
│   ├── app.yaml             # Kubernetes Namespace, Deployments & Services
│   └── network-policy.yaml  # GCP IMDS & Cloud Metadata isolation NetworkPolicy
├── start.sh                 # One-click start script for local dev
└── README.md
```

---

## 🚀 Quick Start

### 1. Docker Compose (Recommended for Containers)

Spin up both containerized services with Docker Compose:

```bash
docker compose up --build
```

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Launch with `start.sh` (Local Development)

Run the convenient local start script:

```bash
./start.sh
```

- **Frontend Application**: [http://localhost:3000](http://localhost:3000)
- **Backend API & Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 3. Manual Setup & Running

#### Backend (Python + FastAPI + SQLite)

```bash
cd backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Frontend (Node.js + React + Vite)

```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Running Tests

To run the automated backend test suite:

```bash
PYTHONPATH=backend ./backend/venv/bin/pytest backend/test_api.py -v
```

To run the frontend production build test:

```bash
cd frontend && npm run build
```

---

---

## ☁️ GKE Deployment & Upwind Integration

This application is designed for cloud-native deployment to Google Kubernetes Engine (GKE) and integration with **Upwind Security** for runtime threat detection, reachability analysis, and workload protection.

### 1. Cluster Information

| Parameter | Value |
| :--- | :--- |
| **Cluster Name** | `upwind-integ-vuln-app-cluster-rd` |
| **GCP Project** | `endor-experiments` |
| **Zone / Region** | `us-central1-a` (`us-central1`) |
| **Kubernetes Namespace** | `signature-demo` |
| **Workload Label** | `demo: upwind-endor-runtime` |

---

### 2. Connect to GKE Cluster

Authenticate `gcloud` and configure your `kubectl` context:

```bash
# Get cluster credentials
gcloud container clusters get-credentials upwind-integ-vuln-app-cluster-rd \
    --zone=us-central1-a \
    --project=endor-experiments

# Verify cluster connection
kubectl get nodes
```

---

### 3. Build & Deploy to GKE

You can deploy using Google Artifact Registry (`endor-experiments/demo-repository`) or GitHub Container Registry:

```bash
# 1. Configure Docker authentication for Google Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet

# 2. Deploy privately without public internet exposure (default)
INTERNET_EXPOSURE=false ./deploy-gke.sh

# Or deploy with a public LoadBalancer IP:
# INTERNET_EXPOSURE=true ./deploy-gke.sh
```

---

### 4. Upwind Runtime Integration & Monitoring

The Kubernetes manifests in [`k8s/app.yaml`](file:///Users/rdhakne/Documents/rd/git/catch-all-repos/email-signature-security-demo/k8s/app.yaml) are annotated with security labels to facilitate Upwind sensor discovery and runtime tracking:

- **Namespace**: `signature-demo`
- **Workload Labels**: `demo: upwind-endor-runtime`, `tier: backend`, `tier: frontend`
- **Endpoints & Exposure**:
  - `frontend-service`: Configurable via `INTERNET_EXPOSURE=false` (`ClusterIP`, default) or `INTERNET_EXPOSURE=true` (`LoadBalancer`).
  - `backend`: Internal `ClusterIP` exposing FastAPI endpoints on port `8000`.

#### Local Access (When Internet Exposure is Disabled)

```bash
# Port-forward frontend service to localhost
kubectl port-forward svc/frontend-service 8080:80 -n signature-demo

# Open http://localhost:8080 in your browser
```

#### Verify Deployment Status

```bash
# Check pod status
kubectl get pods -n signature-demo

# Check public load balancer IP
kubectl get svc frontend-service -n signature-demo
```

---

### 5. 🛡️ Security & Cloud Isolation (IMDS / Metadata Protection)

Because this demonstration application contains intentional vulnerability test vectors for runtime detection tools (such as Upwind), safeguards are established to prevent lateral movement or access to the underlying GCP project:

- **Network Policy Isolation ([`k8s/network-policy.yaml`](file:///Users/rdhakne/Documents/rd/git/catch-all-repos/email-signature-security-demo/k8s/network-policy.yaml))**:
  Blocks pods from reaching the Google Cloud Instance Metadata Service (IMDS) at `169.254.169.254` and the `169.254.0.0/16` link-local range.
  ```bash
  # Apply IMDS blocking NetworkPolicy
  kubectl apply -f k8s/network-policy.yaml
  ```
- **GKE Workload Identity**:
  Replaces default node compute credentials with the GKE Metadata Server (`GKE_METADATA`), rejecting any unauthorized token queries from within containers.
- **Least-Privilege Scopes**:
  Pods operate under default unprivileged Kubernetes service accounts with no GCP IAM permissions.

---

## 💡 How to Use the Generated Signatures

1. Customize your details (Name, Job Title, Department, Company, Social Profiles, Logo).
2. Choose your preferred template and brand colors in the **Design** tab.
3. In the live preview pane, click **"Copy Rich Signature"**.
4. Open your email client:
   - **Gmail**: Go to *Settings &rarr; See all settings &rarr; General &rarr; Signature*, click *Create new*, and press **Ctrl+V / Cmd+V**.
   - **Outlook**: Go to *Settings &rarr; Mail &rarr; Signatures*, click *New*, and paste into the editor.
   - **Apple Mail**: Go to *Mail &rarr; Settings &rarr; Signatures*, add a new signature, and paste.
5. Save your email client settings and you're ready to go!