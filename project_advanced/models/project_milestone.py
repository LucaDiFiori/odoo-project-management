from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.addons.project.models.project_task import CLOSED_STATES

# Extends the milestone model to manage state, progress, and synchronization
# between the workflow (state) and the is_reached flag.
class ProjectMilestone(models.Model):
    #--------------------------------------------------------------
    # model metadata
    #--------------------------------------------------------------
    _inherit = 'project.milestone'

    #--------------------------------------------------------------
    # fields definition
    #--------------------------------------------------------------
    # state is a class attribute that defines the milestone's workflow status
    # as a Selection field, so each record can only be in one allowed state
    # (todo, in_progress, or done).
    state = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='State', default='todo', required=True, tracking=True)

    # progress is a class attribute that defines a Float field whose value is computed by
    # _compute_progress, representing the milestone completion percentage
    # based on done tasks over total
    progress = fields.Float(
        string='Progress',
        # Computed field: Odoo fills this value by calling _compute_progress
        compute='_compute_progress',
        help='Percentage of completed tasks',
    )

    # Determines whether the milestone can be set to 'done'.
    # True only if there is at least one top-level task and all of them are in CLOSED_STATES.
    # Subtasks are excluded, consistent with the progress calculation logic.
    can_set_done = fields.Boolean(
        compute='_compute_can_set_done',
        string='Can Set Done',
    )

    #--------------------------------------------------------------
    # computed fields
    #--------------------------------------------------------------
    # Compute the completion percentage based on top-level tasks only (subtasks are excluded).
    # Calculates the ratio of done top-level tasks to total top-level tasks as a percentage (0-100).
    # Returns 0 if no top-level tasks exist to avoid division by zero.
    # NOTE:
    # @api.depends('task_ids.state', 'task_ids.parent_id') tells Odoo to recompute progress
    # whenever a task's state or parent changes, ensuring subtasks never inflate the percentage.
    @api.depends('task_ids.state', 'task_ids.parent_id')
    def _compute_progress(self):
        # counts_per_milestone is a dictionary that maps each milestone ID to a tuple (total, done),
        # - total: the number of top-level tasks assigned to that milestone 
        # - done: the number of those tasks whose state is in CLOSED_STATES ('1_done' or '1_canceled').
        # _read_group groups tasks by milestone_id and returns, for each group, the milestone record,
        # the total count of tasks (__count), and the list of all state values (state:array_agg).
        # The filter ('parent_id', '=', False) ensures only top-level tasks are considered.
        counts_per_milestone = {}
        for milestone, count, state_list in self.env['project.task']._read_group(
            [('milestone_id', 'in', self.ids), ('parent_id', '=', False)], # filter: only top-level tasks for the milestones in self
            ['milestone_id'], # group by milestone_id
            ['__count', 'state:array_agg'], # aggregate: count of tasks and list of their states
        ):
            counts_per_milestone[milestone.id] = (count, sum(state in CLOSED_STATES for state in state_list))
        for milestone in self:
            total, done = counts_per_milestone.get(milestone.id, (0, 0))
            milestone.progress = (done / total * 100) if total else 0.0

    # Computes whether the milestone can be marked as done.
    # Used in the view to enable the "Mark as Done" button: True only if the milestone
    # has at least one top-level task and all top-level tasks are in a closed state.
    @api.depends('task_ids.state', 'task_ids.parent_id')
    def _compute_can_set_done(self):
        for milestone in self:
            top_tasks = milestone.task_ids.filtered(lambda t: not t.parent_id)
            milestone.can_set_done = bool(top_tasks) and all(
                t.state in CLOSED_STATES for t in top_tasks
            )

    #--------------------------------------------------------------
    # action methods
    #--------------------------------------------------------------
    # Sets the milestone state to 'todo' and syncs is_reached accordingly.
    # Called by the "To Do" button in the form view header.
    def action_set_todo(self):
        self.write({'state': 'todo'})

    # Sets the milestone state to 'in_progress' and syncs is_reached accordingly.
    # Called by the "In Progress" button in the form view header.
    def action_set_in_progress(self):
        self.write({'state': 'in_progress'})

    # Sets the milestone state to 'done' and syncs is_reached accordingly.
    # Called by the "Done" button in the form view header.
    def action_set_done(self):
        self.write({'state': 'done'})

    #--------------------------------------------------------------
    # ORM overrides
    #--------------------------------------------------------------
    # Aligns state and is_reached automatically before creating records.
    # Handles bulk creation and ensures bidirectional sync between state and is_reached.
    # Calls _sync_state_is_reached for each record before calling the parent create method.
    # NOTE:
    # - @api.model_create_multi is a decorator that allows the create method to accept a list of dictionaries
    #  (vals_list) for bulk record creation, improving performance by reducing the number of database calls.
    # - super() is used to call the original create method of the parent class (models.Model) after processing the input values,
    # - this method uses self to refer to the current model (ProjectMilestone) and ensures that the synchronization logic is applied to each record being created.
    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.user.has_group('project.group_project_manager'):
            raise AccessError("Only Project Managers can create milestones.")
        for vals in vals_list:
            self._sync_state_is_reached(vals)
        return super().create(vals_list)

    def unlink(self):
        if not self.env.user.has_group('project.group_project_manager'):
            raise AccessError("Only Project Managers can delete milestones.")
        return super().unlink()

    # Keeps state and is_reached synchronized before updating records.
    # Ensures that when either state or is_reached is modified, the other field is
    # updated consistently before the write operation is executed.
    def write(self, vals):
        if not self.env.user.has_group('project.group_project_manager'):
            raise AccessError("Only Project Managers can edit milestones.")
        self._sync_state_is_reached(vals)
        return super().write(vals)

    # Updates the is_reached flag and sets the corresponding state.
    # Sets is_reached to the provided value and updates state to 'done' if is_reached is True,
    # otherwise sets state to 'todo'. Works on a single record (ensure_one).
    # Used by the toggle in the kanban view to mark milestones as reached or not reached, 
    # ensuring both fields remain in sync.
    def toggle_is_reached(self, is_reached):
        self.ensure_one()
        self.update({
            'is_reached': is_reached,
            'state': 'done' if is_reached else 'todo',
        })
        return self._get_data()

    #--------------------------------------------------------------
    # helpers
    #--------------------------------------------------------------
    # Synchronizes state and is_reached fields bidirectionally.
    # When state is set, derives is_reached (True if state is 'done', False otherwise).
    # When is_reached is set, derives state ('done' if True, unchanged otherwise).
    # State takes priority if both are being set.
    # NOTE: is_reached is a native Odoo field used by the core (reports, kanban, notifications, etc.).
    # Since it cannot be removed, it must be kept in sync with our custom state field.
    @staticmethod
    def _sync_state_is_reached(vals):
        """Synchronize state and is_reached fields bidirectionally.

        If both are set, state takes priority.
        """
        if 'state' in vals and 'is_reached' not in vals:
            vals['is_reached'] = vals['state'] == 'done'
        elif 'is_reached' in vals and 'state' not in vals:
            if vals['is_reached']:
                vals['state'] = 'done'
