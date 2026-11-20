#!/usr/bin/env python3
"""Generate the 4 n8n workflow JSONs of the UMKM pack.

Each workflow is a standard n8n export (nodes + connections) that imports
cleanly into any n8n instance; credential fields are intentionally left as
placeholders for the buyer to connect (Google Sheets, Telegram, Gmail).
"""
import json
import os
import uuid

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workflows")


def nid():
    return str(uuid.uuid4())


def node(name, ntype, tver, x, y, params=None, creds=None):
    n = {"parameters": params or {}, "id": nid(), "name": name, "type": ntype,
         "typeVersion": tver, "position": [x, y]}
    if creds:
        n["credentials"] = creds
    return n


def sticky(text, x, y, w=460, h=180):
    return {"parameters": {"content": text, "height": h, "width": w, "color": 4},
            "id": nid(), "name": "Sticky Note", "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1, "position": [x, y]}


def wf(name, nodes, conns, tags):
    return {"name": name, "nodes": nodes, "connections": conns, "active": False,
            "settings": {"executionOrder": "v1"}, "tags": [{"name": t} for t in tags],
            "meta": {"templateCredsSetupCompleted": False}}


def link(a, b):
    return {a: {"main": [[{"node": b, "type": "main", "index": 0}]]}}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out.setdefault(k, {"main": []})
            out[k]["main"].extend(v["main"])
    return out


GS_CREDS = {"googleSheetsOAuth2Api": {"id": "", "name": "Google Sheets account"}}
TG_CREDS = {"telegramApi": {"id": "", "name": "Telegram account"}}
GM_CREDS = {"gmailOAuth2": {"id": "", "name": "Gmail account"}}

# ---------------------------------------------------------------- 1. Orders
n1 = [
    sticky("## 1 — Catat Order Otomatis\nOrder masuk lewat webhook (form order / gateway WhatsApp) → tersimpan rapi ke Google Sheets → pemilik toko dapat notifikasi Telegram.\n\n**Setup:** sambungkan Google Sheets & Telegram, ganti ID sheet dan chat ID. Lihat PANDUAN.md.", -220, -40, 520, 200),
    node("Webhook Order Masuk", "n8n-nodes-base.webhook", 2, 300, 240,
         {"httpMethod": "POST", "path": "order-masuk", "responseMode": "lastNode", "options": {}}),
    node("Rapikan Data Order", "n8n-nodes-base.set", 3.4, 520, 240,
         {"assignments": {"assignments": [
             {"id": "a1", "name": "tanggal", "type": "string", "value": "={{ $now.format('yyyy-MM-dd HH:mm') }}"},
             {"id": "a2", "name": "nama", "type": "string", "value": "={{ $json.nama }}"},
             {"id": "a3", "name": "telepon", "type": "string", "value": "={{ $json.telepon }}"},
             {"id": "a4", "name": "produk", "type": "string", "value": "={{ $json.produk }}"},
             {"id": "a5", "name": "jumlah", "type": "number", "value": "={{ $json.jumlah }}"},
             {"id": "a6", "name": "total", "type": "number", "value": "={{ $json.total }}"},
             {"id": "a7", "name": "status", "type": "string", "value": "BARU"}]},
          "options": {}}),
    node("Simpan ke Google Sheets", "n8n-nodes-base.googleSheets", 4.2, 740, 240,
         {"documentId": {"__rl": True, "value": "GANTI_ID_SHEET", "mode": "url"},
          "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": "Orders"},
          "columns": {"mappingMode": "autoMapInputData", "matchingColumns": []},
          "options": {}}, GS_CREDS),
    node("Notifikasi Telegram Pemilik", "n8n-nodes-base.telegram", 1.2, 960, 240,
         {"chatId": "GANTI_CHAT_ID", "text": "=🛎️ Order baru!\n{{ $json.nama }} — {{ $json.produk }} x{{ $json.jumlah }}\nTotal: Rp{{ $json.total }}\nStatus: {{ $json.status }}",
          "additionalFields": {}}, TG_CREDS),
]
c1 = merge(link("Webhook Order Masuk", "Rapikan Data Order"),
           link("Rapikan Data Order", "Simpan ke Google Sheets"),
           link("Simpan ke Google Sheets", "Notifikasi Telegram Pemilik"))

# ------------------------------------------------------- 2. Payment reminder
n2 = [
    sticky("## 2 — Pengingat Pembayaran Otomatis\nSetiap pagi workflow membaca order berstatus BELUM LUNAS yang sudah lewat jatuh tempo, lalu mengirim pengingat sopan ke pelanggan (Telegram; untuk WhatsApp ganti node terakhir dengan HTTP Request ke gateway WA — contoh di PANDUAN.md) dan menandai kolom diingatkan.\n\n**Setup:** sesuaikan nama sheet & kolom, atur jam jalan.", -220, -40, 560, 220),
    node("Setiap Pagi 08:00", "n8n-nodes-base.scheduleTrigger", 1.2, 300, 240,
         {"rule": {"interval": [{"field": "cronExpression", "expression": "0 8 * * *"}]}}),
    node("Baca Order Belum Lunas", "n8n-nodes-base.googleSheets", 4.2, 520, 240,
         {"documentId": {"__rl": True, "value": "GANTI_ID_SHEET", "mode": "url"},
          "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": "Orders"},
          "filtersUI": {"values": [{"lookupColumn": "status", "lookupValue": "BELUM LUNAS"}]},
          "options": {}}, GS_CREDS),
    node("Sudah Jatuh Tempo?", "n8n-nodes-base.if", 2.2, 740, 240,
         {"conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
                         "conditions": [{"id": "c1", "leftValue": "={{ $json.jatuh_tempo }}",
                                         "rightValue": "={{ $now.format('yyyy-MM-dd') }}",
                                         "operator": {"type": "string", "operation": "notEquals"}}],
                         "combinator": "and"}, "options": {}}),
    node("Kirim Pengingat", "n8n-nodes-base.telegram", 1.2, 960, 140,
         {"chatId": "={{ $json.chat_id }}",
          "text": "=Halo {{ $json.nama }} 🙏 Mengingatkan dengan sopan: pembayaran order {{ $json.produk }} sebesar Rp{{ $json.total }} jatuh tempo {{ $json.jatuh_tempo }}. Jika sudah membayar, abaikan pesan ini. Terima kasih!",
          "additionalFields": {}}, TG_CREDS),
    node("Tandai Diingatkan", "n8n-nodes-base.googleSheets", 4.2, 960, 380,
         {"operation": "update",
          "documentId": {"__rl": True, "value": "GANTI_ID_SHEET", "mode": "url"},
          "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": "Orders"},
          "columns": {"mappingMode": "defineBelow", "value": {"diingatkan": "={{ $now.format('yyyy-MM-dd') }}"},
                      "matchingColumns": ["telepon"]},
          "options": {}}, GS_CREDS),
]
c2 = merge(link("Setiap Pagi 08:00", "Baca Order Belum Lunas"),
           link("Baca Order Belum Lunas", "Sudah Jatuh Tempo?"),
           link("Kirim Pengingat", "Tandai Diingatkan"),
           {"Sudah Jatuh Tempo?": {"main": [[{"node": "Kirim Pengingat", "type": "main", "index": 0}], []]}})

# ------------------------------------------------------------ 3. Daily recap
n3 = [
    sticky("## 3 — Rekap Penjualan Harian\nSetiap malam pukul 21:00, workflow menjumlah penjualan hari ini dari Google Sheets dan mengirim rekap ringkas ke Telegram pemilik: total order, total omzet, produk terlaris.\n\n**Setup:** sesuaikan sheet & chat ID.", -220, -40, 520, 200),
    node("Setiap Malam 21:00", "n8n-nodes-base.scheduleTrigger", 1.2, 300, 240,
         {"rule": {"interval": [{"field": "cronExpression", "expression": "0 21 * * *"}]}}),
    node("Baca Order Hari Ini", "n8n-nodes-base.googleSheets", 4.2, 520, 240,
         {"documentId": {"__rl": True, "value": "GANTI_ID_SHEET", "mode": "url"},
          "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": "Orders"},
          "filtersUI": {"values": [{"lookupColumn": "tanggal", "lookupValue": "={{ $now.format('yyyy-MM-dd') }}"}]},
          "options": {}}, GS_CREDS),
    node("Hitung Rekap", "n8n-nodes-base.code", 2, 740, 240,
         {"jsCode": "const rows = $input.all().map(i => i.json);\nconst omzet = rows.reduce((s, r) => s + (Number(r.total) || 0), 0);\nconst perProduk = {};\nfor (const r of rows) perProduk[r.produk] = (perProduk[r.produk] || 0) + (Number(r.jumlah) || 0);\nconst terlaris = Object.entries(perProduk).sort((a, b) => b[1] - a[1])[0];\nreturn [{ json: { tanggal: $now.format('yyyy-MM-dd'), order: rows.length, omzet, terlaris: terlaris ? `${terlaris[0]} (${terlaris[1]} terjual)` : '-' } }];"}),
    node("Kirim Rekap ke Pemilik", "n8n-nodes-base.telegram", 1.2, 960, 240,
         {"chatId": "GANTI_CHAT_ID",
          "text": "=📊 Rekap {{ $json.tanggal }}\nOrder masuk: {{ $json.order }}\nOmzet: Rp{{ $json.omzet }}\nTerlaris: {{ $json.terlaris }}",
          "additionalFields": {}}, TG_CREDS),
]
c3 = merge(link("Setiap Malam 21:00", "Baca Order Hari Ini"),
           link("Baca Order Hari Ini", "Hitung Rekap"),
           link("Hitung Rekap", "Kirim Rekap ke Pemilik"))

# ------------------------------------------------------------- 4. Lead reply
n4 = [
    sticky("## 4 — Balas Lead Otomatis\nLead baru dari webhook (iklan / form / link bio) langsung: tercatat ke Sheets CRM sederhana, menerima email sambutan, dan pemilik toko diberi tahu via Telegram.\n\n**Setup:** sambungkan Google Sheets, Gmail & Telegram; sesuaikan isi email.", -220, -40, 520, 200),
    node("Webhook Lead Baru", "n8n-nodes-base.webhook", 2, 300, 240,
         {"httpMethod": "POST", "path": "lead-baru", "responseMode": "lastNode", "options": {}}),
    node("Simpan Lead ke Sheets", "n8n-nodes-base.googleSheets", 4.2, 520, 240,
         {"documentId": {"__rl": True, "value": "GANTI_ID_SHEET_CRM", "mode": "url"},
          "sheetName": {"__rl": True, "value": "gid=0", "mode": "list", "cachedResultName": "Leads"},
          "columns": {"mappingMode": "autoMapInputData", "matchingColumns": []},
          "options": {}}, GS_CREDS),
    node("Email Sambutan", "n8n-nodes-base.gmail", 2.1, 740, 140,
         {"email": "={{ $json.email }}", "subject": "Terima kasih sudah menghubungi kami!",
          "emailType": "text",
          "message": "=Halo {{ $json.nama }}, terima kasih sudah menghubungi kami. Tim kami akan membalas dalam 1x24 jam kerja. Jika mendesak, balas email ini atau chat kami kembali.",
          "options": {}}, GM_CREDS),
    node("Beri Tahu Pemilik", "n8n-nodes-base.telegram", 1.2, 740, 380,
         {"chatId": "GANTI_CHAT_ID",
          "text": "=🌱 Lead baru: {{ $json.nama }} ({{ $json.email }}) — sumber: {{ $json.sumber }}",
          "additionalFields": {}}, TG_CREDS),
]
c4 = merge(link("Webhook Lead Baru", "Simpan Lead ke Sheets"),
           link("Simpan Lead ke Sheets", "Email Sambutan"),
           link("Simpan Lead ke Sheets", "Beri Tahu Pemilik"))

PACK = [
    ("01-catat-order-otomatis.json", wf("UMKM 1 — Catat Order Otomatis", n1, c1, ["umkm", "order"])),
    ("02-pengingat-pembayaran.json", wf("UMKM 2 — Pengingat Pembayaran", n2, c2, ["umkm", "reminder"])),
    ("03-rekap-penjualan-harian.json", wf("UMKM 3 — Rekap Penjualan Harian", n3, c3, ["umkm", "rekap"])),
    ("04-balas-lead-otomatis.json", wf("UMKM 4 — Balas Lead Otomatis", n4, c4, ["umkm", "lead"])),
]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fname, data in PACK:
        json.dump(data, open(os.path.join(OUT, fname), "w"), indent=2, ensure_ascii=False)
        print("wrote", fname, len(data["nodes"]), "nodes")
