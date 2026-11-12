<div align="center">

# 📡 freebie-tracker

**Radar bansos zero-token untuk AI agent.
Memantau daftar free tier dan komunitas deal di seluruh dunia, membandingkan
perubahan, dan hanya membangunkan agent saat ada temuan yang benar-benar layak diklaim.**

[![CI](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/wiskovic/freebie-tracker/actions/workflows/ci.yml)
[![last-commit](https://img.shields.io/github/last-commit/wiskovic/freebie-tracker)](https://github.com/wiskovic/freebie-tracker/commits/main)
[![repo-size](https://img.shields.io/github/repo-size/wiskovic/freebie-tracker)](https://github.com/wiskovic/freebie-tracker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

*Penariknya nol biaya jalan: tanpa token, tanpa API key, tanpa panggilan LLM.
Agent hanya memakai perhatian saat diff-nya memang layak.*

[English](README.md) | [简体中文](README.zh-CN.md) | [한국어](README.ko.md) | Bahasa Indonesia

</div>

---

Sisi mesinnya sengaja dibuat sederhana dan murah (Python standard library saja, tanpa API key, tanpa panggilan LLM), sisi penilaiannya urusan agent. Agent memverifikasi kandidat ke halaman resmi provider, menerapkan filter aman pemiliknya, lalu hanya melaporkan yang benar-benar layak diklaim.

## Kenapa

Free tier, kredit AI, subsidi GPU, dan kode giveaway tersebar di daftar kurasi Tiongkok, komunitas startup Korea, daftar developer Barat, dan postingan sosial yang hilang dalam hitungan jam. Manusia tidak bisa memantau semuanya. Agent bisa, asal memantaunya sendiri hampir nol biaya dan agent hanya memakai perhatian saat diff-nya tidak kosong.

Proyek ini menggeneralisasi satu setup yang sudah jalan di produksi: melintasi daftar kurasi Tiongkok (lanmao, baipiaoji, jidan), forum deal (LINUX DO, V2EX, NodeSeek), dan postingan pemburu di Facebook dan X, lalu menambahkan lapisan yang dilewatkan kebanyakan tracker, yaitu program dukungan dan subsidi AI berskala besar (AI Voucher Korea, komputasi IndiaAI India, EuroHPC Uni Eropa, dan lainnya), tempat alokasi gratis terbesar sebenarnya berada.

## Cara kerja

```
sources.json          registry: feed, halaman program, lahan sosial
     |
tracker.py            menarik semua feed, memotretnya, membandingkan
     |
state/last-diff.json  entri baru / berubah / hilang, per kategori
     |
agent (gerbang bangun)  hanya jalan saat sumber pemicu berubah;
                      memverifikasi tiap kandidat ke halaman resmi
                      provider, menerapkan filter aman, dedupe
                      lawan inventaris pemilik, lapor singkat
                      per kategori
```

Disiplin bangun adalah trik intinya: feed firehose (obrolan marketplace, blog software umum) tetap dibandingkan dan disimpan, tapi **tidak pernah membangunkan agent sendirian**. Hanya daftar kurasi dan forum khusus deal yang bisa. Di produksi, ini membuat biaya agent mendekati nol tanpa melewatkan hal yang penting.

## Mulai cepat

```bash
git clone https://github.com/wiskovic/freebie-tracker
cd freebie-tracker
python3 tracker.py --seed   # jalan pertama: menulis baseline
python3 tracker.py          # jalan berikutnya: tarik dan bandingkan
cat state/last-diff.json    # lihat yang berubah
```

Jadwalkan dengan cara apa pun yang platform agent kamu dukung (cron, webhook poller, systemd timer). Ritme 4 sampai 6 jam bekerja dengan baik; kode giveaway publik bisa mati dalam hitungan jam, jadi kaki sosial di `docs/agent-guide.md` penting untuk yang seperti itu.

## Bentuk outputnya

Satu kali jalan mencetak satu baris ringkasan dan menulis diff lengkap ke `state/last-diff.json`:

```json
{"sources_ok": 18, "sources_failed": [], "items_per_source": {"baipiaoji": 131, "lanmao": 341, "jidan": 40, "linuxdo": 25, "v2ex": 50, "lowendtalk": 100, "free-for-dev": 1379, "...": "..."}, "new_count": 22, "changed_count": 1, "removed_count": 22, "wake_new_count": 2, "wake_changed_count": 1}
```

Agent hanya bangun karena `wake_new_count + wake_changed_count` lebih besar dari nol, lalu memverifikasi, menyaring, dan melaporkan. Contoh laporan jadinya ada di `examples/report-example.md`.

## Kategori

Setiap sumber dan entri diberi tag: `ai`, `gpu`, `cloud`, `vps`, `database`, `dev-tools`, `saas`, `design`, `education`, `gov-programs`, `games`, `other`. Laporan mengelompokkan temuan per kategori, jadi pemilik bisa melihat misalnya hanya tawaran VM baru saat itu yang dia pedulikan. Lihat `docs/categories.md`.

## Sumber sekilas

| Lapisan | Contoh | Cara |
|---|---|---|
| Daftar kurasi (CN) | baipiaoji limits.json, lanmao offers, jidan | feed mesin |
| Forum deal | LINUX DO welfare, V2EX promotions, LowEndTalk offers, LowEndSpirit free offers | feed mesin |
| Firehose | NodeSeek, Appinn, ghxi, iPlaySoft, Slickdeals, OzBargain, Giveaway of the Day, LowEndBox | feed mesin, pasif |
| Daftar developer (global) | free-for.dev, free-ai-apis | feed mesin |
| Berita developer (KR) | GeekNews | feed mesin |
| Program dukungan besar | KR AI Voucher (NIPA/MSIT), K-Startup, IndiaAI, EuroHPC, J-Startup, AI Singapore | cek halaman oleh agent |
| Program startup berpagar | AWS Activate, Google Cloud for Startups, Microsoft for Startups, GitHub Student Pack | cek halaman oleh agent, berpagar |
| Lahan sosial | Akun pemburu di X, grup komunitas niche (Facebook, Discord, forum) yang berbagi free tier dan giveaway | kaki agent, saat bangun |

Registry lengkap beserta catatan: `sources.json`. Katalog yang enak dibaca manusia: `docs/sources.md`.

## Filter aman (ringkasan)

Satu entri di daftar adalah **petunjuk, bukan temuan**. Sebelum agent melaporkan apa pun sebagai bisa diklaim, dia wajib memverifikasi ke sumber resmi provider dan menolak:

- tawaran yang butuh kartu kredit yang tidak bisa atau tidak mau diberikan pemiliknya
- tawaran di balik verifikasi real-name atau KYC yang tidak bisa dilewati pemiliknya
- jual beli akun, patungan, kredit API berbagi atau relay, umpan token
- tawaran kedaluwarsa dan diskon berbayar yang menyamar jadi gratisan
- tawaran terkunci wilayah yang pemiliknya tidak memenuhi syaratnya

Filter ini berjalan dengan parameter keadaan pemiliknya (lihat `templates/profile.example.json`), bukan dengan mengandaikan semua pemilik menghadapi tembok yang sama. Filter lengkap dan manual operasi agent ada di `docs/agent-guide.md`.

## Struktur

```
tracker.py              penariknya (hanya stdlib)
sources.json            registry sumber (feed, halaman, sosial)
docs/agent-guide.md     cara agent menjalankan ini: loop, filter, laporan
docs/categories.md      taksonomi kategori
docs/sources.md         katalog sumber dengan catatan per wilayah
examples/               contoh laporan agent
templates/              template inventaris dan profil pemilik
state/                  snapshot dan diff runtime (diabaikan git)
```

## Status produksi

Deployment referensinya menjalankan persis kode ini. Agent-nya polling tiap 6 jam dari checkout repo ini, menyimpan snapshot dan inventaris pemiliknya di folder deployment privat di luar git, dan melaporkan temuan ke pemiliknya. Perubahan di sini diuji melawan snapshot live sebelum dirilis.

## Penafian

Semua yang surfaced alat ini adalah petunjuk yang belum terverifikasi sampai agent (atau pemiliknya) mengecek halaman resmi provider. Tawaran bisa berubah, kedaluwarsa, dan terkunci wilayah tanpa pemberitahuan. Jangan pernah memasukkan kredensial, kode, atau data pembayaran di mana pun kecuali situs provider itu sendiri, dan hanya atas instruksi eksplisit pemiliknya.

## Lisensi

MIT. Lihat `LICENSE`.
