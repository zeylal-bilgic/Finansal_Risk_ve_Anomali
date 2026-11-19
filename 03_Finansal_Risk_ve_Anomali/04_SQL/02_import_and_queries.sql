USE financial_risk;

-- Workbench Table Data Import Wizard ile 02_Veri/transfers.csv dosyasını seçip
-- hedef tablo olarak transfer_transactions seçin. Sütun sırasını kontrol edin.
-- MySQL'in yerel yükleme izinleri kapalıysa Workbench sihirbazını kullanın.

-- 1) Aktarımın kontrolü: 10.085 satır beklenir.
SELECT COUNT(*) AS transaction_count,
       COUNT(DISTINCT transaction_id) AS unique_transaction_ids
FROM transfer_transactions;

-- 2) Kanal ve yön bazında tutar ve işlem sayısı
SELECT channel, direction, COUNT(*) AS transaction_count,
       ROUND(SUM(amount_try), 2) AS total_try,
       ROUND(AVG(amount_try), 2) AS average_try
FROM transfer_transactions
GROUP BY channel, direction
ORDER BY channel, direction;

-- 3) Günlük brüt giriş, brüt çıkış ve net çıkış
SELECT DATE(transaction_time) AS transaction_date,
       ROUND(SUM(CASE WHEN direction='incoming' THEN amount_try ELSE 0 END),2) AS incoming_try,
       ROUND(SUM(CASE WHEN direction='outgoing' THEN amount_try ELSE 0 END),2) AS outgoing_try,
       ROUND(SUM(CASE WHEN direction='outgoing' THEN amount_try ELSE -amount_try END),2) AS net_outflow_try
FROM transfer_transactions
GROUP BY DATE(transaction_time)
ORDER BY transaction_date;

-- 4) Yüksek tutar adayları. Bu sorgu yalnızca örnek bir eşik kullanır;
-- resmi analizde Python, kanal başına IQR üst sınırlarını kullanır.
SELECT transaction_id, transaction_time, account_id, beneficiary_id, channel, amount_try
FROM transfer_transactions
WHERE direction='outgoing' AND amount_try >= 2000
ORDER BY amount_try DESC;

-- 5) Aynı hesap/yararlanıcı/kanalda 10 dakika içindeki ardışık işlemler
WITH sequenced AS (
    SELECT transaction_id, transaction_time, account_id, beneficiary_id, channel, amount_try,
           LAG(transaction_time) OVER (
             PARTITION BY account_id, beneficiary_id, channel ORDER BY transaction_time
           ) AS previous_time
    FROM transfer_transactions
    WHERE direction='outgoing'
)
SELECT transaction_id, transaction_time, account_id, beneficiary_id, channel, amount_try,
       TIMESTAMPDIFF(SECOND, previous_time, transaction_time) AS seconds_since_previous
FROM sequenced
WHERE previous_time IS NOT NULL
  AND TIMESTAMPDIFF(SECOND, previous_time, transaction_time) BETWEEN 0 AND 600
ORDER BY transaction_time;
