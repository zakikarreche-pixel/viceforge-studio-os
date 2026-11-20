# ViceForge Studio OS — AAA Video Game Studio Production & Release Management System

**University of Boumerdes (UMBB)** — Faculty of Science, Department of Computer Science  
**Course:** Information System (L2, Sem. 3) | **Instructor:** Dr. Benzenati  
**Academic Year:** 2026–2027

## Project Overview
A desktop Information System prototype built with **Python (Tkinter)** and **SQLite** to digitize AAA game production tracking, enforce direct and indirect data validation controls, automate developer labor cost calculations, and evaluate deterministic release readiness certification.

## Repository Contents
* `viceforge_studio.py` — Complete desktop GUI prototype (Executive Dashboard, Tasks & Labor Cost Tracker, QA Bug Triage).
* `schema.sql` — Relational database schema (`GameProject`, `Developer`, `Milestone`, `Task`, `BugReport`) and automated KPI view (`v_ProjectKPIs`).

## How to Run Locally
Requires **Python 3** (uses only the Python standard library — no external packages needed):

```bash
python viceforge_studio.py
