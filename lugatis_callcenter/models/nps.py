import secrets

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LugatisNps(models.Model):
    """Post-call satisfaction survey (0–10). The customer answers by clicking a
    score in the mail (no login); the answer is written to the linked record's
    chatter (CRM opportunity, sale, contact…)."""

    _name = "lugatis.nps"
    _description = "Çağrı sonrası memnuniyet anketi"
    _order = "create_date desc"

    partner_id = fields.Many2one("res.partner", "Müşteri", required=True, index=True)
    user_id = fields.Many2one("res.users", "Temsilci", default=lambda self: self.env.user, index=True)
    res_model = fields.Char("Kayıt modeli")
    res_id = fields.Many2oneReference("Kayıt ID", model_field="res_model")
    call_key = fields.Char("Görüşme anahtarı", index=True)
    token = fields.Char(required=True, copy=False, index=True, default=lambda self: secrets.token_urlsafe(24))
    score = fields.Integer("Puan", default=-1)
    comment = fields.Text("Yorum")
    state = fields.Selection([("sent", "Gönderildi"), ("answered", "Cevaplandı")], default="sent", required=True)
    answered_at = fields.Datetime("Cevap zamanı")
    category = fields.Selection(
        [("promoter", "Destekçi (9–10)"), ("passive", "Pasif (7–8)"), ("detractor", "Eleştirmen (0–6)")],
        compute="_compute_category", store=True,
    )

    _sql_constraints = [("token_unique", "unique(token)", "Anket bağlantısı benzersiz olmalı.")]

    @api.depends("score")
    def _compute_category(self):
        for r in self:
            r.category = (
                False if r.score < 0 else "promoter" if r.score >= 9 else "passive" if r.score >= 7 else "detractor"
            )

    @api.model
    def send_survey(self, partner_id, res_model=False, res_id=False, call_key=False):
        """Creates the survey and mails it to the customer; returns its id."""
        partner = self.env["res.partner"].browse(partner_id).exists()
        if not partner or not partner.email:
            raise UserError(_("Müşterinin e-posta adresi yok."))
        if call_key and self.search_count([("call_key", "=", call_key)]):
            return self.search([("call_key", "=", call_key)], limit=1).id
        survey = self.create({
            "partner_id": partner.id,
            "res_model": res_model or False,
            "res_id": res_id or False,
            "call_key": call_key or False,
        })
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        company = self.env.company
        cells = "".join(
            f'<td style="padding:2px"><a href="{base}/lugatis/nps/{survey.token}/{n}" '
            f'style="display:inline-block;width:30px;padding:8px 0;text-align:center;border-radius:6px;'
            f'background:{"#ef4444" if n <= 6 else "#f59e0b" if n <= 8 else "#22c55e"};color:#fff;'
            f'text-decoration:none;font-weight:bold">{n}</a></td>'
            for n in range(11)
        )
        body = Markup(
            "<p>Merhaba {name},</p><p>Az önce {user} ile yaptığınız görüşme için teşekkür ederiz. "
            "<b>{company}</b>'i bir arkadaşınıza tavsiye etme olasılığınız nedir?</p>"
            "<table><tr>{cells}</tr></table>"
            '<p style="color:#888;font-size:12px">0 = hiç, 10 = kesinlikle. Tek tıklama yeterli.</p>'
        ).format(name=escape(partner.name), user=escape(self.env.user.name), company=escape(company.name),
                 cells=Markup(cells))
        self.env["mail.mail"].sudo().create({
            "subject": f"{company.name}: görüşmemizi nasıl buldunuz?",
            "body_html": body,
            "email_to": partner.email_formatted,
            "email_from": company.email_formatted or self.env.user.email_formatted,
            "auto_delete": True,
        }).send()
        return survey.id

    def record_answer(self, score, comment=None):
        """Called by the public page (sudo): stores the score once, notes it on the record."""
        self.ensure_one()
        first = self.state == "sent"
        values = {"score": max(0, min(10, int(score))), "state": "answered"}
        if first:
            values["answered_at"] = fields.Datetime.now()
        if comment is not None:
            values["comment"] = comment[:2000]
        self.write(values)
        target = self.partner_id
        if self.res_model and self.res_id and self.res_model in self.env:
            linked = self.env[self.res_model].browse(self.res_id).exists()
            if linked and hasattr(linked, "message_post"):
                target = linked
        text = Markup("📊 Memnuniyet anketi: <b>{score}/10</b> ({cat}){comment}").format(
            score=self.score,
            cat=dict(self._fields["category"].selection).get(self.category, ""),
            comment=Markup("<br/>") + escape(self.comment) if self.comment else "",
        )
        if first or comment:
            target.message_post(body=text, message_type="comment", subtype_xmlid="mail.mt_note",
                                author_id=self.partner_id.id)

    @api.model
    def stats(self, since):
        """NPS since a UTC datetime: score (−100…100), answers, promoters, detractors, sent."""
        answered = self.search([("state", "=", "answered"), ("answered_at", ">=", since)])
        n = len(answered)
        pro = len(answered.filtered(lambda r: r.score >= 9))
        det = len(answered.filtered(lambda r: r.score <= 6))
        sent = self.search_count([("create_date", ">=", since)])
        return {"score": round((pro - det) * 100 / n) if n else None, "answers": n,
                "promoters": pro, "detractors": det, "sent": sent}
