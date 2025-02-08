# pengujian_data.py
PENGUJIAN_DATA = {
    "diskrit_18_19_20": {
        "ground_truth": [
            {
                "title": "jokowi, kampanye, pilkada, Etis, hak, masyarakat",
                "source": "https://nasional.kompas.com/read/2024/10/30/08214651/jokowi-dan-kampanye-pilkada-2024-etis-atau-tidak-jadi-hak-masyarakat",
                "date": "30 Oktober 2024",
                "tweet": "calon gubernur pilkada jakarta bekas xl pimpin daerah layak pimpin jakarta hasil kerja pimpin jawa barat banyak memangkkan bangun",
                "trending_topics": "pilkada, debat, hasil, calon, gubernur, jateng, survei, jawa, lawan"
            },
            {
                "title": "relawan, calon, kepala, daerah, jokowi, jurkamp",
                "source": "https://nasional.kompas.com/read/2024/11/02/19160911/relawan-bilang-banyak-calon-kepala-daerah-minta-jokowi-jadi-juru-kampanye",
                "date": "30 Oktober 2024",
                "tweet": "debat pilkada jateng ahmad luthfi singgung sikap jokowi hingga sebut perintah prabowo",
                "trending_topics": "pilkada, jateng, lihat, masyarakat"
            },
            {
                "title": "calon, bupati, pamekasan, dilaporkan, bagi-bagi, uang, sembako",
                "source": "https://surabaya.kompas.com/read/2024/11/01/183508878/2-calon-bupati-pamekasan-dilaporkan-bagi-bagi-uang-dan-sembako",
                "date": "1 November 2024",
                "tweet": "sangka per oktober buzzer jokowi hbis kontrak nyata meleset mrka makin banyak muncul mungkin panjang kelar pilkada nov calon usung moncer",
                "trending_topics": "pilkada, jakarta, jokowi, pilih, dki, menang, solo"
            },
            {
                "title": "debat, pilkada, jateng, luthfi, cawagub, hendi, penonton, ricuh",
                "source": "https://regional.kompas.com/read/2024/10/30/205248678/debat-pilkada-jateng-luthfi-salah-sebut-nama-cawagubnya-jadi-hendi-penonton",
                "date": "30 Oktober 2024",
                "tweet": "kemarin dinaikin narasi pilkada adem gegara uang siapa monas matsuri beneran jadi patah semua narasi",
                "trending_topics": "pilkada, debat, uang, bikin"
            },
            {
                "title": "ahmad luthfi, singgung, jokowi, prabowo, debat, pilkada, jateng",
                "source": "https://www.tempo.co/politik/ahmad-luthfi-singgung-nama-jokowi-dan-prabowo-di-debat-pilkada-jawa-tengah-1161799",
                "date": "30 Oktober 2024",
                "tweet": "warga pinrang sukses pilkada menang nomor",
                "trending_topics": "pilkada, dukung, menang, prabowo, jakarta, putar, kali, coblos"
            },
            {
                "title": "projo, dukung, ridwan kamil-suswono, pilkada, jakarta",
                "source": "https://www.tempo.co/politik/projo-dukung-ridwan-kamil-suswono-di-pilkada-jakarta-1161818",
                "date": "30 Oktober 2024",
                "tweet": "bupati masyarakat pokus pilkada dua anak maju pilkada maklum bangun dinasty kecil lan",
                "trending_topics": "pilkada, calon, pilih, daerah, gubernur, pimpin, bupati, wakil, kepala"
            },
            {
                "title": "mobilisasi, kepala, desa, marak, menjelang, pencoblosan, pilkada",
                "source": "https://www.tempo.co/newsletter/mobilisasi-kepala-desa-marak-menjelang-pencoblosan-pilkada-1162960",
                "date": "2 November 2024",
                "tweet": "hari tuju pilkada serentak november",
                "trending_topics": "pilkada, serentak, masyarakat, laksana, aman, kota, kabupaten, november, damai, jelang"
            },
            {
                "title": "debat, perdana, pilkada, kota, bogor, digelar, november",
                "source": "https://megapolitan.kompas.com/read/2024/10/31/13240521/debat-perdana-pilkada-kota-bogor-digelar-8-november-2024",
                "date": "31 Oktober 2024",
                "tweet": "dukung luthfi gus yasin saat generasi muda suara pilkada",
                "trending_topics": "pilkada, damai, jaga, muda, generasi, aman, suara, sukses, ayo, demokrasi, dukung, luthfi, yasin, gus, hoaks, papua"
            },
            {
                "title": "hasil, survei, pilkada, jabar, dedi-erwan, unggul, daerah, nonbasis",
                "source": "https://bandung.kompas.com/read/2024/10/30/064108878/3-hasil-survei-pilkada-jawa-barat-dedi-erwan-unggul-di-daerah-nonbasis",
                "date": "30 Oktober 2024",
                "tweet": "sangat penting revisi uu kpk revisi uu pemilu uu pilkada uu partai politik batas masa urus coba bayang atur revisi percaya pemilu pilkada",
                "trending_topics": "pilkada, partai, calon, pilpres, kampanye, rakyat, pemilu"
            },
            {
                "title": "survei, smrc, andika-hendi, persen, luthfi-yasin, persaingan, pilkada, jateng, ketat",
                "source": "https://regional.kompas.com/read/2024/11/01/163401078/survei-smrc-andika-hendi-raih-481-persen-luthfi-yasin-475-persen-persaingan",
                "date": "1 November 2024",
                "tweet": "habis presiden jurkam pilkada lumayan giat",
                "trending_topics": "pilkada, debat, presiden, jurkam"
            },

        ],
        "metrics": {
            "topic_recall": {
                "value": 0.6,
                "fraction": "6/10"
            },
            "keyword_precision": {
                "value": 0.517857143,
                "fraction": "29/56"
            },
            "keyword_recall": {
                "value": 0.568627451,
                "fraction": "29/51"
            }
        }
    },
    "diskrit_22_23_24": {
        "ground_truth": [
            {
                "title": "debat, perdana, pilkada, kendal, paslon",
                "source": "https://regional.kompas.com/read/2024/11/05/073014478/debat-perdana-pilkada-kendal-3-paslon-puas",
                "date": "5 November 2024",
                "tweet": "juta ton beras buat siap pilkada guyur bansos",
                "trending_topics": "pilkada, serentak, suara, pilih"
            },
            {
                "title": "jagoan, pdip, pilgub, jakarta, jateng, unggul, survei litbang, kompas",
                "source": "https://www.tempo.co/politik/-jagoan-pdip-di-pilgub-jakarta-dan-jateng-unggul-versi-survei-litbang-kompas-1164116",
                "date": "5 November 2024",
                "tweet": "tahu level pintar minta jokowi jadi jurkam pilkada",
                "trending_topics": "pilkada, presiden, jokowi, jakarta, mantan, dki, prabowo, warga"
            },
            {
                "title": "jaga, ruang, aman, digital, pilkada, menkomdigi, paparkan, program, kampanye, damai",
                "source": "https://nasional.kompas.com/read/2024/11/07/21330741/jaga-ruang-aman-digital-di-pilkada-menkomdigi-paparkan-5-program-kampanye",
                "date": "5 November 2024",
                "tweet": "debat calon gubernur serasa debat capres seru pakai banget semua pilkada calon gubernur jatim kayak punya pilih calon gubernur paling unggul kompeten rakyat jatim bebas milih baik maju jawa timur",
                "trending_topics": "pilkada, calon, gubernur, bupati, wakil, daerah, pilih, debat"
            },
            {
                "title": "bawaslu, jakarta, lakukan, patroli, pengawasan, kampanye, antisipasi, pelanggaran",
                "source": "https://megapolitan.kompas.com/read/2024/11/06/21331371/bawaslu-jakarta-lakukan-patroli-pengawasan-selama-masa-kampanye-untuk",
                "date": "6 November 2024",
                "tweet": "banget pilkada kim partai buruh aneh",
                "trending_topics": "pilkada, jokowi, partai, bansos, dukung"
            },
            {
                "title": "pks, klaim, prabowo, jokowi, dukung, ridwan kamil- suswono, pilkada, jakarta",
                "source": "https://www.tempo.co/politik/giliran-pks-klaim-prabowo-dan-jokowi-dukung-ridwan-kamil-suswono-di-pilkada-jakarta--1164159",
                "date": "5 November 2024",
                "tweet": "hari tuju pilkada serentak november",
                "trending_topics": "pilkada, aman, masyarakat, jelang, tertib, serentak, damai, ajak"
            },
            {
                "title": "calon, kepala, daerah, sowan, rumah, jokowi, jelang, pilkada",
                "source": "https://www.tempo.co/politik/ini-daftar-calon-kepala-daerah-yang-sowan-ke-rumah-jokowi-jelang-pilkada-2024-1165095",
                "date": "7 November 2024",
                "tweet": "lawan hoaks ujar benci pilkada aman kualitas",
                "trending_topics": "pilkada, dukung, pasang, garut, menang, pks, coblos"
            },
            {
                "title": "program, warga, kebon pala, ridwan kamil, menang",
                "source": "https://www.tempo.co/politik/sampaikan-program-ke-warga-kebon-pala-ridwan-kamil-tapi-menang-dulu-ya-1163163",
                "date": "3 November 2024",
                "tweet": "pilkada pilih warga lokal bang",
                "trending_topics": "pilkada, rakyat, pilpres, menang, uang"
            },
            {
                "title": "elektabilitas, cagub-cawagub, jateng, ketat, golkar, partai, pengusung, luthfi-yasin, solid",
                "source": "https://regional.kompas.com/read/2024/11/05/190257078/elektabilitas-cagub-cawagub-jateng-ketat-golkar-ajak-partai-pengusung",
                "date": "5 November 2024",
                "tweet": "pilkada jakarta siapa paling peluang ikut kompas",
                "trending_topics": "pilkada, jakarta, debat, kompas, pilih, kaltim, calon, hasil, jateng, survei, kembang"
            },
            {
                "title": "pertemuan, ridwan kamil, prabowo, jokowi, dukungan, pilkada, jakarta",
                "source": "https://megapolitan.kompas.com/read/2024/11/03/08570371/pertemuan-ridwan-kamil-dengan-prabowo-dan-jokowi-dukungan-buat-pilkada",
                "date": "3 November 2024",
                "tweet": "lho ahok terus komut menang pilkada pdip",
                "trending_topics": "pilkada. Pdip, menang, judol, aktif, pilpres, tim, timses"
            },
            {
                "title": "debat, pilkada, sumut, edy rahmayadi, jalan, desa, urusan, gubernur",
                "source": "https://medan.kompas.com/read/2024/11/06/212757878/debat-kedua-pilkada-sumut-edy-rahmayadi-jalan-desa-bukan-urusan-gubernur",
                "date": "6 November 2024",
                "tweet": "pilkada jalan sesuai harap semua lancar",
                "trending_topics": "pilkada, bawaslu, awas, jaga, adil, demokrasi, jalan, jujur, ketat, curang"
            },
            
        ],
        "metrics": {
            "topic_recall": {
                "value": 0.53,
                "fraction": "5.3/10"
            },
            "keyword_precision": {
                "value": 0.543859649,
                "fraction": "31/57"
            },
            "keyword_recall": {
                "value": 0.508196721,
                "fraction": "29/61"
            }
        }
    }
}