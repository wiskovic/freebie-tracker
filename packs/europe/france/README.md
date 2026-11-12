# Country pack: Prancis

Country pack adalah lensa tersaring atas satu negara, bukan timbunan data negara itu. Setiap isi pack ini lolos uji masuk relevansi yang sama seperti registry: dia bisa memunculkan free tier, trial, kredit gratis, kode giveaway, atau sinyal komunitas yang layak ditindak, dipantau, dan diambil. Secara teknis pack ini divalidasi runner dengan aturan id dan format yang sama seperti registry sebelum dijalankan.

Pola lokal yang perlu diketahui lebih dulu: di Prancis, trial yang layak saat ini datang dari provider hosting kecil (hébergeur), dan mereka mengumumkannya di situs mereka sendiri dan server Discord mereka, bukan di forum yang punya feed. Tidak ada padanan Prancis untuk papan bansos sekelas LINUX DO yang punya feed mesin. Penanda terkuat dari trial yang bisa diklaim adalah frasa "sans CB" (tanpa kartu bank).

## Istilah pencarian lokal (terverifikasi di sumber Prancis yang hidup)

- Kata benda inti: "VPS gratuit", "hébergement gratuit", "serveur gratuit", "essai gratuit"
- Penanda tanpa kartu: "sans CB", "sans carte bancaire" (pasangan dengan presisi tertinggi buat saringan keamanan pemilik)
- Berburu kredit: "crédit offert", "crédit de X $"
- Frasa pengumuman komunitas: "offres gratuites", "100 % gratuit"
- Istilah payung, hanya berguna kalau digabung kata benda teknis: "bon plan", "code promo"
- Penanda negatif: "échantillons gratuits" artinya sampel produk konsumen; sumber yang didominasi istilah ini adalah kelas ritel.

Rumus istilah terkuat: (gratuit) digabung (VPS, hébergement, serveur), digabung (sans CB, sans carte bancaire).

## Feed mesin (terverifikasi hidup, dua duanya firehose)

- **Korben** (https://korben.info/feed): blog penemuan teknologi Prancis terbesar di ceruk alat dan layanan web. Dari 23 item terbarunya, 8 menyebut kata "gratuit" di badan artikelnya; liputan alat dan SaaS gratisnya rutin. Firehose: dibaca saat ada wake, tidak pernah jadi pemicu.
- **Sebsauvage, Liens en vrac** (https://sebsauvage.net/links/?do=rss): blog tautan satu kurator manusia yang sudah berjalan puluhan tahun. Kepadatannya rendah (sekitar 4 sinyal layanan gratis yang eksplisit dari 50 item) tapi kualitas kurasinya tinggi dan kadang persis on-category, contohnya layanan DDNS gratis. Firehose.

## Ladang perburuan kaki agent

- **DISBOARD, daftar server Discord, tag "vps", filter Prancis** (https://disboard.org/servers/tag/vps?fl=fr): habitat para hébergeur kecil Prancis. Listing yang terlihat saat pack ini dibuat antara lain host yang mengiklankan "des offres gratuites pour commencer" dan satu proyek komunitas yang memberi hosting gratis 100 persen dari infrastruktur di Prancis, pendaftarannya lewat Discord. Di sinilah trial hosting Prancis benar benar lahir; agent membaca listing ini berkala dan memeriksa hébergeur yang baru muncul beserta situs mereka.
- **TeamKit** (https://www.teamkit.fr): proyek komunitas Prancis yang membuatkan server game dedicated gratis di mesin di Prancis, tanpa abonnement, tanpa kartu, permintaannya lewat formulir singkat yang dibaca manusia. Kecil dan khusus game, tapi contoh hidup pola "serveur gratuit communautaire".
- **Direktori CHATONS** (https://chatons.org): katalog kolektif hosting alternatif dan asosiatif Prancis. Bukan feed; ini peta statis. Panen daftar hébergeur anggotanya sekali, lalu pantau situs mereka masing masing buat layanan gratis dan trial baru.

## Preset GDELT

API DOC milik GDELT itu gratis dan tanpa kunci, dan filternya cocok dengan bentuk pack:

- Query inti: ("VPS gratuit" OR "hébergement gratuit" OR "serveur gratuit" OR "essai gratuit") sourcecountry:FR sourcelang:fra
- Varian tanpa kartu: query inti ditambah AND ("sans CB" OR "sans carte bancaire")
- Setelan sapuan: mode ArtList, format json, sort DateDesc, maxrecords 25, timespan 1m. Buat sapuan pertama, lebarkan timespan preset nya jadi 3m di pack.json.

Catatan pakai: GDELT membatasi satu request per 5 detik per IP. Runner memanggil semua preset dalam satu larian dengan jeda 6 detik antar panggilan. Dari jaringan yang IP nya dipakai bersama, panggilannya gampang kena batas itu dan tercatat sebagai kegagalan sumber tanpa merusak larian; jawaban GDELT yang kosong itu sah dan snapshot nya dipertahankan. Jalankan dari egress yang lebih sepi atau sebagai pekerjaan terjadwal beberapa kali sehari.