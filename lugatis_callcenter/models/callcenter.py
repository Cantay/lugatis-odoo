from odoo import api, fields, models

COLOR_HELP = "Renk, ör. #22c55e (Lugatis'te nokta ve şerit rengi)."


class LugatisCallResult(models.Model):
    _name = "lugatis.call.result"
    _description = "Çağrı sonuç kodu"
    _order = "sequence, id"

    name = fields.Char("Ad", required=True, translate=True)
    code = fields.Char("Kod", required=True, help="Raporlar için kısa kod, ör. SUCCESSFUL.")
    color_hex = fields.Char("Renk", default="#22c55e", help=COLOR_HELP)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class LugatisCallTag(models.Model):
    _name = "lugatis.call.tag"
    _description = "Çağrı etiketi"
    _order = "sequence, name"

    name = fields.Char("Ad", required=True, translate=True)
    color_hex = fields.Char("Renk", default="#3b82f6", help=COLOR_HELP)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class LugatisAgentStatus(models.Model):
    _name = "lugatis.agent.status"
    _description = "Kullanıcı (temsilci) durumu"
    _order = "sequence, id"

    name = fields.Char("Ad", required=True, translate=True)
    kind = fields.Selection(
        [("available", "Uygun — çağrı alır"), ("busy", "Meşgul — gelen çağrı düşmez"), ("break", "Mola — mesai molası")],
        string="Tür",
        required=True,
        default="busy",
    )
    color_hex = fields.Char("Renk", default="#6b7280", help=COLOR_HELP)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class LugatisCall(models.Model):
    _name = "lugatis.call"
    _description = "Telefon görüşmesi (Lugatis)"
    _order = "start desc, id desc"
    _rec_name = "number"

    user_id = fields.Many2one("res.users", "Temsilci", default=lambda self: self.env.user, index=True)
    direction = fields.Selection([("in", "Gelen"), ("out", "Giden")], "Yön", required=True)
    number = fields.Char("Numara")
    partner_id = fields.Many2one("res.partner", "Kişi", index=True)
    res_model = fields.Char("Kayıt modeli")
    res_id = fields.Many2oneReference("Kayıt ID", model_field="res_model")
    res_name = fields.Char("Kayıt")
    start = fields.Datetime("Başlangıç", required=True, default=fields.Datetime.now, index=True)
    duration = fields.Integer("Süre (sn)")
    duration_minutes = fields.Float("Süre (dk)", compute="_compute_duration_minutes", store=True)
    state = fields.Selection(
        [
            ("answered", "Görüşüldü"),
            ("missed", "Cevapsız"),
            ("rejected", "Reddedildi"),
            ("cancelled", "Vazgeçildi"),
            ("failed", "Kurulamadı"),
        ],
        "Durum",
        required=True,
        default="answered",
    )
    result_id = fields.Many2one("lugatis.call.result", "Sonuç kodu", index=True)
    tag_ids = fields.Many2many("lugatis.call.tag", string="Etiketler")
    note = fields.Text("Açıklama")
    mos = fields.Float("Ses kalitesi (MOS)", digits=(2, 1))
    client_key = fields.Char("İstemci anahtarı", index=True, copy=False, help="Mükerrer kaydı önler.")

    @api.depends("duration")
    def _compute_duration_minutes(self):
        for call in self:
            call.duration_minutes = (call.duration or 0) / 60.0


class LugatisAgentLog(models.Model):
    _name = "lugatis.agent.log"
    _description = "Kullanıcı durum geçmişi"
    _order = "start desc, id desc"

    user_id = fields.Many2one("res.users", "Temsilci", required=True, index=True)
    status_id = fields.Many2one("lugatis.agent.status", "Durum", required=True)
    kind = fields.Selection(related="status_id.kind", store=True)
    start = fields.Datetime("Başlangıç", required=True)
    end = fields.Datetime("Bitiş")
    duration_minutes = fields.Float("Süre (dk)", compute="_compute_duration_minutes", store=True)

    @api.depends("start", "end")
    def _compute_duration_minutes(self):
        for log in self:
            if log.start and log.end:
                log.duration_minutes = (log.end - log.start).total_seconds() / 60.0
            else:
                log.duration_minutes = 0.0

    @api.model
    def lg_set_status(self, status_id):
        """Sets the current user's status: closes the open entry, opens a new one."""
        now = fields.Datetime.now()
        user = self.env.user
        self.sudo().search([("user_id", "=", user.id), ("end", "=", False)]).write({"end": now})
        status = self.env["lugatis.agent.status"].browse(status_id).exists()
        if status:
            self.sudo().create({"user_id": user.id, "status_id": status.id, "start": now})
        user.sudo().write({"lg_status_id": status.id or False, "lg_status_since": now})
        return True


class ResUsers(models.Model):
    _inherit = "res.users"

    lg_status_id = fields.Many2one("lugatis.agent.status", "Lugatis durumu", readonly=True)
    lg_status_since = fields.Datetime("Durum başlangıcı", readonly=True)
