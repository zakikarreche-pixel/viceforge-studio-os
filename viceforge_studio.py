import sqlite3
import re
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# GTA 6 VICE CITY NEON SUNSET THEME PALETTE
# ==========================================
BG_DARK = "#0D0620"       # Leonida Midnight
BG_CARD = "#1B1035"       # Palm Dusk Surface
BG_INPUT = "#26174A"      # Deep Violet Input
NEON_PINK = "#FF2A85"     # Vice Magenta
NEON_CYAN = "#00F0FF"     # Ocean Cyan
SUNSET_GOLD = "#FF9E00"   # Miami Sunset Gold
TEXT_LIGHT = "#F2ECFF"    # Crisp Lavender White
TEXT_MUTED = "#A99BC8"    # Soft Muted Violet
SUCCESS_GREEN = "#00E676" # Cert Approved Green

DB_NAME = "viceforge_studio.db"


class StudioDatabase:
    def __init__(self, db_path=DB_NAME):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.create_schema()
        self.seed_if_empty()

    def create_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS GameProject (
                ProjectID TEXT PRIMARY KEY,
                Title TEXT NOT NULL,
                Genre TEXT NOT NULL,
                TotalBudget REAL NOT NULL CHECK (TotalBudget > 0),
                TargetReleaseDate TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Developer (
                DevID TEXT PRIMARY KEY,
                Name TEXT NOT NULL,
                Role TEXT NOT NULL,
                HourlyRate REAL NOT NULL CHECK (HourlyRate BETWEEN 15 AND 400)
            );
            CREATE TABLE IF NOT EXISTS Milestone (
                MilestoneID TEXT PRIMARY KEY,
                PhaseName TEXT NOT NULL,
                DueDate TEXT NOT NULL,
                Status TEXT NOT NULL CHECK (Status IN ('Planned', 'Active', 'Completed', 'Delayed')),
                ProjectID TEXT NOT NULL,
                FOREIGN KEY (ProjectID) REFERENCES GameProject(ProjectID) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS Task (
                TaskID TEXT PRIMARY KEY,
                Title TEXT NOT NULL,
                HoursLogged REAL NOT NULL DEFAULT 0 CHECK (HoursLogged >= 0 AND HoursLogged <= 2000),
                Priority TEXT NOT NULL CHECK (Priority IN ('Low', 'Medium', 'High', 'Urgent')),
                Status TEXT NOT NULL CHECK (Status IN ('To Do', 'In Progress', 'Completed', 'Blocked')),
                MilestoneID TEXT NOT NULL,
                DevID TEXT NOT NULL,
                FOREIGN KEY (MilestoneID) REFERENCES Milestone(MilestoneID) ON DELETE CASCADE,
                FOREIGN KEY (DevID) REFERENCES Developer(DevID) ON DELETE RESTRICT
            );
            CREATE TABLE IF NOT EXISTS BugReport (
                BugID TEXT PRIMARY KEY,
                Severity TEXT NOT NULL CHECK (Severity IN ('Critical', 'High', 'Medium', 'Low')),
                DateReported TEXT NOT NULL,
                Status TEXT NOT NULL CHECK (Status IN ('Open', 'In Fix', 'Verified', 'Closed')),
                TaskID TEXT NOT NULL,
                DevID TEXT,
                FOREIGN KEY (TaskID) REFERENCES Task(TaskID) ON DELETE CASCADE,
                FOREIGN KEY (DevID) REFERENCES Developer(DevID) ON DELETE SET NULL
            );
        """)
        self.conn.commit()

    def seed_if_empty(self):
        cur = self.conn.cursor()
        if cur.execute("SELECT COUNT(*) FROM GameProject").fetchone()[0] > 0:
            return
        cur.executemany("INSERT INTO GameProject VALUES (?, ?, ?, ?, ?)", [
            ("PRJ-26-001", "Project Leonida (GTA VI Scale)", "Open-World", 250000.00, "2027-05-26"),
            ("PRJ-26-002", "Vice Drift Online", "Racing", 85000.00, "2026-12-15"),
        ])
        cur.executemany("INSERT INTO Developer VALUES (?, ?, ?, ?)", [
            ("DEV-ENG-001", "Karim Benali", "Lead Dev", 120.00),
            ("DEV-ART-002", "Lina Mansouri", "3D Artist", 85.00),
            ("DEV-ENG-003", "Yacine Toumi", "Programmer", 95.00),
            ("DEV-QAT-004", "Amine Khelifi", "QA Tester", 55.00),
        ])
        cur.executemany("INSERT INTO Milestone VALUES (?, ?, ?, ?, ?)", [
            ("MLS-001-2", "Alpha", "2026-11-30", "Active", "PRJ-26-001"),
            ("MLS-001-3", "Beta", "2027-02-28", "Planned", "PRJ-26-001"),
            ("MLS-002-4", "Gold", "2026-12-01", "Completed", "PRJ-26-002"),
        ])
        cur.executemany("INSERT INTO Task VALUES (?, ?, ?, ?, ?, ?, ?)", [
            ("TSK-0001", "Dynamic Miami Weather & Volumetric Clouds", 180.0, "High", "Completed", "MLS-001-2", "DEV-ENG-001"),
            ("TSK-0002", "Vice Beach Neon Strip 3D Assets", 240.0, "High", "Completed", "MLS-001-2", "DEV-ART-002"),
            ("TSK-0003", "NPC Traffic AI Pathfinding Engine", 150.0, "Urgent", "In Progress", "MLS-001-2", "DEV-ENG-003"),
            ("TSK-0004", "Multiplayer Lobby Sync & Matchmaking", 320.0, "Urgent", "Completed", "MLS-002-4", "DEV-ENG-001"),
            ("TSK-0005", "Arcade Drift Physics Tuning", 140.0, "Medium", "Completed", "MLS-002-4", "DEV-ENG-003"),
        ])
        cur.executemany("INSERT INTO BugReport VALUES (?, ?, ?, ?, ?, ?)", [
            ("BUG-C-0001", "Critical", "2026-11-10", "Open", "TSK-0003", "DEV-ENG-003"),
            ("BUG-H-0002", "High", "2026-11-12", "In Fix", "TSK-0002", "DEV-ART-002"),
            ("BUG-M-0003", "Medium", "2026-11-14", "Closed", "TSK-0001", "DEV-ENG-001"),
            ("BUG-L-0004", "Low", "2026-11-15", "Closed", "TSK-0004", "DEV-ENG-001"),
        ])
        self.conn.commit()

    def get_project_kpis(self):
        query = """
            SELECT
                p.ProjectID, p.Title, p.TotalBudget, p.TargetReleaseDate,
                COALESCE((
                    SELECT SUM(t.HoursLogged * d.HourlyRate)
                    FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID
                    JOIN Developer d ON d.DevID = t.DevID WHERE m.ProjectID = p.ProjectID
                ), 0),
                (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID WHERE m.ProjectID = p.ProjectID),
                (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID WHERE m.ProjectID = p.ProjectID AND t.Status = 'Completed'),
                (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID JOIN BugReport b ON b.TaskID = t.TaskID WHERE m.ProjectID = p.ProjectID),
                (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID JOIN BugReport b ON b.TaskID = t.TaskID WHERE m.ProjectID = p.ProjectID AND b.Status = 'Closed'),
                (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID JOIN BugReport b ON b.TaskID = t.TaskID WHERE m.ProjectID = p.ProjectID AND b.Severity = 'Critical' AND b.Status != 'Closed')
            FROM GameProject p
        """
        rows = []
        for r in self.conn.execute(query).fetchall():
            pid, title, budget, rel_date, labor, t_tot, t_done, b_tot, b_closed, crit_open = r
            task_ratio = (t_done / t_tot) if t_tot > 0 else 0.0
            bug_ratio = (b_closed / b_tot) if b_tot > 0 else 1.0
            readiness = round((0.6 * task_ratio + 0.4 * bug_ratio) * 100, 1)
            if crit_open > 0:
                readiness = min(readiness, 75.0)

            c1_tasks_done = (t_tot > 0 and t_done == t_tot)
            c2_zero_crit = (crit_open == 0)
            c3_in_budget = (labor <= budget)

            if not c1_tasks_done:
                verdict = "R4: IN DEVELOPMENT"
            elif not c2_zero_crit:
                verdict = "R3: BLOCKED (CRITICAL BUGS)"
            elif not c3_in_budget:
                verdict = "R2: BUDGET ESCALATION"
            else:
                verdict = "R1: CERTIFIED GOLD READY"

            rows.append({
                "ProjectID": pid, "Title": title, "TotalBudget": budget,
                "ReleaseDate": rel_date, "LaborCost": labor,
                "BudgetRemaining": budget - labor, "Tasks": f"{t_done}/{t_tot}",
                "OpenCritical": crit_open, "Readiness": readiness, "Verdict": verdict
            })
        return rows


class ViceForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.db = StudioDatabase()
        self.title("VICEFORGE STUDIO OS — AAA Production & Release Management System")
        self.geometry("1180x720")
        self.configure(bg=BG_DARK)
        self.setup_styles()
        self.build_ui()
        self.refresh_all()

    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_MUTED,
                        padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", NEON_PINK)],
                  foreground=[("selected", "#FFFFFF")])
        style.configure("Treeview", background=BG_CARD, fieldbackground=BG_CARD,
                        foreground=TEXT_LIGHT, rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=BG_INPUT, foreground=NEON_CYAN,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", NEON_PINK)])

    def build_ui(self):
        header = tk.Frame(self, bg=BG_CARD, height=68, highlightbackground=NEON_PINK, highlightthickness=2)
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(header, text="VICEFORGE STUDIO OS", bg=BG_CARD, fg=NEON_PINK,
                 font=("Segoe UI", 18, "bold")).pack(side="left", padx=18, pady=12)
        tk.Label(header, text="AAA Production, Automated Labor Cost & Release Certification Engine",
                 bg=BG_CARD, fg=NEON_CYAN, font=("Segoe UI", 10, "italic")).pack(side="left", padx=8)
        tk.Button(header, text="Refresh KPIs", bg=SUNSET_GOLD, fg="#0D0620",
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=5,
                  command=self.refresh_all).pack(side="right", padx=18)

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=8)

        self.tab_dash = tk.Frame(self.tabs, bg=BG_DARK)
        self.tab_tasks = tk.Frame(self.tabs, bg=BG_DARK)
        self.tab_bugs = tk.Frame(self.tabs, bg=BG_DARK)

        self.tabs.add(self.tab_dash, text="  Executive Dashboard & Release Gate  ")
        self.tabs.add(self.tab_tasks, text="  Tasks & Labor Cost Tracker  ")
        self.tabs.add(self.tab_bugs, text="  QA Bug Triage & Patch Control  ")

        self.build_dashboard_tab()
        self.build_tasks_tab()
        self.build_bugs_tab()

    def make_kpi_card(self, parent, title, color):
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=color, highlightthickness=2, padx=14, pady=10)
        card.pack(side="left", fill="both", expand=True, padx=6)
        tk.Label(card, text=title, bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        val_lbl = tk.Label(card, text="--", bg=BG_CARD, fg=color, font=("Segoe UI", 16, "bold"))
        val_lbl.pack(anchor="w", pady=(4, 0))
        return val_lbl

    def build_dashboard_tab(self):
        kpi_row = tk.Frame(self.tab_dash, bg=BG_DARK)
        kpi_row.pack(fill="x", pady=10)
        self.lbl_budget = self.make_kpi_card(kpi_row, "TOTAL STUDIO BUDGET", NEON_CYAN)
        self.lbl_labor = self.make_kpi_card(kpi_row, "AUTOMATED LABOR COST", SUNSET_GOLD)
        self.lbl_crit = self.make_kpi_card(kpi_row, "OPEN CRITICAL BUGS", NEON_PINK)
        self.lbl_ready = self.make_kpi_card(kpi_row, "AVG RELEASE READINESS", SUCCESS_GREEN)

        tk.Label(self.tab_dash, text="ACTIVE AAA TITLES — AUTOMATED DECISION TABLE CERTIFICATION",
                 bg=BG_DARK, fg=NEON_CYAN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=6, pady=(10, 4))

        cols = ("ID", "Title", "Budget ($)", "Labor Cost ($)", "Remaining ($)", "Tasks", "Crit Bugs", "Readiness %", "Certification Verdict")
        self.tree_dash = ttk.Treeview(self.tab_dash, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree_dash.heading(c, text=c)
            self.tree_dash.column(c, width=118, anchor="center")
        self.tree_dash.column("Title", width=200, anchor="w")
        self.tree_dash.column("Certification Verdict", width=190, anchor="center")
        self.tree_dash.pack(fill="both", expand=True, padx=6, pady=6)

    def build_tasks_tab(self):
        search_bar = tk.Frame(self.tab_tasks, bg=BG_CARD, padx=10, pady=8)
        search_bar.pack(fill="x", padx=6, pady=6)
        tk.Label(search_bar, text="Search Tasks (ID / Title / Dev):", bg=BG_CARD, fg=NEON_CYAN,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.task_search_var = tk.StringVar()
        self.task_search_var.trace_add("write", lambda *_: self.refresh_tasks())
        tk.Entry(search_bar, textvariable=self.task_search_var, bg=BG_INPUT, fg=TEXT_LIGHT,
                 insertbackground=NEON_CYAN, width=35, relief="flat").pack(side="left", padx=10)

        cols = ("TaskID", "Title", "Milestone", "Developer", "Hours", "Rate ($/h)", "Labor Cost ($)", "Priority", "Status")
        self.tree_tasks = ttk.Treeview(self.tab_tasks, columns=cols, show="headings", height=11)
        for c in cols:
            self.tree_tasks.heading(c, text=c)
            self.tree_tasks.column(c, width=105, anchor="center")
        self.tree_tasks.column("Title", width=230, anchor="w")
        self.tree_tasks.pack(fill="both", expand=True, padx=6, pady=4)

        form = tk.LabelFrame(self.tab_tasks, text=" Log New Development Task (Auto-Calculates Labor Cost) ",
                             bg=BG_CARD, fg=SUNSET_GOLD, font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=6, pady=6)

        self.e_tid = self._entry(form, "TaskID (TSK-NNNN):", 0, 0, "TSK-0006")
        self.e_ttitle = self._entry(form, "Task Title:", 0, 2, "")
        self.e_thours = self._entry(form, "Hours Logged:", 0, 4, "40")
        self.e_tmls = self._entry(form, "MilestoneID:", 1, 0, "MLS-001-2")
        self.e_tdev = self._entry(form, "DevID:", 1, 2, "DEV-ENG-001")
        self.cb_tstatus = ttk.Combobox(form, values=["To Do", "In Progress", "Completed", "Blocked"], width=15, state="readonly")
        self.cb_tstatus.set("In Progress")
        tk.Label(form, text="Status:", bg=BG_CARD, fg=TEXT_LIGHT).grid(row=1, column=4, sticky="e", padx=4)
        self.cb_tstatus.grid(row=1, column=5, padx=4, pady=4)

        tk.Button(form, text="+ Save Task", bg=NEON_PINK, fg="#FFFFFF", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=14, pady=5, command=self.add_task).grid(row=1, column=6, padx=10)

    def build_bugs_tab(self):
        search_bar = tk.Frame(self.tab_bugs, bg=BG_CARD, padx=10, pady=8)
        search_bar.pack(fill="x", padx=6, pady=6)
        tk.Label(search_bar, text="Filter Bugs (ID / Severity / Status):", bg=BG_CARD, fg=NEON_PINK,
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        self.bug_search_var = tk.StringVar()
        self.bug_search_var.trace_add("write", lambda *_: self.refresh_bugs())
        tk.Entry(search_bar, textvariable=self.bug_search_var, bg=BG_INPUT, fg=TEXT_LIGHT,
                 insertbackground=NEON_PINK, width=35, relief="flat").pack(side="left", padx=10)

        cols = ("BugID", "Severity", "DateReported", "Status", "TaskID", "Assigned Dev")
        self.tree_bugs = ttk.Treeview(self.tab_bugs, columns=cols, show="headings", height=11)
        for c in cols:
            self.tree_bugs.heading(c, text=c)
            self.tree_bugs.column(c, width=150, anchor="center")
        self.tree_bugs.pack(fill="both", expand=True, padx=6, pady=4)

        form = tk.LabelFrame(self.tab_bugs, text=" Report QA Bug (Internal Consistency Checked: BUG-[C/H/M/L]-NNNN) ",
                             bg=BG_CARD, fg=NEON_CYAN, font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        form.pack(fill="x", padx=6, pady=6)

        self.e_bid = self._entry(form, "BugID:", 0, 0, "BUG-C-0005")
        tk.Label(form, text="Severity:", bg=BG_CARD, fg=TEXT_LIGHT).grid(row=0, column=2, sticky="e", padx=4)
        self.cb_bsev = ttk.Combobox(form, values=["Critical", "High", "Medium", "Low"], width=14, state="readonly")
        self.cb_bsev.set("Critical")
        self.cb_bsev.grid(row=0, column=3, padx=4, pady=4)
        self.e_btask = self._entry(form, "TaskID:", 0, 4, "TSK-0003")
        self.e_bdev = self._entry(form, "Resolver DevID:", 1, 0, "DEV-ENG-003")

        tk.Button(form, text="+ Log Bug Report", bg=NEON_PINK, fg="#FFFFFF", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=14, pady=5, command=self.add_bug).grid(row=1, column=2, padx=10)
        tk.Button(form, text="Mark Selected Bug Closed", bg=SUCCESS_GREEN, fg="#0D0620",
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=5,
                  command=self.close_selected_bug).grid(row=1, column=4, columnspan=2, padx=10)

    def _entry(self, parent, label, r, c, default=""):
        tk.Label(parent, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9)).grid(row=r, column=c, sticky="e", padx=4, pady=4)
        e = tk.Entry(parent, bg=BG_INPUT, fg=TEXT_LIGHT, insertbackground=NEON_CYAN, width=18, relief="flat")
        e.insert(0, default)
        e.grid(row=r, column=c + 1, padx=4, pady=4)
        return e

    def add_task(self):
        tid = self.e_tid.get().strip().upper()
        title = self.e_ttitle.get().strip()
        mls = self.e_tmls.get().strip().upper()
        dev = self.e_tdev.get().strip().upper()
        status = self.cb_tstatus.get()

        if not re.match(r"^TSK-\d{4}$", tid):
            return messagebox.showerror("Format Control Error", "TaskID must follow structured code TSK-NNNN.")
        if not title:
            return messagebox.showerror("Presence Control Error", "Task Title cannot be empty.")
        try:
            hours = float(self.e_thours.get())
            if not (0 <= hours <= 2000):
                raise ValueError
        except ValueError:
            return messagebox.showerror("Range Control Error", "HoursLogged must be a number between 0 and 2000.")
        if hours > 1000:
            messagebox.showwarning("Plausibility Control Alert", "Logging > 1000 hours on a single task is unusual. Please verify.")

        try:
            self.db.conn.execute(
                "INSERT INTO Task VALUES (?, ?, ?, 'High', ?, ?, ?)",
                (tid, title, hours, status, mls, dev)
            )
            self.db.conn.commit()
            self.refresh_all()
            messagebox.showinfo("Success", f"Task {tid} saved & labor cost recalculated.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("External Consistency / Key Error", f"Database rejected entry:\n{e}")

    def add_bug(self):
        bid = self.e_bid.get().strip().upper()
        sev = self.cb_bsev.get()
        tid = self.e_btask.get().strip().upper()
        dev = self.e_bdev.get().strip().upper() or None

        if not re.match(r"^BUG-[CHML]-\d{4}$", bid):
            return messagebox.showerror("Format Control Error", "BugID must follow structured code BUG-[C/H/M/L]-NNNN.")
        if bid[4] != sev[0]:
            return messagebox.showerror(
                "Internal Consistency Error",
                f"Code prefix '{bid[4]}' in {bid} contradicts Severity '{sev}' (expected '{sev[0]}')."
            )

        try:
            self.db.conn.execute(
                "INSERT INTO BugReport VALUES (?, ?, ?, 'Open', ?, ?)",
                (bid, sev, date.today().isoformat(), tid, dev)
            )
            self.db.conn.commit()
            self.refresh_all()
            messagebox.showinfo("QA Logged", f"Bug {bid} logged. Release readiness updated.")
        except sqlite3.IntegrityError as e:
            messagebox.showerror("External Consistency Error", f"Database rejected entry:\n{e}")

    def close_selected_bug(self):
        sel = self.tree_bugs.selection()
        if not sel:
            return messagebox.showwarning("Selection Required", "Select a bug row to close.")
        bid = self.tree_bugs.item(sel[0])["values"][0]
        self.db.conn.execute("UPDATE BugReport SET Status = 'Closed' WHERE BugID = ?", (bid,))
        self.db.conn.commit()
        self.refresh_all()

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_tasks()
        self.refresh_bugs()

    def refresh_dashboard(self):
        self.tree_dash.delete(*self.tree_dash.get_children())
        kpis = self.db.get_project_kpis()
        tot_b = sum(k["TotalBudget"] for k in kpis)
        tot_l = sum(k["LaborCost"] for k in kpis)
        tot_c = sum(k["OpenCritical"] for k in kpis)
        avg_r = (sum(k["Readiness"] for k in kpis) / len(kpis)) if kpis else 0

        self.lbl_budget.config(text=f"${tot_b:,.2f}")
        self.lbl_labor.config(text=f"${tot_l:,.2f}")
        self.lbl_crit.config(text=str(tot_c))
        self.lbl_ready.config(text=f"{avg_r:.1f}%")

        for k in kpis:
            self.tree_dash.insert("", "end", values=(
                k["ProjectID"], k["Title"], f"${k['TotalBudget']:,.2f}",
                f"${k['LaborCost']:,.2f}", f"${k['BudgetRemaining']:,.2f}",
                k["Tasks"], k["OpenCritical"], f"{k['Readiness']}%", k["Verdict"]
            ))

    def refresh_tasks(self):
        self.tree_tasks.delete(*self.tree_tasks.get_children())
        q = f"%{self.task_search_var.get().strip()}%"
        rows = self.db.conn.execute("""
            SELECT t.TaskID, t.Title, t.MilestoneID, d.Name, t.HoursLogged,
                   d.HourlyRate, (t.HoursLogged * d.HourlyRate), t.Priority, t.Status
            FROM Task t JOIN Developer d ON t.DevID = d.DevID
            WHERE t.TaskID LIKE ? OR t.Title LIKE ? OR d.Name LIKE ?
            ORDER BY t.TaskID
        """, (q, q, q)).fetchall()
        for r in rows:
            self.tree_tasks.insert("", "end", values=(
                r[0], r[1], r[2], r[3], f"{r[4]:.1f}", f"${r[5]:.2f}", f"${r[6]:,.2f}", r[7], r[8]
            ))

    def refresh_bugs(self):
        self.tree_bugs.delete(*self.tree_bugs.get_children())
        q = f"%{self.bug_search_var.get().strip()}%"
        rows = self.db.conn.execute("""
            SELECT BugID, Severity, DateReported, Status, TaskID, COALESCE(DevID, 'Unassigned')
            FROM BugReport
            WHERE BugID LIKE ? OR Severity LIKE ? OR Status LIKE ?
            ORDER BY BugID
        """, (q, q, q)).fetchall()
        for r in rows:
            self.tree_bugs.insert("", "end", values=r)


if __name__ == "__main__":
    app = ViceForgeApp()
    app.mainloop()