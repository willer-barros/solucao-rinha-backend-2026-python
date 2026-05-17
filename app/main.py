from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
import numpy as np
from fastapi import Body
import os
import orjson
from usearch.index import Index
app = FastAPI(default_response_class=ORJSONResponse)

INDEX = Index(ndim=14, metric='l2sq', dtype='f32')
LABELS = None
NORM = None
MCC_RISK = None

def get_day_of_week(y,m,d):
    t = [0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4]
    if m < 3:
        y -=1
    return (y + y // 4 - y // 100 + y // 400 + t[m - 1] + d) % 7


@app.on_event("startup")
async def startup_event():
    global LABELS
    print("Carregando index do USearch...")
    INDEX.view("data/rinha_usearch.index")
    
    print("Mapeando labels binárias...")
    LABELS = np.memmap("data/labels.bin", dtype=np.uint8, mode='r')
    print(f"Sucesso! Mapeados {len(LABELS)} registros.")

@app.get("/ready", status_code=200)
async def ready():
    return {"status": "ready"}

@app.post("/fraud-score")
async def fraud_score(payload: dict = Body(...)):
    try:
        tx = payload["transaction"]
        cust = payload["customer"]
        merch = payload["merchant"]
        term = payload["terminal"]
        last = payload["last_transaction"]

        amt = tx['amount']

        d0 = amt / NORM["max_amount"]
        if d0 > 1.0: d0 = 1.0
        elif d0 < 0.0: d0 = 0.0
            
        d1 = tx["installments"] / NORM["max_installments"]
        if d1 > 1.0: d1 = 1.0
        elif d1 < 0.0: d1 = 0.0
        
        avg_amt = cust["avg_amount"]
        if avg_amt > 0:
            d2 = (amt / avg_amt) / NORM["amount_vs_avg_ratio"]
            if d2 > 1.0: d2 = 1.0
            elif d2 < 0.0: d2 = 0.0
        else:
            d2 = 0.0
            
        req_at = tx["requested_at"]
        hour = int(req_at[11:13])
        d3 = hour / 23.0
        
        year = int(req_at[0:4])
        month = int(req_at[5:7])
        day = int(req_at[8:10])
        sakamoto = get_day_of_week(year, month, day)
        weekday = 6 if sakamoto == 0 else sakamoto - 1 
        d4 = weekday / 6.0

        if last is None:
            d5 = -1.0
            d6 = -1.0
        else:
            t_curr_min = (hour * 60) + int(req_at[14:16])
            
            l_ts = last["timestamp"]
            l_hour = int(l_ts[11:13])
            t_last_min = (l_hour * 60) + int(l_ts[14:16])
            
            diff_minutes = t_curr_min - t_last_min
            if diff_minutes < 0:
                diff_minutes += 1440
                
            d5 = diff_minutes / NORM["max_minutes"]
            if d5 > 1.0: d5 = 1.0
            elif d5 < 0.0: d5 = 0.0
                
            d6 = last["km_from_current"] / NORM["max_km"]
            if d6 > 1.0: d6 = 1.0
            elif d6 < 0.0: d6 = 0.0

        d7 = term["km_from_home"] / NORM["max_km"]
        if d7 > 1.0: d7 = 1.0
        elif d7 < 0.0: d7 = 0.0
            
        d8 = cust["tx_count_24h"] / NORM["max_tx_count_24h"]
        if d8 > 1.0: d8 = 1.0
        elif d8 < 0.0: d8 = 0.0
            
        d9 = 1.0 if term["is_online"] else 0.0
        d10 = 1.0 if term["card_present"] else 0.0
        
        d11 = 0.0 if merch["id"] in cust["known_merchants"] else 1.0
        
        d12 = float(MCC_RISK.get(merch["mcc"], 0.5))
        
        d13 = merch["avg_amount"] / NORM["max_merchant_avg_amount"]
        if d13 > 1.0: d13 = 1.0
        elif d13 < 0.0: d13 = 0.0

        input_vector = [d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13]

        #Busca no USearch e inferencia do NumPy
        matches = INDEX.search(input_vector, 5)
        fraud_count = int(np.sum(LABELS[matches.keys]))
        score = fraud_count / 5.0
        approved = score < 0.6

        return {
            "approved": approved,
            "fraud_score": score
        }

    except Exception:
        return {
            "approved": True,
            "fraud_score": 0.0
        }