from odoo import api, fields, models

PARAM = "lugatis.restrict_modules"
MODULES = [
    "crm", "sales", "projects", "calendar", "helpdesk", "invoicing", "mail", "phone",
    "customer360", "stock", "quotes", "campaigns", "collections", "approvals",
    "dashboard", "shipments", "service", "hr", "calltime", "nps", "triage", "assistant", "meeting",
    "phoneagent", "automation", "ecommerce", "pos", "expense",
]


class LugatisAccess(models.AbstractModel):
    """Asked by the desktop app at login: which of its modules this user may use."""

    _name = "lugatis.access"
    _description = "Lugatis modül erişimi"

    @api.model
    def get_modules(self):
        restricted = self.env["ir.config_parameter"].sudo().get_param(PARAM) == "True"
        everything = not restricted or self.env.user.has_group("base.group_system")
        return {
            "restricted": restricted,
            "modules": {
                key: everything or self.env.user.has_group(f"lugatis_callcenter.group_module_{key}")
                for key in MODULES
            },
        }


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    lugatis_restrict_modules = fields.Boolean(
        "Lugatis modüllerini gruplara göre sınırla", config_parameter=PARAM
    )


class ResGroups(models.Model):
    _inherit = "res.groups"

    @api.model
    def _lugatis_categorize(self):
        """The module groups shown together under "Lugatis": in a category (Odoo 18)
        or, as each is an on/off of its own, each under its own privilege (Odoo 19)."""
        category = self.env.ref("lugatis_callcenter.module_category_lugatis")
        groups = self.env["ir.model.data"].search(
            [("module", "=", "lugatis_callcenter"), ("model", "=", "res.groups")]
        )
        groups = self.browse(groups.mapped("res_id")).exists()
        # The administrator has every module ("users" in Odoo 18, "user_ids" in 19).
        everything = self.env.ref("lugatis_callcenter.group_module_all")
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)
        members = "user_ids" if "user_ids" in self._fields else "users"
        if admin:
            everything.write({members: [(4, admin.id)]})
        if "category_id" in self._fields:
            groups.write({"category_id": category.id})
        elif "privilege_id" in self._fields and "res.groups.privilege" in self.env:
            Privilege = self.env["res.groups.privilege"].sudo()
            for group in groups:
                privilege = group.privilege_id or Privilege.search(
                    [("name", "=", group.name), ("category_id", "=", category.id)], limit=1
                )
                if not privilege:
                    privilege = Privilege.create({"name": group.name, "category_id": category.id})
                group.privilege_id = privilege
