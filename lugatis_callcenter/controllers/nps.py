from markupsafe import Markup, escape

from odoo import http
from odoo.http import request

PAGE = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Teşekkürler</title>
<style>body{{font-family:system-ui,sans-serif;max-width:520px;margin:60px auto;padding:0 20px;color:#222}}
textarea{{width:100%;min-height:90px;font:inherit}}button{{padding:10px 18px;border:0;border-radius:8px;
background:#21c063;color:#fff;font:inherit}}</style></head><body>{content}</body></html>"""


class NpsController(http.Controller):
    def _survey(self, token):
        return request.env["lugatis.nps"].sudo().search([("token", "=", token)], limit=1)

    @http.route("/lugatis/nps/<string:token>/<int:score>", type="http", auth="public", website=False)
    def answer(self, token, score, **kw):
        survey = self._survey(token)
        if not survey or not 0 <= score <= 10:
            return request.make_response(PAGE.format(content="<p>Bu anket bağlantısı geçersiz.</p>"))
        survey.record_answer(score)
        content = Markup(
            "<h2>Teşekkür ederiz!</h2><p>Puanınız: <b>{score}/10</b></p>"
            '<form method="post" action="/lugatis/nps/{token}/comment">'
            "<p>Eklemek istediğiniz bir şey var mı? (isteğe bağlı)</p>"
            '<textarea name="comment"></textarea><p><button type="submit">Gönder</button></p></form>'
        ).format(score=survey.score, token=escape(token))
        return request.make_response(PAGE.format(content=content))

    @http.route("/lugatis/nps/<string:token>/comment", type="http", auth="public", methods=["POST"],
                csrf=False, website=False)
    def comment(self, token, comment="", **kw):
        survey = self._survey(token)
        if survey and survey.state == "answered" and comment.strip():
            survey.record_answer(survey.score, comment.strip())
        return request.make_response(PAGE.format(content="<h2>Teşekkür ederiz!</h2><p>Yorumunuz iletildi.</p>"))
