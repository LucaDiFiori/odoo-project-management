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
    #--------------------------------------------------------------
    # model metadata
    #--------------------------------------------------------------
    _inherit = 'project.project'

    #--------------------------------------------------------------
    # fields definition
    #--------------------------------------------------------------
    # Inverse side of the One2many: lists all team members linked to this project.
    team_member_ids = fields.One2many(
        'project.team.member', # target model
        'project_id',          # Many2one field on project.team.member pointing back here
        string='Team Members',
    )
    # Computed float (0–100) representing the share of milestones already reached.
    milestone_progress_percentage = fields.Float(
        string='Milestone Progress',
        compute='_compute_milestone_progress_percentage',
        help='Percentage of milestones marked as Done',
    )

    #--------------------------------------------------------------
    # computed fields
    #--------------------------------------------------------------
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
