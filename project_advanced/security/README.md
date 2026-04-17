# Security

This folder contains access control rules for the `project_advanced` module.

## ir.model.access.csv

Defines record-level permissions (CRUD) for each model, mapped to Odoo user groups.

| ID | Name | Model | Group | Read | Write | Create | Delete |
|----|------|-------|-------|------|-------|--------|--------|
| `access_project_team_member_user` | `project.team.member.user` | `project.team.member` | Project User | yes | no | no | no |
| `access_project_team_member_manager` | `project.team.member.manager` | `project.team.member` | Project Manager | yes | yes | yes | yes |

### General rule

> **The `group_id` is allowed to perform the specified operations (read, write, create, delete) on the `model_id`.**

### How it works

`ir.model.access.csv` is the standard Odoo mechanism for defining **model-level access control** (ACL). Odoo reads this file when the module is installed or updated and creates `ir.model.access` records in the database.

Each row defines a permission rule. Here is what each field means:

- **`id`** — a unique name for this rule, used by Odoo to identify it.
- **`name`** — a human-readable label, visible in the admin interface.
- **`model_id:id`** — which model this rule applies to (e.g. `model_project_team_member`).
- **`group_id:id`** — which group of users this rule applies to (e.g. managers, basic users). Leave empty to apply to everyone.
- **`perm_read`** — `1` = can view records, `0` = cannot.
- **`perm_write`** — `1` = can edit records, `0` = cannot.
- **`perm_create`** — `1` = can create new records, `0` = cannot.
- **`perm_unlink`** — `1` = can delete records, `0` = cannot.

When a user tries to perform an operation, Odoo checks whether any rule grants that permission to **at least one group the user belongs to**. If no matching rule is found, access is denied and Odoo raises an `AccessError`.

This file must be declared in the module's `__manifest__.py` under the `data` key to be loaded automatically:

```python
'data': [
    'security/ir.model.access.csv',
    ...
]
```

### Rules summary

- **Project Users** can only view team members.
- **Project Managers** have full access to team member records.
