import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '5s', target: 50 },
        { duration: '20s', target: 50 },
        { duration: '5s', target: 0 },
    ],
    thresholds: {
        http_req_failed: ['rate<0.01'], 
        http_req_duration: ['p(99)<20'],
    },
};

export default function () {
    const url = 'http://host.docker.internal:9999/fraud-score';
    
    const payload = JSON.stringify({
        id: "tx-3576980410",
        transaction: { amount: 384.88, installments: 3, requested_at: "2026-03-11T20:23:35Z" },
        customer: { avg_amount: 769.76, tx_count_24h: 3, known_merchants: ["MERC-009", "MERC-001"] },
        merchant: { id: "MERC-001", mcc: "5912", avg_amount: 298.95 },
        terminal: { is_online: false, card_present: true, km_from_home: 13.7 },
        last_transaction: { timestamp: "2026-03-11T14:58:35Z", km_from_current: 18.8 }
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const res = http.post(url, payload, params);

    check(res, {
        'status é 200': (r) => r.status === 200,
    });

    sleep(0.01); 
}