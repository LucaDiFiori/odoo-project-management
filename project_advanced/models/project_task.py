from odoo import api, models

# Extends project.task to automatically synchronize task assignees with the
# project.team.member table. When a user is assigned to a task, they are added
# as a team member of the project (with role 'developer') if not already present.
class ProjectTask(models.Model):
    #--------------------------------------------------------------
    # model metadata
    #--------------------------------------------------------------
    _inherit = 'project.task'

    #--------------------------------------------------------------
    # helpers
    #--------------------------------------------------------------
    # Ensures all users in user_ids are registered as team members of the given project.
    # Queries existing team members first to avoid duplicates, then creates only the missing ones.
    # NOTE:
    # - user_ids is a list of res.users IDs (integers), not a recordset.
    # - project_id is the integer ID of the project.project record.
    # - The guard (if not project_id or not user_ids) skips the sync for tasks
    #   that have no project or no assignees, avoiding unnecessary DB queries.
    def _sync_assignees_to_team_members(self, user_ids, project_id):
        if not project_id or not user_ids:
            return
        TeamMember = self.env['project.team.member']
        # existing collects the IDs of users who are already team members of this project,
        # so that we only create records for the truly new ones.
        # .mapped('user_id').ids is the idiomatic Odoo way to extract a list of IDs
        # from a recordset field — equivalent to [r.user_id.id for r in records].
        existing = TeamMember.search([
            ('project_id', '=', project_id),
            ('user_id', 'in', list(user_ids)),
        ]).mapped('user_id').ids
        to_create = [uid for uid in user_ids if uid not in existing]
        for uid in to_create:
            TeamMember.create({
                'project_id': project_id,
                'user_id': uid,
                'role': 'developer',
            })

    #--------------------------------------------------------------
    # ORM overrides
    #--------------------------------------------------------------
    # Syncs assignees to team members after task creation.
    # The sync runs after super().create() because only at that point are the Many2many
    # user_ids rows committed to the DB and readable via task.user_ids.ids.
    # NOTE:
    # @api.model_create_multi allows bulk creation: vals_list is a list of dicts,
    # one per record. Odoo 17+ requires this pattern instead of the old single-dict create.
    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            if task.project_id and task.user_ids:
                self._sync_assignees_to_team_members(
                    task.user_ids.ids, task.project_id.id
                )
        return tasks

    # Syncs assignees to team members after task updates.
    # The check (if 'user_ids' in vals or 'project_id' in vals) avoids running the sync
    # on every write — only when the fields that affect team membership actually change.
    # The sync runs after super().write() so that task.user_ids reflects the updated values.
    # NOTE:
    # self can be a recordset with multiple tasks (e.g. mass assignment from the list view).
    # The for loop handles all of them correctly.
    def write(self, vals):
        res = super().write(vals)
        if 'user_ids' in vals or 'project_id' in vals:
            for task in self:
                if task.project_id and task.user_ids:
                    self._sync_assignees_to_team_members(
                        task.user_ids.ids, task.project_id.id
                    )
        return res
