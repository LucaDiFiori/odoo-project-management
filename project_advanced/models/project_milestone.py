from odoo import api, fields, models

# Extends the milestone model to manage state, progress, and synchronization
# between the workflow (state) and the is_reached flag.
class ProjectMilestone(models.Model):
    _inherit = 'project.milestone'

    # state is a class attribute that defines the milestone's workflow status as a Selection field, 
    # so each record can only be in one allowed state (todo, in_progress, or done).
    state = fields.Selection([
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], string='State', default='todo', required=True, tracking=True)

    # progress is a class attribute that defines a Float field whose value is computed by 
    # _compute_progress, representing the milestone completion percentage based on done tasks over total
    progress = fields.Float(
        string='Progress',
        # Computed field: Odoo fills this value by calling _compute_progress, so users do not enter it manually.
        compute='_compute_progress',
        help='Percentage of completed tasks',
    )

    # Compute the completion percentage based on completed tasks.
    # Calculates the ratio of done_task_count to task_count as a percentage (0-100).
    # Returns 0 if no tasks exist to avoid division by zero.
    # NOTE:
    # @api.depends('task_count', 'done_task_count') is a decorator that tells Odoo to automatically 
    # recompute the progress field whenever task_count or done_task_count changes, 
    # ensuring that the progress value is always up-to-date with the current state of tasks.
    @api.depends('task_count', 'done_task_count')
    def _compute_progress(self):
        for milestone in self:
            if milestone.task_count:
                milestone.progress = (milestone.done_task_count / milestone.task_count) * 100
            else:
                milestone.progress = 0.0

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
        for vals in vals_list:
            self._sync_state_is_reached(vals)
        return super().create(vals_list) 

    # Keeps state and is_reached synchronized before updating records.
    # Ensures that when either state or is_reached is modified, the other field is
    # updated consistently before the write operation is executed.
    def write(self, vals):
        self._sync_state_is_reached(vals)
        return super().write(vals)

    # Updates the is_reached flag and sets the corresponding state.
    # Sets is_reached to the provided value and updates state to 'done' if is_reached is True,
    # otherwise sets state to 'todo'. Works on a single record (ensure_one).
    def toggle_is_reached(self, is_reached):
        self.ensure_one()
        self.update({
            'is_reached': is_reached,
            'state': 'done' if is_reached else 'todo',
        })
        return self._get_data()

    # Synchronizes state and is_reached fields bidirectionally.
    # When state is set, derives is_reached (True if state is 'done', False otherwise).
    # When is_reached is set, derives state ('done' if True, unchanged otherwise).
    # State takes priority if both are being set.
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
