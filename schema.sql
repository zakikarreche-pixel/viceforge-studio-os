PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS GameProject (
    ProjectID         TEXT PRIMARY KEY,
    Title             TEXT NOT NULL,
    Genre             TEXT NOT NULL,
    TotalBudget       REAL NOT NULL CHECK (TotalBudget > 0),
    TargetReleaseDate TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Developer (
    DevID      TEXT PRIMARY KEY,
    Name       TEXT NOT NULL,
    Role       TEXT NOT NULL,
    HourlyRate REAL NOT NULL CHECK (HourlyRate BETWEEN 15 AND 400)
);

CREATE TABLE IF NOT EXISTS Milestone (
    MilestoneID TEXT PRIMARY KEY,
    PhaseName   TEXT NOT NULL,
    DueDate     TEXT NOT NULL,
    Status      TEXT NOT NULL CHECK (Status IN ('Planned', 'Active', 'Completed', 'Delayed')),
    ProjectID   TEXT NOT NULL,
    FOREIGN KEY (ProjectID) REFERENCES GameProject(ProjectID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Task (
    TaskID      TEXT PRIMARY KEY,
    Title       TEXT NOT NULL,
    HoursLogged REAL NOT NULL DEFAULT 0 CHECK (HoursLogged >= 0 AND HoursLogged <= 2000),
    Priority    TEXT NOT NULL CHECK (Priority IN ('Low', 'Medium', 'High', 'Urgent')),
    Status      TEXT NOT NULL CHECK (Status IN ('To Do', 'In Progress', 'Completed', 'Blocked')),
    MilestoneID TEXT NOT NULL,
    DevID       TEXT NOT NULL,
    FOREIGN KEY (MilestoneID) REFERENCES Milestone(MilestoneID) ON DELETE CASCADE,
    FOREIGN KEY (DevID)       REFERENCES Developer(DevID)       ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS BugReport (
    BugID        TEXT PRIMARY KEY,
    Severity     TEXT NOT NULL CHECK (Severity IN ('Critical', 'High', 'Medium', 'Low')),
    DateReported TEXT NOT NULL,
    Status       TEXT NOT NULL CHECK (Status IN ('Open', 'In Fix', 'Verified', 'Closed')),
    TaskID       TEXT NOT NULL,
    DevID        TEXT,
    FOREIGN KEY (TaskID) REFERENCES Task(TaskID)       ON DELETE CASCADE,
    FOREIGN KEY (DevID)  REFERENCES Developer(DevID)   ON DELETE SET NULL
);

-- Automated Labor Cost & Release Readiness View
CREATE VIEW IF NOT EXISTS v_ProjectKPIs AS
SELECT
    p.ProjectID,
    p.Title,
    p.TotalBudget,
    p.TargetReleaseDate,
    COALESCE((
        SELECT SUM(t.HoursLogged * d.HourlyRate)
        FROM Milestone m
        JOIN Task t ON t.MilestoneID = m.MilestoneID
        JOIN Developer d ON d.DevID = t.DevID
        WHERE m.ProjectID = p.ProjectID
    ), 0) AS TotalLaborCost,
    (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID WHERE m.ProjectID = p.ProjectID) AS TotalTasks,
    (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID WHERE m.ProjectID = p.ProjectID AND t.Status = 'Completed') AS DoneTasks,
    (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID JOIN BugReport b ON b.TaskID = t.TaskID WHERE m.ProjectID = p.ProjectID) AS TotalBugs,
    (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID JOIN BugReport b ON b.TaskID = t.TaskID WHERE m.ProjectID = p.ProjectID AND b.Status = 'Closed') AS ClosedBugs,
    (SELECT COUNT(*) FROM Milestone m JOIN Task t ON t.MilestoneID = m.MilestoneID JOIN BugReport b ON b.TaskID = t.TaskID WHERE m.ProjectID = p.ProjectID AND b.Severity = 'Critical' AND b.Status != 'Closed') AS OpenCriticalBugs
FROM GameProject p;
