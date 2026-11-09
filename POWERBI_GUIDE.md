# Power BI Dashboard Build Guide

## 1. Load data (Get Data -> Text/CSV) from `data/processed/`
`rfm_customers.csv`, `segment_summary.csv`, `cohort_retention.csv`, `orders_enriched.csv`, `kpis.csv`

## 2. Model
Relationship: `orders_enriched[customer_unique_id]` -> `rfm_customers[customer_unique_id]` (many-to-one).
Set `orders_enriched[order_purchase_timestamp]` as Date/Time. Sort `segment` by a custom order (Champions, Loyal Customers, At Risk, Potential Loyalists, Need Attention, About to Sleep, Lost Customers).

## 3. DAX measures
```DAX
Total Customers = DISTINCTCOUNT(rfm_customers[customer_unique_id])
Total Orders = DISTINCTCOUNT(orders_enriched[order_id])
Total Revenue = SUM(orders_enriched[payment_value])
Avg Order Value = DIVIDE([Total Revenue], [Total Orders])

Repeat Customers = CALCULATE([Total Customers], rfm_customers[frequency] > 1)
Single Purchase Rate % = 1 - DIVIDE([Repeat Customers], [Total Customers])

Customer % of Total =
DIVIDE([Total Customers], CALCULATE([Total Customers], ALL(rfm_customers[segment])))

Revenue % of Total =
DIVIDE([Total Revenue], CALCULATE([Total Revenue], ALL(rfm_customers[segment])))
```

## 4. Pages
**Page 1 - Overview:** KPI cards (Total Customers, Total Orders, Total Revenue, Single Purchase Rate %, Month-1 Retention from `kpis`), line chart of orders/revenue by month.

**Page 2 - Retention:** Matrix with `cohort_month` (rows), `month_index` (columns), `retention_pct` (values, average) + conditional-format background colour; line chart of average retention by month_index.

**Page 3 - RFM Segments:** Donut/bar of Customer % by segment, bar of Revenue % by segment, table from `segment_summary` (avg recency, frequency, monetary), scatter of recency vs monetary coloured by segment.

**Slicers:** segment, customer_state, order month.

## 5. Save
Save as `powerbi/Customer_Retention_RFM.pbix`, add screenshots to `outputs/charts/` and reference them in the README.
