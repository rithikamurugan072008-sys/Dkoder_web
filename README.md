# DKoder 2.0 — AI-Powered Coding, Learning & Placement Preparation Platform

> The Ultimate Placement LMS & Engineering Career Acceleration Suite

**DKoder 2.0** upgrades the original DKoder placement platform with **10 advanced enterprise modules**, powered by a robust Python/Django backend, isolated multi-language compiler sandboxes, real-time analytics, and AI mentoring — all while strictly preserving DKoder's signature **vibrant yellow (`#FCC419`) and deep purple (`#12052B`) brand identity** and dynamic micro-animations.

---

## 🎨 Brand Identity & Visual Design
- **Signature Colors Preserved**: Luxury deep purple backgrounds (`#12052B`, `#1E0D47`, `#240C52`) with high-energy radiant yellow accents (`#FCC419`, `#FFD84D`).
- **Dynamic Micro-Animations**:
  - Ambient floating background glowing orbs (`orb-purple`, `orb-yellow`).
  - Interactive recruiter marquee ticker.
  - Brutalist button press physics (`.btn-dk-yellow`, `.btn-dk-purple`).
  - Voice recording audio wave visualizer bars.
  - Confetti celebration bursts upon testcase acceptance.
  - Live typing indicators in AI Mentor and CodeLab terminal console.

---

## 🚀 The 10 Advanced Modules in DKoder 2.0

### 1. 🤖 DKoder AI Mentor
- **Purpose**: AI-powered personal placement tutor and code debugger.
- **Capabilities**: Line-by-line code explanation, runtime & compiler error diagnostics, algorithmic optimization hints, aptitude problem breakdown, and mock interview practice.
- **Dual Engine**: Pluggable AI Service supporting live **Google Gemini API** (`GEMINI_API_KEY`) or intelligent domain-specific development simulation engine.
- **Features**: Chat history persistence, code syntax highlighting, copy-code button, recommended prompt chips, and conversation clearing.

### 2. ⚡ DKoder CodeLab (Online Compiler Sandbox)
- **Supported Languages**: Python 3.12, JavaScript (Node/Browser), C, C++, Java, and isolated SQL.
- **Security & Isolation**: Isolated process sandboxing with execution timeouts (5s), memory guards, code size limits, and hidden test-case protection against malicious code.
- **Features**: Split problem-solving IDE, custom testcase inputs, live stdout/stderr console, real-time runtime memory & time measurement, automated grading, and confetti celebration on full acceptance.

### 3. 🗺️ My Placement Roadmap
- **Personalized Planning**: Generates customized prep schedules based on graduation year, target companies (Zoho, Amazon, TCS, Infosys), daily available hours, and department.
- **12 Comprehensive Tracks**: Programming fundamentals, DSA, Aptitude & Logical Reasoning, DBMS, OOP, OS, Computer Networks, SQL Queries, Technical Interviews, HR Prep, Resume Crafting, and Mock Assessments.
- **Interactive Checklist**: Real-time task completion toggle, milestone progress calculation (0–100%), and deadline tracking.

### 4. 📊 Smart Student Analytics
- **Live Dashboards**: Solved problems counter, accepted submissions, coding success rate (%), aptitude accuracy, current coding streak (e.g. 14 days), and roadmap milestones.
- **Interactive Charting**: Visualized using Chart.js with responsive time-range filters (Last 7 Days, 30 Days, 90 Days, All Time).
- **Zero Fake Data**: Real backend calculations with dedicated empty states for new learners.

### 5. 🎙️ DKoder Interview Studio (AI Mock Interviews)
- **Interview Formats**: Technical rounds, HR & Behavioral, Coding & Architecture, Quantitative Aptitude, and Company-Specific rounds (e.g. Zoho, Amazon).
- **Interactive Flow**: Multi-question progression with text responses and optional voice transcription with review before submission.
- **Comprehensive AI Evaluation**: Transparent scoring across Technical Correctness, Communication Structure, and Problem-Solving Approach with actionable recommendations.

### 6. 🏆 DKoder Arena (Live Coding Competitions)
- **Features**: Timed competitive programming contests with registration deadlines, countdown timers, live leaderboard podiums, and problem sets.
- **Integrity Guards**: Server-side time enforcement (never trusting browser clock), submission rate limiting, and tie-breaking by penalty points.

### 7. 🎯 Skill Gap Analyzer
- **Diagnostic Engine**: Tracks 14 engineering competencies (Arrays, Dynamic Programming, SQL, Operating Systems, Trees & Graphs, Quantitative Aptitude, etc.).
- **Proficiency Tiers**: Automatically classifies skills into *Proficient*, *Developing*, or *Needs Attention* based on actual quiz and submission performance.
- **Smart Recommendations**: Links directly to recommended roadmap practice tasks.

### 8. 🌐 DKoder Community & Social Leaderboards
- **Community Hub**: Public student profiles, peer discussion feed, tag filtering (`#ZohoDrive`, `#DSA`, `#DBMS`), comments, and reactions.
- **Safety & Moderation**: Post reporting mechanism, profanity guards, and administrative moderation tools.
- **Global Leaderboards**: Server-calculated rankings for weekly coding activity, monthly consistency, and arena points.

### 9. 📄 DKoder Career Profile (Resume Builder & Portfolio Generator)
- **ATS-Friendly Resume Builder**: Interactive form editing Education, Skills, Projects, Experience, and Certifications with real-time live preview.
- **Export**: One-click Print/PDF export layout and live ATS compatibility score gauge (e.g. 88%).
- **Public Portfolio Generator**: Toggleable public portfolio URL with project showcase tags and privacy controls.

### 10. 🛡️ Admin Dashboard (Role-Based Access Control)
- **Restricted Access**: Server-enforced role authentication (`student`, `moderator`, `admin`).
- **Administrative Tools**:
  - System KPIs (total students, problems, submissions, pass rates, AI engine status).
  - User Directory with status activation/deactivation.
  - Problem & Test Case Manager with hidden testcase configuration.
  - Content Moderation Queue for reported community discussions.
  - System Audit Trail logging critical administrative events.

---

## 🗄️ Database Architecture (32 Relational Entities)

The platform is backed by a relational schema in `core/models.py`:
1. `User` (Extends Django AbstractUser with roles: student, moderator, admin)
2. `StudentProfile` (College, degree, target companies, streak, points, bio)
3. `RolePermission` (RBAC definitions)
4. `AIConversation` (Persistent AI chat sessions)
5. `AIMessage` (Individual chat turns, tokens, code snippets)
6. `CodingProblem` (Slug, difficulty, topic tags, points, starter code)
7. `TestCase` (Public and hidden testcases with expected outputs)
8. `CodeSubmission` (Submitted code, status, execution metrics)
9. `PlacementRoadmap` (Target role, deadline, completion percentage)
10. `RoadmapTask` (Category, milestone, priority, completed boolean)
11. `StudentSkill` (Proficiency tier, accuracy, assessment counts)
12. `SkillAssessment` (Quiz evaluations)
13. `StudentAnalytics` (Aggregated statistics, history logs)
14. `MockInterview` (Interview session configurations and reports)
15. `InterviewQuestion` (Questions asked in interview)
16. `InterviewAnswer` (Student answers and AI feedback scores)
17. `Competition` (Contest timing, rules, max participants)
18. `CompetitionRegistration` (User contest enrollments)
19. `CompetitionSubmission` (Contest code submissions)
20. `LeaderboardEntry` (Rank, score, penalties)
21. `CommunityPost` (Discussions, topics, like counts)
22. `Comment` (Nested replies to posts)
23. `Reaction` (Likes and reactions)
24. `StudyGroup` (Peer study circles)
25. `GroupMembership` (Study circle members)
26. `ContentReport` (Flagged community posts with moderation status)
27. `Resume` (Stored student resumes)
28. `ResumeVersion` (Resume version history)
29. `Portfolio` (Public portfolio configuration)
30. `PortfolioProject` (Projects featured on portfolio)
31. `AdminAuditLog` (Security and moderation audit records)
32. `Notification` (In-app notifications and alerts)

---

## ⚡ Quick Start & Running Locally

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Dependencies installed: `django`, `whitenoise`, `pillow` (already installed in environment)

### 2. Launch the Application
Run the DKoder 2.0 runner from the project root:
```bash
py server.py
```
*Or using the standard Django CLI:*
```bash
py manage.py runserver 0.0.0.0:8080
```

### 3. Open in Browser
Visit: **`http://localhost:8080/`**

### 4. Switch Between Built-in Demo Accounts
Click the **"Switch User"** badge in the top navigation bar to test all roles immediately:
- **Alex Rivera (`alex`)**: SDE Aspirant (Student role) — test CodeLab, AI Mentor, Roadmap, Resume, and Analytics.
- **Priya Patel (`priya`)**: Student Moderator — test community interaction.
- **Prof. Vikram Sharma (`admin`)**: Faculty Dean & Admin — access the restricted Admin Dashboard.

### 5. Optional: Activate Live Google Gemini AI
DKoder 2.0 comes with an intelligent domain-specific development simulation AI engine active by default. To connect live Google Gemini:
```powershell
$env:GEMINI_API_KEY="your_actual_gemini_api_key"
py server.py
```

---

## 📁 Project Directory Map
```
DKoder/
├── backend/                  # Django project configuration
│   ├── settings.py           # Installed apps, WhiteNoise static files, templates
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py               # WSGI application entry
├── core/                     # Core DKoder 2.0 application
│   ├── models.py             # 32 Relational database models
│   ├── views.py              # REST API endpoints for all 10 features
│   ├── urls.py               # API routing table (/api/...)
│   ├── ai_service.py         # AI Mentor & Interview LLM service abstraction
│   ├── compiler_service.py   # Isolated multi-language code runner
│   ├── seed_data.py          # Realistic seed generator
│   └── migrations/           # Django database migration history
├── assets/
│   ├── css/
│   │   ├── style.css         # Original DKoder styles preserved
│   │   └── dkoder-2.css      # DKoder 2.0 animations, tokens, and workspaces
│   ├── js/
│   │   ├── script.js         # Original homepage logic preserved
│   │   ├── dkoder-api.js     # Unified API client & dual-mode offline sync
│   │   └── dkoder-app.js     # DKoder 2.0 interactive UI controller
│   └── images/               # Brand assets & illustrations
├── index.html                # Unified single-page application & homepage
├── server.py                 # Self-bootstrapping development server
├── db.sqlite3                # Pre-migrated & seeded database
└── README.md                 # Project documentation
```

---

## 📄 License
© 2026 DKoder Platforms Inc. All rights reserved.
