import base64
import hashlib

from odoo import api, fields, models


class LugatisPlugin(models.Model):
    """A Lugatis desktop plugin (.wasm) published to the company's users.
    The app shows its permissions and asks each user before installing it."""

    _name = "lugatis.plugin"
    _description = "Lugatis eklentisi"
    _order = "name"

    name = fields.Char("Ad", required=True)
    key = fields.Char("Anahtar", required=True, help="Eklentinin kendi bildirdiği anahtar")
    version = fields.Char("Sürüm")
    description = fields.Text("Açıklama")
    author = fields.Char("Yazar")
    wasm = fields.Binary("Eklenti dosyası (.wasm)", attachment=True, required=True)
    wasm_name = fields.Char("Dosya adı")
    sha256 = fields.Char("SHA-256", compute="_compute_sha256", store=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [("key_unique", "unique(key)", "Bu anahtarla bir eklenti zaten var.")]

    @api.depends("wasm")
    def _compute_sha256(self):
        for plugin in self:
            raw = base64.b64decode(plugin.with_context(bin_size=False).wasm or b"")
            plugin.sha256 = hashlib.sha256(raw).hexdigest() if raw else False
