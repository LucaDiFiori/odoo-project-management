# Odoo Project Management Module

> Development of an advanced Odoo module for project management, milestones, and team allocation.

---

## Table of Contents

- [Description](#description)
- [Module Overview](#module-overview)
- [Installing the Module](#installing-the-module)
- [Prerequisites](#prerequisites)
- [Development Environment Setup](#development-environment-setup)
- [Project Structure](#project-structure)
- [Common Commands During Development](#common-commands-during-development)
- [Troubleshooting](#troubleshooting)
- [Quick Start](#quick-start)
- [Official Resources](#official-resources)

---

## Description

This module extends Odoo's native project management functionality with:

- **Milestone system** (project phases) for better planning
- **Team role management** (Team Lead, Developer, Tester, Analyst)
- **Automatic team member sync**: assigning a user to a task automatically adds them as a project team member
- **Deletion protection**: a team member cannot be removed while they have tasks assigned in the project
- **Role-based access control**: Project Users have read-only access to team members; Project Managers have full access
- **Progress tracking views** based on milestone completion

---

## Module Overview

### Models

#### `project_milestone.py` — Extends `project.milestone`

**Features:**
- Adds a `state` field (`To Do`, `In Progress`, `Done`) as a richer alternative to the native boolean `is_reached`
- Adds a computed `progress` field (percentage of completed top-level tasks)
- Adds a computed `can_set_done` field (True only when all top-level tasks are closed)
- Exposes action buttons: `action_set_todo`, `action_set_in_progress`, `action_set_done`

**Technical notes:**
- `state` and `is_reached` are kept bidirectionally synchronized in `create`, `write`, and `toggle_is_reached` to preserve compatibility with Odoo's native UI (kanban checkboxes, native views)
- Progress is computed using `_read_group` with `state:array_agg` — a single SQL query instead of N queries, excluding subtasks via `parent_id = False`
- `@api.depends('task_ids.state', 'task_ids.parent_id')` uses dot-notation to track changes on related records

---

#### `project_team_member.py` — New model `project.team.member`

**Features:**
- Associates a user to a project with a role (`Team Lead`, `Developer`, `Tester`, `Analyst`)
- Exposes the user's email as a read-only related field
- Blocks deletion if the user still has tasks assigned in the project

**Technical notes:**
- `UNIQUE(project_id, user_id)` SQL constraint prevents duplicate entries at the database level — stronger than a Python `@api.constrains` since it covers direct DB writes too
- `ondelete='cascade'` on both `project_id` and `user_id` ensures records are cleaned up automatically if the project or user is deleted
- `email` is a `related` field (no DB column) — always reflects the user's current email without data duplication
- `unlink()` is overridden to raise a `ValidationError` listing conflicting task names before any row is deleted

---

#### `project_project.py` — Extends `project.project`

**Features:**
- Adds `team_member_ids` (One2many to `project.team.member`) to expose team members from the project form
- Adds computed `team_member_count` (integer)
- Adds computed `milestone_progress_percentage` (float, 0–100)

**Technical notes:**
- `One2many` does not create a DB column — it uses the `project_id` foreign key in `project_team_member`
- `@api.depends('milestone_ids.is_reached')` uses dot-notation to recompute whenever any linked milestone changes

---

#### `project_task.py` — Extends `project.task`

**Features:**
- When a user is assigned to a task, they are automatically added as a `project.team.member` with role `developer` if not already present

**Technical notes:**
- Sync runs **after** `super().create()` / `super().write()` because Many2many `user_ids` rows are only committed after the parent call
- `write()` checks `if 'user_ids' in vals or 'project_id' in vals` to avoid running the sync on every field change
- Pre-checks existing members before inserting to avoid triggering the SQL UNIQUE constraint

---

### Views

| File | What it does |
|---|---|
| `project_milestone_views.xml` | Extends milestone list/form views; adds state badge, progress bar, statusbar, task inline list |
| `project_team_member_views.xml` | Defines list, form, search views and action for `project.team.member` |
| `project_project_views.xml` | Extends project form with two new tabs: Milestones and Team |
| `project_advanced_menus.xml` | Adds Milestones and Team Members entries to the Project main menu |

### Security

| Group | Read | Write | Create | Delete |
|---|---|---|---|---|
| Project User | ✓ | ✗ | ✗ | ✗ |
| Project Manager | ✓ | ✓ | ✓ | ✓ |

---

## Installing the Module

Once the development environment is set up, use the `Makefile` to install or update the module.

### First installation (fresh database)

```bash
make install
```

Runs `odoo-bin -i project_advanced --stop-after-init`. Odoo will:
1. Create all tables defined by the module's models (`project_team_member`, new columns on `project_milestone`, etc.)
2. Load all XML files (views, menus, actions)
3. Apply security rules from `ir.model.access.csv`
4. Stop automatically when done (no server left running)

Prints `[OK] Installation completed successfully.` on success, or `[ERROR]` with the exit code on failure.

### After modifying models, views, or security rules

```bash
make update
```

Runs `odoo-bin -u project_advanced --stop-after-init`. Odoo will:
1. Diff the current DB schema against the Python models and apply any changes (new columns, altered constraints, etc.)
2. Reload all XML files (views, menus, actions) — changes to existing records are re-applied
3. Re-apply security rules
4. Stop automatically when done

Prints `[OK] Update completed successfully.` on success, or `[ERROR]` with the exit code on failure.

> **When to use which:** use `make install` only once on a fresh database. Use `make update` every time you change a model field, add a view, or modify `ir.model.access.csv`.

### Verify the installation

1. Open `http://localhost:8069`
2. Log in as `admin` / `admin`
3. The **Project** app menu should show **Milestones** and **Team Members** entries
4. Open any project form — you should see the **Milestones** and **Team** tabs

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Git 2.x
- pip and virtualenv

---

## Development Environment Setup

This section walks through setting up a complete Odoo 18 development environment from scratch.

### Step 1: Check System Requirements

First, verify you have the required software installed on your machine.

#### On Linux (Ubuntu/Debian):
```bash
# Check Python version
python3 --version  # Should be 3.10 or higher

# Check Git
git --version

# Check if PostgreSQL is available
which psql
```

#### On macOS:
```bash
python3 --version
git --version
which psql
```

#### On Windows:
```bash
python --version
git --version
where psql
```

**What we're checking:** These are the core tools you need. Python runs Odoo, PostgreSQL stores data, and Git tracks changes.

---

### Step 2: PostgreSQL Setup

PostgreSQL is a **database**—it's where Odoo stores all business data (projects, tasks, users, etc.).

#### Linux (Ubuntu/Debian with Homebrew):

If PostgreSQL is already installed via Homebrew, just start the service:

```bash
# Start PostgreSQL
brew services start postgresql@14

# Verify it's running
brew services list
```

If PostgreSQL is not installed:

```bash
# Install PostgreSQL via Homebrew
brew install postgresql@14

# Start the service
brew services start postgresql@14
```

#### Linux (Ubuntu/Debian - System Package Manager):

```bash
# Update package list
sudo apt update

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql

# Verify installation
psql --version
```

#### macOS (using Homebrew):
```bash
# Install PostgreSQL if not already installed
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Verify
psql --version
```

#### Windows:
Download and install from https://www.postgresql.org/download/windows/
- During installation, **remember the password** you set for the `postgres` user
- Ensure "Start service" is checked
- Use default port 5432

**Why PostgreSQL?** Odoo is an ERP system—it needs a real database to manage concurrent users, large datasets, and transactions safely.

---

### Step 3: Create a PostgreSQL User for Odoo

PostgreSQL needs a dedicated user account that Odoo will use to access the database.

#### Linux/macOS (with Homebrew):

```bash
# Create the odoo user with superuser privileges
createuser -s odoo

# Verify user was created
psql -c "\du"
```

You should see `odoo` in the list of roles.

#### Linux (System PostgreSQL):
```bash
# Switch to postgres user
sudo -u postgres createuser -s odoo

# Verify user was created
sudo -u postgres psql -c "\du"
```

#### Windows (using pgAdmin):
1. Open pgAdmin (installed with PostgreSQL)
2. Right-click "Login/Group Roles" → Create → Login/Group Role
3. Set Name: `odoo`
4. Go to "Privileges" tab → Enable "Superuser"
5. Click Save

**What this does:** Creates an Odoo database user with superuser permissions (needed during development).

**Why needed?** When Odoo starts, it connects to PostgreSQL using this user account to create databases and tables.

---

### Step 4: Clone Odoo 18 from GitHub

For development, we'll clone the Odoo source code directly from GitHub instead of using pip. This gives you access to the full codebase and makes it easier to debug.

```bash
# Navigate to your home directory
cd /<homepath>  # or your home path

# Clone Odoo 18.0 repository
git clone https://github.com/odoo/odoo.git --depth=1 --branch=18.0

# Navigate into the cloned directory
cd odoo
```

**What this does:**
- `--depth=1` → Downloads only the latest commit (faster, ~500MB instead of full history)
- `--branch=18.0` → Clones specifically the 18.0 branch
- You now have the complete Odoo 18 source code

---

### Step 5: Clone This Repository and Create a Virtual Environment

Clone this module's repository and create the virtual environment **inside it** (not inside the Odoo directory).

```bash
# Clone this repository
git clone <repository-url>
cd odoo-project-management

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# You should see (venv) in your terminal prompt
```

**Why here and not in the Odoo directory?** The venv belongs to this module project. Odoo source is a shared dependency we'll point to, not something we own.

---

### Step 6: Install Odoo and Its Dependencies

With the venv activated, install Odoo from the cloned source in **editable mode** (`-e`). This installs Odoo and all its dependencies in one step.

```bash
# Install Odoo from the local clone
pip install -e /<homepath>/odoo

# Install a missing dependency not included in Odoo's requirements.txt
pip install lxml_html_clean

# Verify Odoo is ready
python -c "from odoo import api, fields, models; print('OK')"
```

**What `-e` does:** Links the venv directly to the Odoo source folder. Changes to Odoo source are reflected immediately — no reinstall needed.

**Why `lxml_html_clean`?** It was split off from `lxml` into a separate package; Odoo 18's `requirements.txt` hasn't caught up yet.

---

### Step 6b: Configure Pyright / VS Code (optional)

The repository already includes a `pyrightconfig.json` that tells Pyright to use the local venv. For it to resolve the `odoo` import, you need to register the Odoo source path in the venv with a `.pth` file:

```bash
# Replace /<homepath>/odoo with your actual Odoo clone path
echo "/<homepath>/odoo" > venv/lib/python3.*/site-packages/odoo-source.pth
```

For example, if your Odoo clone is at `/home/john/odoo` and you're on Python 3.13:

```bash
echo "/home/john/odoo" > venv/lib/python3.13/site-packages/odoo-source.pth
```

Then reload your editor window. The `Import "odoo" could not be resolved` warning will disappear.

---

### Step 7: Create Odoo Configuration File

Odoo needs a configuration file (`.odoorc`) to know:
- Which database to use
- Database credentials
- HTTP port to listen on

Create the file in your home directory:

```bash
cat > ~/.odoorc << 'EOF'
[options]
admin_passwd = admin
db_host = localhost
db_port = 5432
db_user = odoo
db_password = 
db_name = odoo_dev
http_port = 8069
workers = 0
logfile = /tmp/odoo.log
EOF
```

**What these settings mean:**
- `admin_passwd` → Master password for Odoo (use "admin" for development)
- `db_host/port` → Where PostgreSQL is running (localhost:5432)
- `db_user` → The PostgreSQL user we created (`odoo`)
- `db_name` → Database Odoo will create (`odoo_dev`)
- `http_port` → Port to access Odoo web interface (8069)

---

### Step 8: Start Odoo for the First Time

Now let's launch Odoo! This is the important moment - Odoo will create the database automatically.

Make sure:
1. The venv is activated (you see `(venv)` in prompt)
2. PostgreSQL is running

Then execute from the Odoo source directory:

```bash
cd /<homepath>/odoo
python odoo-bin --addons-path=addons,/<path>/odoo-project-management --dev=all -d odoo_dev
```

Or use the `odoo` command if it's on your PATH:

```bash
odoo --addons-path=/<homepath>/odoo/addons,/<path>/odoo-project-management --dev=all -d odoo_dev
```

**What's happening:**
1. Odoo connects to PostgreSQL
2. Creates the `odoo_dev` database
3. Loads all core modules
4. Starts web server on http://localhost:8069
5. `--dev=all` enables hot-reload (auto-refresh when you edit code)

**First time setup takes 2-5 minutes** while PostgreSQL loads all core modules.

When you see a message like `Listening on 127.0.0.1:8069`, Odoo is ready!

---

### Step 9: Access Odoo Web Interface

Open your browser and go to:
```
http://localhost:8069
```

**First login:**
- Email: `admin`
- Password: `admin`

(These are the default credentials Odoo creates automatically)

You should see:
- Dashboard with default Odoo apps (Sales, Inventory, Projects, HR, etc.)
- Menu on left side
- Settings button in top right


---

### Step 10: Enable Developer Mode

To develop custom modules, you need Developer Mode enabled.

1. Click your user avatar (top right)
2. Select "Settings"
3. Look for "Developer Tools" section
4. Enable "Activate the developer mode"
5. Refresh page (F5)

**What changed:**
- New menu items in Settings: "Fields", "Action", "Views", etc.
- You can now inspect and edit Odoo internals
- Developer-only features become available

---

## Project Structure

```
odoo-project-management/
├── venv/                           # Virtual environment (auto-created)
├── project_advanced/               # Our custom module
│   ├── __init__.py
│   ├── __manifest__.py             # Module metadata and dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project_milestone.py    # Extends project.milestone (state, progress, sync)
│   │   ├── project_team_member.py  # New model: project.team.member
│   │   ├── project_project.py      # Extends project.project (team_member_ids, computed fields)
│   │   └── project_task.py         # Extends project.task (auto-sync assignees → team members)
│   ├── views/
│   │   ├── project_milestone_views.xml
│   │   ├── project_team_member_views.xml
│   │   ├── project_project_views.xml
│   │   └── project_advanced_menus.xml
│   ├── security/
│   │   └── ir.model.access.csv
├── .gitignore
├── requirements.txt
├── Makefile
└── README.md
```

---

## Common Commands During Development

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Start Odoo with auto-reload
odoo --dev=all -d odoo_dev

# Start Odoo with different port
odoo --dev=all -d odoo_dev --http-port 8070

# View logs in real-time
odoo --dev=all -d odoo_dev --logfile=/tmp/odoo.log && tail -f /tmp/odoo.log

# Restart Odoo
# Press Ctrl+C to stop, then run the start command again
```

---

## Troubleshooting

### PostgreSQL Connection Failed
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
# or
brew services list  # macOS

# Verify Odoo user exists
sudo -u postgres psql -c "\du"
```

### Port 8069 Already in Use
```bash
# Use different port
odoo --dev=all -d odoo_dev --http-port 8070
```

### Database Already Exists
```bash
# Odoo will use existing database
# To start fresh, delete it:
sudo -u postgres dropdb odoo_dev
# Then restart odoo
```

### ModuleNotFoundError: No module named 'odoo'
```bash
# 1. Make sure the virtual environment is activated
source venv/bin/activate  # Linux/macOS

# 2. Make sure Odoo is installed in the venv
pip install -e /<homepath>/odoo
pip install lxml_html_clean
```

### Import "odoo" could not be resolved (VS Code / Pyright warning)
```bash
# Add the Odoo source path to the venv as a .pth file
echo "/<homepath>/odoo" > venv/lib/python3.13/site-packages/odoo-source.pth
# Then reload the VS Code window (Ctrl+Shift+P → Reload Window)
```

---

## Quick Start

Once the environment is set up (see steps above), use the `Makefile` to manage the Odoo server:

| Command | Description |
|---|---|
| `make run` | Starts the Odoo server with hot-reload enabled. Use this during normal development — code changes are picked up automatically without restarting. |
| `make install` | Installs the `project_advanced` module for the first time on a fresh database. Run this once after creating the database. |
| `make update` | Reinstalls the module, applying any changes to models, views, or security rules. Run this whenever you add new fields, models, or XML records. |

**Typical workflow:**

```bash
# First time: install the module
make install

# Start developing (hot-reload active)
make run

# After adding a new model or view
make update
```

---

## Official Resources

- Odoo 18 Documentation: https://www.odoo.com/documentation/18.0/
- Odoo Developer Tutorials: https://www.odoo.com/documentation/18.0/developer/tutorials.html
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

**Status**: Development Setup Guide - Last Updated April 2026
