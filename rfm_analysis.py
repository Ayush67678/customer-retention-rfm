"""
Customer Retention & RFM-Based Segmentation Analysis
Dataset: Olist Brazilian E-Commerce (Kaggle)

Usage:
    python src/rfm_analysis.py --data-dir data/raw
Outputs go to data/processed (CSV for Power BI) and outputs/charts (PNG).
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "At Risk",
    "Potential Loyalists", "Need Attention", "About to Sleep", "Lost Customers",
]


# ---------------------------------------------------------------- load / clean
def load_data(data_dir: Path) -> pd.DataFrame:
    orders = pd.read_csv(
        data_dir / "olist_orders_dataset.csv",
        usecols=["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
        parse_dates=["order_purchase_timestamp"],
    )
    customers = pd.read_csv(
        data_dir / "olist_customers_dataset.csv",
        usecols=["customer_id", "customer_unique_id", "customer_state"],
    )
    pay = (
        pd.read_csv(data_dir / "olist_order_payments_dataset.csv")
        .groupby("order_id", as_index=False)["payment_value"].sum()
    )
    df = (
        orders.merge(customers, on="customer_id", how="left")
        .merge(pay, on="order_id", how="left")
    )
    df["payment_value"] = df["payment_value"].fillna(0.0)
    df = df.dropna(subset=["customer_unique_id", "order_purchase_timestamp"])
    df["order_month"] = df["order_purchase_timestamp"].dt.to_period("M")
    return df


# ------------------------------------------------------------------ retention
def cohort_retention(df: pd.DataFrame, min_cohort_size: int = 100):
    """Monthly cohorts by first purchase month. Returns (long table, wide table, summary dict)."""
    first = df.groupby("customer_unique_id")["order_month"].min().rename("cohort_month")
    d = df.join(first, on="customer_unique_id")
    d["month_index"] = (
        (d["order_month"].dt.year - d["cohort_month"].dt.year) * 12
        + (d["order_month"].dt.month - d["cohort_month"].dt.month)
    )
    counts = (
        d.groupby(["cohort_month", "month_index"])["customer_unique_id"]
        .nunique().unstack(fill_value=0)
    )
    sizes = counts[0]
    counts = counts[sizes >= min_cohort_size]          # drop tiny early cohorts
    sizes = sizes.loc[counts.index]
    retention = counts.div(sizes, axis=0) * 100

    # a cohort is only "observable" at month N if that month exists in the data
    last_month = df["order_month"].max()
    m1_cohorts = [
        c for c in counts.index
        if (last_month.year - c.year) * 12 + (last_month.month - c.month) >= 1
    ]
    month1 = (
        counts.loc[m1_cohorts, 1].sum() / sizes.loc[m1_cohorts].sum() * 100
        if m1_cohorts and 1 in counts.columns else float("nan")
    )

    long = (
        retention.reset_index()
        .melt(id_vars="cohort_month", var_name="month_index", value_name="retention_pct")
    )
    long["cohort_size"] = long["cohort_month"].map(sizes)
    long["cohort_month"] = long["cohort_month"].astype(str)
    return long, retention, {"month1_retention_pct": month1}


# ------------------------------------------------------------------------ RFM
def build_rfm(df: pd.DataFrame) -> pd.DataFrame:
    snapshot = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("customer_unique_id").agg(
        recency=("order_purchase_timestamp", lambda s: (snapshot - s.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("payment_value", "sum"),
    ).reset_index()

    # Recency & Monetary: quintiles (rank first to break ties).
    # Highest score = most recent / highest spend.
    rfm["R"] = pd.qcut(rfm["recency"].rank(method="first", ascending=False), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["M"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    # Frequency: ~97% buy once, so quintiles are meaningless -> fixed bands.
    rfm["F"] = np.select([rfm["frequency"] >= 3, rfm["frequency"] == 2], [3, 2], default=1)
    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    return rfm


def assign_segment(r) -> str:
    R, F, M = r["R"], r["F"], r["M"]
    if F >= 2:                                   # repeat buyers
        if R >= 4:
            return "Champions"
        if R == 3:
            return "Loyal Customers"
        return "At Risk"
    # single-purchase customers
    if R >= 4:
        return "Potential Loyalists"
    if R == 3:
        return "Need Attention" if M >= 4 else "About to Sleep"
    return "Lost Customers"


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    s = rfm.groupby("segment").agg(
        customers=("customer_unique_id", "count"),
        revenue=("monetary", "sum"),
        avg_recency_days=("recency", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_monetary=("monetary", "mean"),
    )
    s["customer_pct"] = s["customers"] / s["customers"].sum() * 100
    s["revenue_pct"] = s["revenue"] / s["revenue"].sum() * 100
    return s.reindex([x for x in SEGMENT_ORDER if x in s.index]).round(2).reset_index()


# --------------------------------------------------------------------- charts
def make_charts(retention, summary, out: Path):
    out.mkdir(parents=True, exist_ok=True)

    r = retention.iloc[:, 1:13]  # months 1-12, skip month 0 (always 100%)
    fig, ax = plt.subplots(figsize=(11, 6))
    im = ax.imshow(r.values, cmap="YlGnBu", aspect="auto", vmin=0, vmax=max(1.0, np.nanmax(r.values)))
    ax.set_xticks(range(r.shape[1])); ax.set_xticklabels(r.columns)
    ax.set_yticks(range(len(r))); ax.set_yticklabels([str(i) for i in r.index], fontsize=8)
    ax.set_xlabel("Months since first purchase"); ax.set_ylabel("Cohort")
    ax.set_title("Cohort Retention (%)"); fig.colorbar(im, label="% of cohort")
    fig.tight_layout(); fig.savefig(out / "cohort_retention_heatmap.png", dpi=150); plt.close(fig)

    for col, title, color, fname in [
        ("customer_pct", "Customer Distribution by RFM Segment", "#2a6f97", "segment_distribution.png"),
        ("revenue_pct", "Revenue Contribution by RFM Segment", "#e07a5f", "segment_revenue.png"),
    ]:
        fig, ax = plt.subplots(figsize=(9, 5))
        vals = summary[col][::-1].tolist()
        ax.barh(summary["segment"][::-1], vals, color=color)
        for i, v in enumerate(vals):
            ax.text(v + 0.3, i, f"{v:.1f}%", va="center")
        ax.set_xlabel("% share"); ax.set_title(title)
        fig.tight_layout(); fig.savefig(out / fname, dpi=150); plt.close(fig)


# ----------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/raw")
    ap.add_argument("--processed-dir", default="data/processed")
    ap.add_argument("--charts-dir", default="outputs/charts")
    a = ap.parse_args()

    df = load_data(Path(a.data_dir))
    proc = Path(a.processed_dir); proc.mkdir(parents=True, exist_ok=True)

    n_orders = df["order_id"].nunique()
    n_cust = df["customer_unique_id"].nunique()
    orders_per_cust = df.groupby("customer_unique_id")["order_id"].nunique()
    single_rate = (orders_per_cust == 1).mean() * 100

    long, retention, stats = cohort_retention(df)
    rfm = build_rfm(df)
    summary = segment_summary(rfm)

    print(f"Transactions (orders): {n_orders:,}")
    print(f"Unique customers:      {n_cust:,}")
    print(f"Single-purchase rate:  {single_rate:.2f}%")
    print(f"Month-1 retention:     {stats['month1_retention_pct']:.2f}%")
    print("\nSegment summary:\n", summary.to_string(index=False))

    # Power BI inputs
    rfm.to_csv(proc / "rfm_customers.csv", index=False)
    summary.to_csv(proc / "segment_summary.csv", index=False)
    long.to_csv(proc / "cohort_retention.csv", index=False)
    df.assign(order_month=df["order_month"].astype(str)).merge(
        rfm[["customer_unique_id", "segment"]], on="customer_unique_id"
    ).to_csv(proc / "orders_enriched.csv", index=False)
    pd.DataFrame([{
        "orders": n_orders, "customers": n_cust,
        "single_purchase_rate_pct": round(single_rate, 2),
        "month1_retention_pct": round(stats["month1_retention_pct"], 2),
    }]).to_csv(proc / "kpis.csv", index=False)

    make_charts(retention, summary, Path(a.charts_dir))
    print(f"\nSaved CSVs -> {proc}  |  charts -> {a.charts_dir}")


if __name__ == "__main__":
    main()
