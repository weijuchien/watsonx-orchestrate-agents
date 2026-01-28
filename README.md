# IBM watsonx Orchestrate – Python Quick Start

This guide walks you through installing the **Agent Development Kit (ADK)** for **the AI Governance Project**, setting up your development environment, and using Orchestrate from Python.

---

## Prerequisites

Before you start, make sure you have:

- **Python 3.11 ~ 3.13**
- Access to an **IBM watsonx Orchestrate** tenant (Developer Edition or SaaS)

---

## 1. Install the Orchestrate ADK

The ADK is distributed as a Python package and includes both:
- A Python SDK
- A command-line interface (CLI)

Install it using `pip`:

```bash
pip install ibm-watsonx-orchestrate-adk
```

---

## 2. Start production environment

For **remote (production)** watsonx Orchestrate hosted on IBM Cloud, AWS, or on-premises, add an environment and activate it so CLI commands target that instance.

### 2.1 Add the production environment

```bash
orchestrate env add -n <environment-name> -u <your-instance-url>
```

- `<environment-name>`: Any name you prefer for this environment.
- `<your-instance-url>`: Your watsonx Orchestrate service instance URL (see [Getting credentials for your environments](https://developer.watson-orchestrate.ibm.com/environment/initiate_environment)).

Optional: activate right after adding with `--activate`:

```bash
orchestrate env add -n <environment-name> -u <your-instance-url> --activate
```

### 2.2 Activate the production environment

Activate to authenticate and point all commands (except `orchestrate server` and `orchestrate chat`) at that environment.

**Interactive (prompt for API key):**

```bash
orchestrate env activate <environment-name>
# When prompted: Please enter WXO API key: <your-api-key>
```

**Non-interactive (e.g. for scripts):**

```bash
orchestrate env activate <environment-name> --api-key <your-api-key>
```

> **Note:** Remote environment authentication expires every 2 hours. Run `orchestrate env activate` again after it expires.

### 2.3 Check and manage environments

List environments (the active one is marked `(active)`):

```bash
orchestrate env list
```

Remove an environment:

```bash
orchestrate env remove -n <environment-name>
```

---

**Reference:** [Configure access to remote environments](https://developer.watson-orchestrate.ibm.com/environment/initiate_environment)

