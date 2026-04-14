# Odoo Module Manifest
# ---------------------
# This file serves as the main configuration entry point for the module.
# It provides essential metadata and controls how the module is loaded
# and integrated into the Odoo system.
#
# It includes:
# - Module metadata (name, version, author)
# - Dependencies on other modules
# - Data files to be loaded (security, views, menus, etc.)
#
# Odoo uses this file to discover, install, and manage the module.

{
    # Module name displayed in the Apps list
    'name': 'Project Advanced',

    # Module version (follows Odoo versioning convention)
    'version': '18.0.1.0.0',

    # Functional category used to group modules in the UI
    'category': 'Services/Project',

    # Short description shown in module list
    'summary': 'Advanced milestone states and team member management for projects',

    # Detailed description of what the module does
    'description': """
        Extends the native Project module with:
        - Milestone state management (To Do, In Progress, Done)
        - Team member roles per project
        - Summary views and filters
    """,

    # Author of the module
    'author': 'Luca Di Fiori',

    # List of required modules (must be installed before this one)
    'depends': ['project'],

    # List of data files loaded at module installation
    'data': [
        # Access rights and security rules
        'security/ir.model.access.csv',

        # Views for milestone model (forms, lists, etc.)
        'views/project_milestone_views.xml',

        # Views for team members management
        'views/project_team_member_views.xml',

        # Extensions to the main project model views
        'views/project_project_views.xml',

        # Menu items and navigation structure
        'views/project_advanced_menus.xml',
    ],

    # Whether the module can be installed
    'installable': True,

    # Whether the module is a full application (shown as app)
    'application': False,

    # License of the module
    'license': 'LGPL-3',
}

