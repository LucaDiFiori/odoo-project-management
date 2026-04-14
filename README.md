# Odoo Project Management Module

> Development of an advanced Odoo module for project management, milestones, and team allocation.

## 📋 Description

This module extends Odoo's native project management functionality with:
- **Milestone system** (project phases) for better planning
- **Team role management** (Team Lead, Developer, Tester, Analyst)
- **Team member allocation** on tasks
- **Progress tracking views** based on milestone completion

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Git 2.x
- pip and virtualenv

## 🛠️ Development Environment Setup

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

### Step 5: Create a Python Virtual Environment

A **virtual environment** is an isolated Python space for this project. It prevents conflicts with other projects.

```bash
# Make sure you're in the odoo directory
cd /<homepath>/odoo

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

**What happened:**
- `python3 -m venv venv` → Creates a folder named `venv` with isolated Python
- `source venv/bin/activate` → "Enter" that isolated environment
- Now any packages you install only affect THIS project

**Why this matters?** Without a virtual env, installing Odoo could break other Python projects on your system.

---

### Step 6: Install Odoo Dependencies

Now we'll install the dependencies that Odoo 18 requires.

```bash
# Make sure virtual environment is activated
# (you should see (venv) in your prompt)

# Install dependencies from requirements.txt
pip install -r requirements.txt

# If there are any missing packages, install them individually
pip install lxml_html_clean psycopg2-binary

# Verify Odoo is ready
odoo --version
```

**What's installing:**
- All Python packages that Odoo 18 depends on (Babel, Jinja2, Werkzeug, etc.)
- `psycopg2-binary` → Driver that lets Python (Odoo) talk to PostgreSQL

This takes a few minutes because it's downloading and installing many dependencies.

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
1. You're in the `odoo` directory
2. The venv is activated (you see `(venv)` in prompt)
3. PostgreSQL is running

Then execute:

```bash
odoo --dev=all -d odoo_dev
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

## 📁 Project Structure

```
odoo-project-module/
├── venv/                       # Virtual environment (auto-created)
├── project_advanced/           # Our custom module
│   ├── __init__.py
│   ├── __manifest__.py         # Module metadata
│   ├── models/
│   │   ├── __init__.py
│   │   ├── milestone.py        # Milestone model
│   │   └── team_member.py      # Team member model
│   ├── views/
│   │   ├── milestone_view.xml
│   │   ├── team_member_view.xml
│   │   └── project_view.xml
│   ├── security/
│   │   └── ir.model.access.csv
│   └── static/                 # CSS, JS (if needed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Common Commands During Development

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

## ❌ Troubleshooting

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
# Virtual environment not activated
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

---

## 📚 Next Steps

Once your environment is working:
1. Explore Odoo's built-in Project module
2. Create the custom models (Milestone, TeamMember)
3. Build views and menus
4. Test with sample data

---

## 🔗 Official Resources

- Odoo 18 Documentation: https://www.odoo.com/documentation/18.0/
- Odoo Developer Tutorials: https://www.odoo.com/documentation/18.0/developer/tutorials.html
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

**Status**: 🔨 Development Setup Guide - Last Updated April 2026
