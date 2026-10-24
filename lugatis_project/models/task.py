from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    # Odoo Community has a deadline but no start; Enterprise's planned_date_begin is
    # used instead when it is there. With allocated_hours (Ayrılan süre) and the
    # company's working calendar, Lugatis draws and moves the task on its Gantt.
    lg_planned_start = fields.Datetime(
        string="Planlanan başlangıç", tracking=True, copy=False, index=True
    )
