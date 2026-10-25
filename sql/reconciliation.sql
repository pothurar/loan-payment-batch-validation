-- Daily reconciliation report for one payment_date.
-- Replace the date, or bind it as a parameter in your client.
-- Returns one row per batch: total / processed / flagged.

SELECT
    b.batch_id,
    b.payment_date,
    COUNT(p.id) AS total,
    COUNT(p.id) FILTER (WHERE p.status = 'processed') AS processed,
    COUNT(p.id) FILTER (WHERE p.status = 'flagged') AS flagged
FROM payment_batches b
LEFT JOIN payments p ON p.batch_id = b.batch_id
WHERE b.payment_date = '2026-01-15'
GROUP BY b.batch_id, b.payment_date
ORDER BY b.batch_id;
