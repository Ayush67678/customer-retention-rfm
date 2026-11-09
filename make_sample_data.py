"""Generates a small synthetic dataset with the Olist schema, ONLY for smoke-testing the pipeline.
Do not use its numbers in the README/resume."""
import argparse, uuid
from pathlib import Path
import numpy as np, pandas as pd

ap = argparse.ArgumentParser(); ap.add_argument("--out", default="data/sample"); ap.add_argument("--n", type=int, default=20000)
a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(42)
start, end = pd.Timestamp("2017-01-01"), pd.Timestamp("2018-08-31")
span = (end - start).days
rows, cust = [], []
for _ in range(a.n):
    uid = uuid.uuid4().hex
    k = 1 + (rng.random() < 0.03) + (rng.random() < 0.004)
    t0 = start + pd.Timedelta(days=int(rng.integers(0, span)))
    for j in range(int(k)):
        t = min(t0 + pd.Timedelta(days=int(rng.integers(20, 150)) * j), end)
        cid, oid = uuid.uuid4().hex, uuid.uuid4().hex
        rows.append((oid, cid, "delivered", t + pd.Timedelta(minutes=int(rng.integers(0, 1440))), round(float(rng.lognormal(4.8, 0.7)), 2)))
        cust.append((cid, uid, rng.choice(["SP", "RJ", "MG", "RS", "PR"])))
o = pd.DataFrame(rows, columns=["order_id", "customer_id", "order_status", "order_purchase_timestamp", "payment_value"])
o.drop(columns="payment_value").to_csv(out / "olist_orders_dataset.csv", index=False)
pd.DataFrame(cust, columns=["customer_id", "customer_unique_id", "customer_state"]).to_csv(out / "olist_customers_dataset.csv", index=False)
o[["order_id", "payment_value"]].to_csv(out / "olist_order_payments_dataset.csv", index=False)
print("sample data ->", out)
