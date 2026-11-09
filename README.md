# Customer Retention & RFM-Based Segmentation Analysis

End-to-end analysis of e-commerce customer retention and RFM segmentation using **Python** and **Power BI**, built on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

## Highlights
- Analysed **99.4K+ transactions** from **96.1K+ customers** to study purchasing patterns, cohort behaviour and retention.
- Found extremely low retention: **~0.48% Month-1 retention** and a **~96.88% single-purchase customer rate**.
- Built an **RFM segmentation into 7 groups**: ~38.5% Potential Loyalists, ~38.3% Lost Customers, plus revenue contribution per segment.
- Delivered an interactive **Power BI dashboard** for retention, segment distribution and revenue.

> Replace the numbers above with the exact output of `python src/rfm_analysis.py` on the real data.

## Project structure
```
├── data/raw/            # put the Olist CSVs here (not committed)
├── data/processed/      # generated CSVs used by Power BI
├── src/rfm_analysis.py  # full pipeline: clean -> cohorts -> RFM -> export -> charts
├── src/make_sample_data.py  # synthetic data to smoke-test only
├── outputs/charts/      # generated PNGs
├── powerbi/             # dashboard (.pbix) + build guide
└── requirements.txt
```

## How to run
1. Download the dataset from Kaggle and place these 3 files in `data/raw/`:
   `olist_orders_dataset.csv`, `olist_customers_dataset.csv`, `olist_order_payments_dataset.csv`
2. Install and run:
```bash
pip install -r requirements.txt
python src/rfm_analysis.py --data-dir data/raw
```
3. Open Power BI and follow `powerbi/POWERBI_GUIDE.md`.

## Methodology
**Cleaning:** orders joined to `customer_unique_id` (the real person; `customer_id` is per-order) and to total payment value per order.

**Retention:** customers are grouped into monthly cohorts by first purchase month. Month-1 retention = share of a cohort that buys again in the following month (cohorts under 100 customers and cohorts without an observable month 1 are excluded).

**RFM:** snapshot date = last order date + 1 day.
- Recency & Monetary: quintile scores 1-5 (5 = best).
- Frequency: fixed bands (1 order, 2 orders, 3+) because ~97% of customers buy once, which makes quintiles meaningless.

| Segment | Rule |
|---|---|
| Champions | repeat buyer, R ≥ 4 |
| Loyal Customers | repeat buyer, R = 3 |
| At Risk | repeat buyer, R ≤ 2 |
| Potential Loyalists | single purchase, R ≥ 4 |
| Need Attention | single purchase, R = 3, M ≥ 4 |
| About to Sleep | single purchase, R = 3, M ≤ 3 |
| Lost Customers | single purchase, R ≤ 2 |

## Key insights (fill after running on real data)
- Retention problem: nearly all customers never return -> the growth lever is a second purchase.
- Potential Loyalists (recent one-time buyers) are the biggest win-back/nurture opportunity.
- Lost Customers are a large share of the base; test low-cost reactivation vs. accept churn.

## Tech
Python (pandas, NumPy, Matplotlib) · Power BI (DAX)
