from odoo import api, fields, models

# ProjectProject Class Represents a project — the top-level entity grouping tasks, milestones, and team members.
#
# ProjectProject extends the native project.project model using _inherit (no _name),
# so no new database table is created — fields are added as columns to the existing one.
# This is necessary to expose the inverse side of the One2many relationship with
# project.team.member (which holds the Many2one foreign key to project.project),
# and to add computed summary fields (team member count, milestone progress)
# that are accessed directly from the project form view.
class ProjectProject(models.Model):
    _inherit = 'project.project'

    team_member_ids = fields.One2many(
        'project.team.member',
        'project_id',
        string='Team Members',
    )
    team_member_count = fields.Integer(
        string='Team Members',
        compute='_compute_team_member_count',
    )
    milestone_progress_percentage = fields.Float(
        string='Milestone Progress',
        compute='_compute_milestone_progress_percentage',
        help='Percentage of milestones marked as Done',
    )

    # Counts the number of team members assigned to each project.
    # NOTE
    # @api.depends('team_member_ids') is a decorator that tells Odoo to automatically 
    # recompute the team_member_count field whenever the team_member_ids field changes 
    # (e.g., when team members are added or removed from the project), 
    # ensuring that the count is always accurate and up-to-date.
    @api.depends('team_member_ids')
    def _compute_team_member_count(self):
        for project in self:
            project.team_member_count = len(project.team_member_ids)

    # Computes the percentage of milestones marked as done for each project.
    # Triggers recompute whenever is_reached changes on any linked milestone.
    # Returns 0.0 if no milestones exist to avoid division by zero.
    @api.depends('milestone_ids.is_reached')
    def _compute_milestone_progress_percentage(self):
        for project in self:
            milestones = project.milestone_ids
            if milestones:
                reached = milestones.filtered('is_reached')
                project.milestone_progress_percentage = (len(reached) / len(milestones)) * 100
            else:
                project.milestone_progress_percentage = 0.0