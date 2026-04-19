from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# ProjectTeamMember represents the association between a project and its team members, 
# including their roles within the project.
class ProjectTeamMember(models.Model):
    #--------------------------------------------------------------
    # model metadata
    #--------------------------------------------------------------
    # model name, generates the table name in the database as 'project_team_member'
    _name = 'project.team.member'
    _description = 'Project Team Member'
    # default ordering of records when retrieved from the database
    _order = 'project_id, role, user_id'

    #--------------------------------------------------------------
    # fields definition
    #--------------------------------------------------------------
    # project_id represents the project that this team member belongs to
    # -`project.project` creates a foreign key relationship in the database, 
    #   linking the team member table to a specific project in the project table.
    # - string='Project' is the label that will be shown in the user interface for this field
    # - required=True means that this field must be filled in for a record to be valid
    # - ondelete='cascade' means that if the linked project is deleted, 
    #   this team member record will also be deleted automatically
    # NOTE:
    # Many2one links this record to one project.
    # We use it here because each team member belongs to a single project,
    # while one project can have many team members.
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade',
    )

    # user_id defines the user that is a member of the project team.
    # It is a Many2one field linking to the 'res.users' model, which represents 
    # the users in the Odoo system.
    # NOTE:
    # Many2one is used here because different records in the project team member 
    # model can link to the same user (e.g., a user can be a member of multiple projects), 
    # but each team member record can only link to one user.
    user_id = fields.Many2one(
        'res.users',
        string='Member',
        required=True,
        ondelete='cascade',
    )

    # role defines the role of the team member within the project. 
    # It is a selection field that allows users to choose from 
    # predefined roles such as 'Team Lead', 'Developer', 'Tester', and 'Analyst'. 
    role = fields.Selection([
        ('team_lead', 'Team Lead'),
        ('developer', 'Developer'),
        ('tester', 'Tester'),
        ('analyst', 'Analyst'),
    ], string='Role', required=True)

    # email is a related field that automatically retrieves 
    # the email address of the user linked in user_id.
    email = fields.Char(
        string='Email',
        related='user_id.email',
        readonly=True,
    )

    #--------------------------------------------------------------
    # computed fields
    #--------------------------------------------------------------
    # milestone_ids is a computed Many2many field that returns all milestones
    # in the project where this user has at least one task assigned.
    # It has no DB column — values are derived on the fly by querying project.task
    # using the method _compute_milestone_ids
    milestone_ids = fields.Many2many(
        'project.milestone',
        compute='_compute_milestone_ids',
        string='Milestones',
    )

    # Searches for all tasks in the project assigned to this user that have a milestone,
    # then returns the distinct milestones via mapped('milestone_id').
    # NOTE:
    # ('milestone_id', '!=', False) filters out tasks with no milestone assigned,
    # so only relevant milestones appear. mapped() deduplicates automatically
    # because it operates on a recordset.
    @api.depends('project_id', 'user_id')
    def _compute_milestone_ids(self):
        for member in self:
            tasks = self.env['project.task'].search([
                ('project_id', '=', member.project_id.id),
                ('user_ids', 'in', member.user_id.id),
                ('milestone_id', '!=', False),
            ])
            member.milestone_ids = tasks.mapped('milestone_id')

    #--------------------------------------------------------------
    # ORM overrides
    #--------------------------------------------------------------
    # Redirects the row click to the linked user's form view instead of opening
    # the project.team.member form. This makes the list behave as a roster where
    # clicking a member navigates directly to their user profile.
    def get_formview_action(self, access_uid=None):
        self.ensure_one()
        return self.user_id.get_formview_action(access_uid=access_uid)


    # Prevents deletion of a team member who still has tasks assigned in the project.
    # Raises a ValidationError listing the conflicting task names so the user knows
    # exactly what to reassign before removing the member.
    # NOTE:
    # unlink() is the Odoo ORM method for DELETE. Overriding it is the correct place
    # to add pre-delete guards — the check runs before any row is removed from the DB.
    # self can be a recordset with multiple records (e.g. bulk delete from list view),
    # so we iterate and collect all conflicts before raising a single error.
    def unlink(self):
        for member in self:
            assigned_tasks = self.env['project.task'].search([
                ('project_id', '=', member.project_id.id),
                ('user_ids', 'in', member.user_id.id),
            ])
            if assigned_tasks:
                task_names = ', '.join(assigned_tasks.mapped('name'))
                raise ValidationError(
                    _("Cannot remove %s: they are still assigned to task(s): %s. "
                      "Please reassign those tasks first.")
                    % (member.user_id.name, task_names)
                )
        return super().unlink()

    #--------------------------------------------------------------
    # SQL constraints
    #--------------------------------------------------------------
    # _sql_constraints is a list of SQL constraints applied at the database level.
    # - unique_member_per_project ensures UNIQUE(project_id, user_id):
    #   a user cannot be added more than once to the same project.
    # - The third element is the error message shown to the user if the constraint is violated.
    # NOTE:
    # A SQL constraint is stronger than @api.constrains — it is enforced by PostgreSQL
    # directly, so it covers direct DB writes that bypass the ORM as well.
    _sql_constraints = [
        (
            'unique_member_per_project',
            'UNIQUE(project_id, user_id)',
            'A user can only be added once per project.',
        ),
    ]