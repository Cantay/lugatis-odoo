# Lugatis Odoo modülleri (Odoo 19.0)

[Lugatis](https://www.lugatsoft.com) masaüstü uygulamasının Odoo tarafı. Lugatis; sohbet, e-posta,
telefon, CRM, kasa, masraf ve projeyi şirketin Odoo'su üzerinde tek pencerede toplar. Bu modüller
Odoo'ya uygulamanın ihtiyaç duyduğu kayıtları ve ayarları ekler; Lugatis olmadan da Odoo içinden
kullanılabilirler.

| Modül | Ne ekler | Bağımlılık |
|---|---|---|
| `lugatis_callcenter` | Çağrı kayıtları, sonuç kodları ve etiketler, kullanıcı (temsilci) durumları ve günlüğü, NPS anketleri (genel bağlantıyla puan ve yorum), eklentiler (WebAssembly), Ayarlar → Lugatis'ten modül bazlı erişim (gruplar) | `base`, `mail` |
| `lugatis_project` | Görevlere **Planlanan başlangıç**; Lugatis'in Gantt görünümü başlangıç + ayrılan süre ile planlar (Odoo Enterprise'ın `planned_date_begin` alanı varsa o kullanılır) | `project` |

## Kurulum

1. Bu dalı (`19.0`) Odoo'nun eklenti yollarından birine klonlayın:
   ```sh
   git clone -b 19.0 https://github.com/Cantay/lugatis-odoo.git
   ```
2. `addons_path`'e ekleyin, Odoo'yu yeniden başlatın.
3. Uygulamalar → *Uygulama listesini güncelle* → "Lugatis" arayıp kurun.

Desteklenen sürümler: dal başına bir Odoo sürümü (`18.0`, `19.0`).

## Lisans

[LGPL-3](LICENSE). © Lugatsoft.

---

# Lugatis Odoo modules (Odoo 19.0)

The Odoo side of the [Lugatis](https://www.lugatsoft.com) desktop app, which brings chat, mail,
phone, CRM, point of sale, expenses and projects together on a company's Odoo. The modules also
work on their own inside Odoo.

- `lugatis_callcenter`: call log, outcome codes and tags, agent statuses and log, NPS surveys
  (public answer links), WebAssembly plugins, per-module access groups (Settings → Lugatis).
  Depends on `base`, `mail`.
- `lugatis_project`: a **planned start** on tasks, used with allocated hours by the Lugatis
  Gantt view (Odoo Enterprise's `planned_date_begin` is used when present). Depends on `project`.

Install: clone this branch into an addons path, update the apps list, install "Lugatis".
One branch per Odoo series (`18.0`, `19.0`). License: LGPL-3.
