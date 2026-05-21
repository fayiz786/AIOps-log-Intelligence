# AIOps Log Intelligence System

![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)

A comprehensive **AIOps (Artificial Intelligence for Operations)** log intelligence platform that automatically ingests log files, classifies errors using Large Language Models (LLM), and generates structured alert summaries with severity levels and intelligent remediation suggestions.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Output Examples](#output-examples)
- [API Integration](#api-integration)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The AIOps Log Intelligence System is designed to solve real-world operational challenges:

- **Log Volume Crisis**: Analyze thousands of log entries automatically
- **Alert Fatigue**: Intelligent classification reduces noise with severity-based prioritization
- **Context Loss**: Rich structured alerts with remediation suggestions
- **Manual Effort**: Automated LLM-powered error analysis with intelligent fallbacks

Perfect for:
- DevOps teams managing microservices
- SRE platforms requiring intelligent monitoring
- Incident response automation
- Log aggregation pipelines (ELK, Splunk integration)

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Multi-Provider LLM** | Supports Claude (Anthropic) & GPT-4o (OpenAI) with auto-fallback |
| **Smart Classification** | 5-tier severity system: CRITICAL, HIGH, MEDIUM, LOW, INFO |
| **Intelligent Fallback** | Rule-based pattern matching when LLM unavailable |
| **Structured Output** | Color-coded terminal tables + JSON export |
| **Log Parsing** | Flexible format: `timestamp \| level \| service \| message \| [error_code]` |
| **Error Remediation** | Context-aware fix suggestions for each alert |
| **Summary Statistics** | Severity breakdown and alert analytics |
| **Real-time Analysis** | Stream processing capability |

### Security & Performance

- ✅ No log data sent to 3rd parties (LLM classification only)
- ✅ Graceful API error handling with automatic fallback
- ✅ Efficient pattern matching with compiled regex
- ✅ Type hints throughout for IDE support
- ✅ Production-grade error handling

## 🏗️ Architecture
┌─────────────────┐ │ Log Source │ │ (Files/API) │ └────────┬────────┘ │ 
▼ ┌─────────────────────────────┐ │ LogAnalyzer.parse_logs() │ │ (Parse & Normalize) │ └────────┬────────────────────┘ │
▼ ┌────────────┐ │ LLM API │ ◄─── Optional (with fallback) │ Available? │ └──┬────┬───┘ │ 
│ YES│ │NO ▼ ▼ ┌────────────────┐ │ classify │ │ with_api() │ └────┬───────────┘ │ 
▼ ┌─────────────────────────────┐ │ AlertSummary Objects │ │ (Structured Output) │ └────────┬────────────────────┘ │
┌───┴────┐ ▼ ▼ ┌──────┐ ┌──────────┐ │Table │ │JSON File │ │Output│ │Export │ └──────┘ └──────────┘

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Basic Installation (Rule-based only)

```bash
# Clone the repository
git clone https://github.com/fayiz786/AIOps-log-Intelligence.git
cd AIOps-log-Intelligence

# No additional dependencies required for rule-based classification
python aiops_log_analyzer.py

## With LLM Support (Recommended)
Option 1: Using Claude (Anthropic)
# Install Anthropic SDK
pip install anthropic

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the analyzer
python aiops_log_analyzer.py
