# Akıllı Finansal Risk ve Anomali İzleme Sistemi

Bu çalışma, banka transferi benzeri **tamamen sentetik** kayıtlar üzerinde şeffaf kontroller uygular. Amaç gerçek bir bankanın işlemlerine bağlanmak, suç tespiti yapmak ya da işlemleri otomatik durdurmak değildir. Çıktılar yalnızca insan incelemesine aday kayıtlar ve nakit akışı senaryolarıdır.

## Hızlı çalıştırma

1. Bu klasörü VS Code'da açın.
2. İsterseniz `run_analysis.bat` dosyasına çift tıklayın. Bu dosya veri üretimini ve analizi sırayla çalıştırır.
3. Alternatif olarak VS Code içindeki Terminal > New Terminal menüsünü seçip aşağıdaki iki komutu sırayla çalıştırın:

```powershell
python 03_Python/generate_data.py
python 03_Python/analyze_transfers.py
```

Python 3 yeterlidir; analiz betikleri ek kütüphane gerektirmez. Her çalıştırmada aynı seed kullanılır, dolayısıyla veri ve sonuçlar tekrar üretilebilir.

## Akış

`generate_data.py` 120 günlük döneme yayılmış 10.085 sentetik işlem üretir. `analyze_transfers.py` üç açıklanabilir kontrol uygular: transfer kanalına göre IQR üst sınırını aşan giden işlemler, bu işlemlerden saat 00:00–04:59 arasında gerçekleşenler ve aynı hesap/yararlanıcı/kanalda 10 dakika içinde ardışık tekrarlar. Daha sonra geçmiş sentetik günlük akışları yerine koyarak 10.000 adet 30 günlük Monte Carlo senaryosu üretir.

Sonuçlar `08_Raporlar/` altına yazılır. Excel özeti `05_Excel/`, ayrıntılı öğrenme rehberi `01_Rehber/`, slaytlar `06_Sunum/`, MySQL dosyaları `04_SQL/` klasöründedir.

## Ana sonuçlar

- Sentetik işlem sayısı: 10.085
- En az bir kontrole takılan benzersiz işlem: 275
- Tüm kontrol tetiklenmelerinin toplamı: 331. Tetiklenmeler kesişebilir; bu bir fraud adedi değildir.
- 30 günlük net nakit çıkışı senaryosunun medyanı: 2.244.225,69 TL
- Senaryo P95 değeri: 2.994.440,23 TL

Monte Carlo örneklemesi geçmiş sentetik günlük akışların aynı dağılımla sürdüğünü varsayar. Gerçek gelecek tahmini veya garanti sunmaz. `scenario_truth.csv` yalnızca geliştirme sırasında eklenen örnek senaryoları listeler; tespit kuralı bu etiketleri kullanmaz.

## Dosya rehberi

- `02_Veri/transfers.csv`: analize giren sentetik işlemler
- `02_Veri/scenario_truth.csv`: eğitim amaçlı enjekte edilmiş senaryo etiketleri
- `03_Python/`: veri üretimi ve analiz
- `04_SQL/`: MySQL tablo tanımı, içe aktarma ve örnek sorgular
- `08_Raporlar/`: aday işlemler, günlük akış, kontrol özeti ve JSON sonuç
- `05_Excel/`: özet görünümü ve ayrıntı sekmeleri
- `01_Rehber/`: kavramlar, yöntemler, adım adım çalışma ve mülakat/video notları
- `06_Sunum/`: proje anlatım sunumu
- `07_Kaynakca/`: kullanılan yöntem ve MySQL belgeleri

## Bilinen sınırlar

Veri kurgusaldır, kurallar basitleştirilmiştir ve normal bir işlem de işaretlenebilir. Tutarın yüksek olması tek başına şüpheli işlem anlamına gelmez. Proje hiçbir gerçek sisteme bağlanmaz; herhangi bir banka, müşteri veya kişiyi değerlendirmez.
