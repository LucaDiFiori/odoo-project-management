from odoo import fields, models

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
    # -`project.project` creates a foreign key relationship in the database, linking the team member table to a specific project in the project table.
    # - string='Project' is the label that will be shown in the user interface for this field
    # - required=True means that this field must be filled in for a record to be valid
    # - ondelete='cascade' means that if the linked project is deleted, this team member record will also be deleted automatically
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
    # It is a Many2one field linking to the 'res.users' model, which represents the users in the Odoo system.
    # NOTE:
    # Many2one is used here because different records in the project team member model can link to 
    # the same user (e.g., a user can be a member of multiple projects), 
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
    # SQL constraints
    #--------------------------------------------------------------
    # _sql_constraints is a list of SQL constraints that are applied to the database table.
    # - unique_member_per_project is the name of the constraint.
    # - UNIQUE(project_id, user_id) ensures that the combination of project_id and user_id is unique across the table, 
    #   meaning that a user cannot be added more than once to the same
    # - The last element is the error message that will be shown if this constraint is violated
    _sql_constraints = [
        (
            'unique_member_per_project',
            'UNIQUE(project_id, user_id)',
            'A user can only be added once per project.',
        ),
    ]