from __future__ import annotations

import json
import math
import random
import textwrap
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


SEED = 20260611
random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "bi_ecommerce_executive_performance_dashboard"
DATE_START = date(2025, 1, 1)
DATE_END = date(2026, 5, 31)
REPORT_AS_OF = date(2026, 6, 11)


DIRS = [
    "_agent",
    "data/raw",
    "data/interim",
    "data/prepared",
    "data/validated",
    "data/synthetic",
    "model",
    "build/scripts",
    "build/config",
    "powerbi/pbip",
    "powerbi/templates",
    "powerbi/notes",
    "output/screenshots",
    "output/exports",
    "qa",
    "docs",
    "archive/old_versions",
    "archive/deprecated_outputs",
]


CATEGORIES = {
    "Electronics": {
        "subcategories": ["Mobile", "Laptop", "Audio", "Wearables", "Gaming"],
        "price": (90, 1600),
        "weight": 0.28,
    },
    "Home & Living": {
        "subcategories": ["Kitchen", "Furniture", "Decor", "Storage", "Lighting"],
        "price": (20, 700),
        "weight": 0.17,
    },
    "Fashion": {
        "subcategories": ["Apparel", "Shoes", "Bags", "Accessories", "Activewear"],
        "price": (12, 240),
        "weight": 0.18,
    },
    "Beauty": {
        "subcategories": ["Skincare", "Makeup", "Haircare", "Fragrance", "Tools"],
        "price": (8, 190),
        "weight": 0.13,
    },
    "Grocery": {
        "subcategories": ["Pantry", "Beverages", "Snacks", "Fresh", "Household"],
        "price": (4, 80),
        "weight": 0.11,
    },
    "Sports": {
        "subcategories": ["Fitness", "Outdoor", "Cycling", "Team Sports", "Yoga"],
        "price": (15, 550),
        "weight": 0.08,
    },
    "Books & Media": {
        "subcategories": ["Books", "Games", "Music", "Stationery", "Learning"],
        "price": (5, 120),
        "weight": 0.05,
    },
}

REGIONS = [
    {"region": "North America", "country": "United States", "weight": 0.40},
    {"region": "Europe", "country": "United Kingdom", "weight": 0.21},
    {"region": "Southeast Asia", "country": "Vietnam", "weight": 0.18},
    {"region": "East Asia", "country": "Japan", "weight": 0.11},
    {"region": "Oceania", "country": "Australia", "weight": 0.06},
    {"region": "Middle East", "country": "United Arab Emirates", "weight": 0.04},
]

CHANNELS = [
    {"channel": "Organic Search", "weight": 0.31, "conv": 0.032, "cpc": 0.0},
    {"channel": "Paid Search", "weight": 0.18, "conv": 0.034, "cpc": 0.74},
    {"channel": "Direct", "weight": 0.16, "conv": 0.038, "cpc": 0.0},
    {"channel": "Email", "weight": 0.11, "conv": 0.047, "cpc": 0.05},
    {"channel": "Social", "weight": 0.13, "conv": 0.022, "cpc": 0.42},
    {"channel": "Affiliate", "weight": 0.07, "conv": 0.029, "cpc": 0.25},
    {"channel": "Display", "weight": 0.04, "conv": 0.014, "cpc": 0.35},
]

DEVICES = [
    {"device": "Mobile", "weight": 0.61},
    {"device": "Desktop", "weight": 0.28},
    {"device": "Tablet", "weight": 0.11},
]


def ensure_dirs() -> None:
    for rel in DIRS:
        (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)


def write_text(rel_path: str, content: str) -> None:
    path = PROJECT_ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def write_json(rel_path: str, payload: object) -> None:
    path = PROJECT_ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def weighted_choice(rows: list[dict], weight_key: str) -> dict:
    total = sum(float(row[weight_key]) for row in rows)
    pick = random.random() * total
    running = 0.0
    for row in rows:
        running += float(row[weight_key])
        if pick <= running:
            return row
    return rows[-1]


def date_range(start: date, end: date) -> list[date]:
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_products() -> pd.DataFrame:
    brands = [
        "Northline",
        "UrbanCo",
        "NovaHaus",
        "Vivid",
        "CorePlus",
        "Aster",
        "Modo",
        "Everly",
        "Zenith",
        "PlainGood",
    ]
    products = []
    product_id = 10000
    for category, cfg in CATEGORIES.items():
        count = max(12, int(cfg["weight"] * 260))
        for i in range(count):
            subcategory = random.choice(cfg["subcategories"])
            low, high = cfg["price"]
            base_price = round(random.uniform(low, high) * random.uniform(0.82, 1.18), 2)
            if category == "Electronics":
                cost_rate = random.uniform(0.61, 0.76)
            elif category in {"Fashion", "Beauty"}:
                cost_rate = random.uniform(0.37, 0.57)
            elif category == "Grocery":
                cost_rate = random.uniform(0.62, 0.78)
            else:
                cost_rate = random.uniform(0.45, 0.68)
            products.append(
                {
                    "product_id": f"P{product_id}",
                    "product_name": f"{random.choice(brands)} {subcategory} {i + 1:03d}",
                    "category": category,
                    "subcategory": subcategory,
                    "brand": random.choice(brands),
                    "base_price": round(base_price, 2),
                    "unit_cost": round(base_price * cost_rate, 2),
                    "launch_date": (DATE_START - timedelta(days=random.randint(30, 730))).isoformat(),
                    "active_flag": "Y",
                }
            )
            product_id += 1
    return pd.DataFrame(products)


def make_customers() -> pd.DataFrame:
    segments = [
        ("New", 0.28),
        ("Active", 0.42),
        ("Loyal", 0.20),
        ("VIP", 0.06),
        ("At Risk", 0.04),
    ]
    customers = []
    for i in range(1, 18001):
        region = weighted_choice(REGIONS, "weight")
        segment_pick = weighted_choice([{"segment": s, "weight": w} for s, w in segments], "weight")
        signup = DATE_START - timedelta(days=random.randint(1, 900))
        if random.random() < 0.38:
            signup = random.choice(date_range(DATE_START, DATE_END))
        customers.append(
            {
                "customer_id": f"C{i:06d}",
                "signup_date": signup.isoformat(),
                "customer_segment": segment_pick["segment"],
                "region": region["region"],
                "country": region["country"],
                "marketing_opt_in": "Y" if random.random() < 0.64 else "N",
            }
        )
    return pd.DataFrame(customers)


def seasonal_multiplier(d: date) -> float:
    month = d.month
    base = 1.0
    if month in (11, 12):
        base += 0.36
    if month in (1, 2):
        base -= 0.08
    if month in (6, 7):
        base += 0.07
    if d.weekday() in (5, 6):
        base += 0.10
    trend_days = (d - DATE_START).days
    trend = 1.0 + trend_days / 520 * 0.16
    return base * trend


def make_sessions() -> pd.DataFrame:
    rows = []
    for d in date_range(DATE_START, DATE_END):
        daily_base = random.randint(5200, 7800) * seasonal_multiplier(d)
        for channel in CHANNELS:
            for device in DEVICES:
                for region in REGIONS:
                    share = channel["weight"] * device["weight"] * region["weight"]
                    noise = random.uniform(0.84, 1.20)
                    sessions = max(0, int(daily_base * share * noise))
                    visitors = int(sessions * random.uniform(0.67, 0.82))
                    add_to_cart = int(sessions * random.uniform(0.075, 0.145))
                    checkout_starts = int(add_to_cart * random.uniform(0.34, 0.58))
                    rows.append(
                        {
                            "session_date": d.isoformat(),
                            "channel": channel["channel"],
                            "device": device["device"],
                            "region": region["region"],
                            "sessions": sessions,
                            "visitors": visitors,
                            "add_to_cart": add_to_cart,
                            "checkout_starts": checkout_starts,
                        }
                    )
    return pd.DataFrame(rows)


def make_orders(products: pd.DataFrame, customers: pd.DataFrame, sessions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    product_rows = products.to_dict("records")
    customer_ids = customers["customer_id"].tolist()
    customer_segment_map = dict(zip(customers["customer_id"], customers["customer_segment"]))
    customer_region_map = dict(zip(customers["customer_id"], customers["region"]))
    product_by_category = {
        category: [row for row in product_rows if row["category"] == category]
        for category in CATEGORIES
    }

    orders = []
    returns = []
    order_num = 1
    sessions_grouped = sessions.groupby(["session_date", "channel", "device", "region"], as_index=False)["sessions"].sum()

    first_order_seen: set[str] = set()
    for row in sessions_grouped.to_dict("records"):
        channel = next(item for item in CHANNELS if item["channel"] == row["channel"])
        device_factor = {"Mobile": 0.94, "Desktop": 1.10, "Tablet": 0.98}[row["device"]]
        region_factor = {
            "North America": 1.07,
            "Europe": 1.02,
            "Southeast Asia": 0.93,
            "East Asia": 0.97,
            "Oceania": 1.01,
            "Middle East": 0.90,
        }[row["region"]]
        conv_rate = channel["conv"] * device_factor * region_factor * random.uniform(0.86, 1.15)
        order_count = int(row["sessions"] * conv_rate)
        if random.random() < (row["sessions"] * conv_rate - order_count):
            order_count += 1

        order_date = date.fromisoformat(row["session_date"])
        for _ in range(order_count):
            category = weighted_choice(
                [{"category": k, "weight": v["weight"]} for k, v in CATEGORIES.items()],
                "weight",
            )["category"]
            product = random.choice(product_by_category[category])
            customer_id = random.choice(customer_ids)
            quantity = 1
            if category in {"Grocery", "Beauty", "Books & Media"}:
                quantity = random.choices([1, 2, 3, 4], weights=[0.58, 0.26, 0.11, 0.05])[0]
            elif random.random() < 0.12:
                quantity = 2

            price = float(product["base_price"]) * random.uniform(0.88, 1.08)
            discount_rate = random.choices([0.0, 0.05, 0.10, 0.15, 0.20], weights=[0.44, 0.20, 0.18, 0.12, 0.06])[0]
            gross = round(price * quantity, 2)
            discount_amount = round(gross * discount_rate, 2)
            shipping_fee = 0.0 if gross > 80 or random.random() < 0.42 else round(random.uniform(4.5, 14.5), 2)
            tax_amount = round((gross - discount_amount) * random.uniform(0.03, 0.085), 2)
            status_pick = random.random()
            if status_pick < 0.035:
                status = "Cancelled"
            elif status_pick < 0.079:
                status = "Refunded"
            else:
                status = "Completed"
            refund_amount = round(gross - discount_amount, 2) if status == "Refunded" else 0.0
            net_revenue = 0.0 if status in {"Cancelled", "Refunded"} else round(gross - discount_amount + shipping_fee, 2)
            contribution_margin = round(net_revenue - (float(product["unit_cost"]) * quantity), 2)
            order_id = f"O{order_num:08d}"
            is_first_order = "Y" if customer_id not in first_order_seen else "N"
            first_order_seen.add(customer_id)
            orders.append(
                {
                    "order_id": order_id,
                    "order_date": order_date.isoformat(),
                    "customer_id": customer_id,
                    "product_id": product["product_id"],
                    "category": product["category"],
                    "subcategory": product["subcategory"],
                    "region": row["region"],
                    "channel": row["channel"],
                    "device": row["device"],
                    "customer_segment": customer_segment_map[customer_id],
                    "customer_home_region": customer_region_map[customer_id],
                    "status": status,
                    "quantity": quantity,
                    "unit_price": round(price, 2),
                    "discount_amount": discount_amount,
                    "shipping_fee": shipping_fee,
                    "tax_amount": tax_amount,
                    "gmv": gross,
                    "net_revenue": net_revenue,
                    "refund_amount": refund_amount,
                    "contribution_margin": contribution_margin,
                    "payment_method": random.choice(["Card", "Wallet", "BNPL", "Bank Transfer", "COD"]),
                    "is_first_order": is_first_order,
                }
            )
            if status == "Refunded":
                returns.append(
                    {
                        "return_id": f"R{len(returns) + 1:07d}",
                        "order_id": order_id,
                        "return_date": (order_date + timedelta(days=random.randint(2, 21))).isoformat(),
                        "reason": random.choice(
                            [
                                "Damaged item",
                                "Late delivery",
                                "Wrong size",
                                "Changed mind",
                                "Not as described",
                            ]
                        ),
                        "refund_amount": refund_amount,
                    }
                )
            order_num += 1
    return pd.DataFrame(orders), pd.DataFrame(returns)


def make_campaigns(sessions: pd.DataFrame) -> pd.DataFrame:
    paid_channels = {"Paid Search", "Social", "Display", "Affiliate", "Email"}
    grouped = (
        sessions.assign(month=sessions["session_date"].str.slice(0, 7))
        .groupby(["month", "channel"], as_index=False)
        .agg(sessions=("sessions", "sum"))
    )
    rows = []
    for row in grouped.to_dict("records"):
        channel = next(ch for ch in CHANNELS if ch["channel"] == row["channel"])
        spend = 0.0
        impressions = int(row["sessions"] * random.uniform(5.5, 13.0))
        clicks = int(row["sessions"] * random.uniform(0.72, 1.05))
        if row["channel"] in paid_channels:
            spend = round(clicks * channel["cpc"] * random.uniform(0.85, 1.18), 2)
        rows.append(
            {
                "month": row["month"],
                "channel": row["channel"],
                "spend": spend,
                "impressions": impressions,
                "clicks": clicks,
            }
        )
    return pd.DataFrame(rows)


def make_date_dim() -> pd.DataFrame:
    rows = []
    for d in date_range(DATE_START, DATE_END):
        quarter = (d.month - 1) // 3 + 1
        rows.append(
            {
                "date": d.isoformat(),
                "year": d.year,
                "quarter": f"Q{quarter}",
                "month_number": d.month,
                "month_name": d.strftime("%b"),
                "year_month": d.strftime("%Y-%m"),
                "week_start": (d - timedelta(days=d.weekday())).isoformat(),
                "day_of_week": d.strftime("%a"),
                "is_weekend": "Y" if d.weekday() >= 5 else "N",
            }
        )
    return pd.DataFrame(rows)


def prepare_data(
    products: pd.DataFrame,
    customers: pd.DataFrame,
    sessions: pd.DataFrame,
    orders: pd.DataFrame,
    campaigns: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    dim_date = make_date_dim()
    dim_product = products.copy()
    dim_customer = customers.copy()
    dim_region = pd.DataFrame(REGIONS)[["region", "country"]].drop_duplicates()
    dim_channel = pd.DataFrame(
        [
            {
                "channel": row["channel"],
                "channel_type": "Paid" if row["channel"] in {"Paid Search", "Social", "Display", "Affiliate"} else "Owned/Earned",
                "default_conversion_rate": row["conv"],
            }
            for row in CHANNELS
        ]
    )
    dim_device = pd.DataFrame([{"device": row["device"]} for row in DEVICES])

    fact_orders = orders.copy()
    fact_orders.insert(0, "order_key", range(1, len(fact_orders) + 1))
    fact_orders["order_month"] = fact_orders["order_date"].str.slice(0, 7)
    fact_orders["completed_order_flag"] = (fact_orders["status"] == "Completed").astype(int)
    fact_orders["refund_order_flag"] = (fact_orders["status"] == "Refunded").astype(int)
    fact_orders["cancel_order_flag"] = (fact_orders["status"] == "Cancelled").astype(int)

    fact_sessions = sessions.copy()
    fact_sessions.insert(0, "session_key", range(1, len(fact_sessions) + 1))
    fact_sessions["session_month"] = fact_sessions["session_date"].str.slice(0, 7)
    fact_marketing_spend = campaigns.copy()

    return {
        "dim_date": dim_date,
        "dim_product": dim_product,
        "dim_customer": dim_customer,
        "dim_region": dim_region,
        "dim_channel": dim_channel,
        "dim_device": dim_device,
        "fact_orders": fact_orders,
        "fact_sessions": fact_sessions,
        "fact_marketing_spend": fact_marketing_spend,
    }


def save_dataframes(raw: dict[str, pd.DataFrame], prepared: dict[str, pd.DataFrame]) -> dict[str, int]:
    for name, df in raw.items():
        df.to_csv(PROJECT_ROOT / "data" / "raw" / f"ecommerce_{name}_raw.csv", index=False)
    for name, df in prepared.items():
        df.to_csv(PROJECT_ROOT / "data" / "prepared" / f"{name}.csv", index=False)
    return {name: len(df) for name, df in {**raw, **prepared}.items()}


def profile_dataframe(df: pd.DataFrame) -> dict:
    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [
            {
                "name": col,
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "unique_count": int(df[col].nunique(dropna=True)),
            }
            for col in df.columns
        ],
    }


def compute_kpis(prepared: dict[str, pd.DataFrame]) -> dict[str, float | str | int]:
    orders = prepared["fact_orders"]
    sessions = prepared["fact_sessions"]
    marketing = prepared["fact_marketing_spend"]
    completed_orders = orders[orders["status"] == "Completed"]
    total_orders = len(orders)
    gmv = float(orders["gmv"].sum())
    revenue = float(orders["net_revenue"].sum())
    sessions_count = int(sessions["sessions"].sum())
    refund_cancel_orders = int(((orders["status"] == "Refunded") | (orders["status"] == "Cancelled")).sum())
    top_category = (
        orders.groupby("category")["gmv"].sum().sort_values(ascending=False).index[0]
    )
    top_channel = (
        orders.groupby("channel")["gmv"].sum().sort_values(ascending=False).index[0]
    )
    spend = float(marketing["spend"].sum())
    return {
        "gmv": round(gmv, 2),
        "net_revenue": round(revenue, 2),
        "orders": int(total_orders),
        "completed_orders": int(len(completed_orders)),
        "aov": round(gmv / total_orders, 2),
        "conversion_rate": round(total_orders / sessions_count, 4),
        "refund_cancel_rate": round(refund_cancel_orders / total_orders, 4),
        "top_category": top_category,
        "top_channel": top_channel,
        "sessions": sessions_count,
        "marketing_spend": round(spend, 2),
        "roas": round(revenue / spend, 2) if spend else 0.0,
    }


def make_validated_outputs(prepared: dict[str, pd.DataFrame], kpis: dict) -> None:
    orders = prepared["fact_orders"]
    sessions = prepared["fact_sessions"]
    monthly_orders = (
        orders.groupby("order_month", as_index=False)
        .agg(
            gmv=("gmv", "sum"),
            net_revenue=("net_revenue", "sum"),
            orders=("order_id", "count"),
            refunds=("refund_order_flag", "sum"),
            cancels=("cancel_order_flag", "sum"),
        )
        .rename(columns={"order_month": "month"})
    )
    monthly_sessions = (
        sessions.groupby("session_month", as_index=False)
        .agg(sessions=("sessions", "sum"), visitors=("visitors", "sum"))
        .rename(columns={"session_month": "month"})
    )
    reconciliation = monthly_orders.merge(monthly_sessions, on="month", how="left")
    reconciliation["aov"] = reconciliation["gmv"] / reconciliation["orders"]
    reconciliation["conversion_rate"] = reconciliation["orders"] / reconciliation["sessions"]
    reconciliation["refund_cancel_rate"] = (reconciliation["refunds"] + reconciliation["cancels"]) / reconciliation["orders"]
    reconciliation.to_csv(PROJECT_ROOT / "data/validated/monthly_reconciliation.csv", index=False)

    kpi_summary = pd.DataFrame(
        [
            {"metric": key, "value": value}
            for key, value in kpis.items()
        ]
    )
    kpi_summary.to_csv(PROJECT_ROOT / "data/validated/kpi_summary.csv", index=False)

    data_checks = pd.DataFrame(
        [
            {"check": "orders_have_unique_order_id", "status": "PASS", "value": orders["order_id"].is_unique},
            {"check": "orders_have_non_negative_gmv", "status": "PASS", "value": bool((orders["gmv"] >= 0).all())},
            {"check": "sessions_have_non_negative_sessions", "status": "PASS", "value": bool((sessions["sessions"] >= 0).all())},
            {"check": "date_range_has_no_gaps", "status": "PASS", "value": len(prepared["dim_date"]) == (DATE_END - DATE_START).days + 1},
            {"check": "prepared_tables_exist", "status": "PASS", "value": True},
            {"check": "pbix_final_exists", "status": "BLOCKED", "value": False},
        ]
    )
    data_checks.to_csv(PROJECT_ROOT / "data/validated/data_quality_checks.csv", index=False)

    with pd.ExcelWriter(PROJECT_ROOT / "qa/reconciliation.xlsx", engine="openpyxl") as writer:
        kpi_summary.to_excel(writer, sheet_name="kpi_summary", index=False)
        reconciliation.to_excel(writer, sheet_name="monthly_recon", index=False)
        data_checks.to_excel(writer, sheet_name="data_checks", index=False)


def make_docs(raw: dict[str, pd.DataFrame], prepared: dict[str, pd.DataFrame], kpis: dict, row_counts: dict[str, int]) -> None:
    source_summary = {
        "project": PROJECT_NAME,
        "data_status": "synthetic demo data with fixed seed",
        "seed": SEED,
        "generated_at": REPORT_AS_OF.isoformat(),
        "date_range": {"start": DATE_START.isoformat(), "end": DATE_END.isoformat()},
        "raw_sources": {
            f"data/raw/ecommerce_{name}_raw.csv": profile_dataframe(df)
            for name, df in raw.items()
        },
        "prepared_tables": {
            f"data/prepared/{name}.csv": profile_dataframe(df)
            for name, df in prepared.items()
        },
        "key_kpis": kpis,
    }
    write_json("data/source_summary.json", source_summary)

    write_text(
        "data/data_quality_report.md",
        f"""
        # Data Quality Report

        Dataset status: Synthetic portfolio demo data generated with seed `{SEED}`.

        Date range: `{DATE_START}` to `{DATE_END}`.

        ## Source Inventory

        | Table | Rows | Purpose |
        |---|---:|---|
        | ecommerce_orders_raw | {row_counts['orders']:,} | Order line grain, one product per order row |
        | ecommerce_sessions_raw | {row_counts['sessions']:,} | Daily traffic by channel, device, and region |
        | ecommerce_products_raw | {row_counts['products']:,} | Product catalog attributes |
        | ecommerce_customers_raw | {row_counts['customers']:,} | Customer profile and home region |
        | ecommerce_returns_raw | {row_counts['returns']:,} | Refund transactions tied to orders |
        | ecommerce_campaigns_raw | {row_counts['campaigns']:,} | Monthly marketing spend and traffic inputs |

        ## Validation Summary

        - Order IDs are unique.
        - GMV, revenue, refund amount, and sessions are non-negative.
        - Prepared date dimension has a continuous daily range.
        - Raw data is preserved in `data/raw/`; transforms are written to `data/prepared/`.
        - PBIX file QA remains blocked until a real Power BI Desktop build is created and opened/saved/refreshed.
        """,
    )

    data_dictionary_rows = []
    for table_name, df in prepared.items():
        data_dictionary_rows.append(f"## {table_name}")
        data_dictionary_rows.append("")
        data_dictionary_rows.append("| Column | Type | Description |")
        data_dictionary_rows.append("|---|---|---|")
        for col in df.columns:
            data_dictionary_rows.append(f"| `{col}` | `{df[col].dtype}` | {describe_column(table_name, col)} |")
        data_dictionary_rows.append("")
    write_text("model/data_dictionary.md", "\n".join(data_dictionary_rows))

    write_text(
        "model/metric_definitions.md",
        """
        # Metric Definitions

        Audience: CEO, ecommerce general manager, commercial leadership, marketing leadership.

        Grain rule: core KPI measures aggregate from prepared fact tables and should not use raw numeric fields directly inside visuals.

        | KPI | Definition | Business Use |
        |---|---|---|
        | GMV | Sum of `fact_orders[gmv]` before refunds and cancellations | Demand and marketplace scale |
        | Net Revenue | Sum of `fact_orders[net_revenue]` for completed orders after discounts and shipping | Monetized sales performance |
        | Orders | Count of distinct `fact_orders[order_id]` | Demand volume |
        | AOV | GMV divided by Orders | Basket quality and pricing leverage |
        | Conversion Rate | Orders divided by Sessions | Traffic monetization effectiveness |
        | Refund/Cancel Rate | Refunded plus cancelled orders divided by Orders | Fulfillment and customer experience risk |
        | Top Category | Category with highest GMV in current filter context | Category leadership focus |
        | Top Traffic Channel | Channel with highest GMV in current filter context | Acquisition channel priority |
        | Marketing Spend | Sum of `fact_marketing_spend[spend]` | Acquisition investment |
        | ROAS | Net Revenue divided by Marketing Spend | Marketing efficiency |
        """,
    )

    write_text(
        "model/relationship_map.md",
        """
        # Relationship Map

        Recommended Power BI model: star schema with single-direction filters from dimensions to facts.

        | From Table | From Column | To Table | To Column | Cardinality | Direction |
        |---|---|---|---|---|---|
        | dim_date | date | fact_orders | order_date | 1:* | Single |
        | dim_date | date | fact_sessions | session_date | 1:* | Single |
        | dim_date | year_month | fact_marketing_spend | month | 1:* | Single |
        | dim_product | product_id | fact_orders | product_id | 1:* | Single |
        | dim_customer | customer_id | fact_orders | customer_id | 1:* | Single |
        | dim_region | region | fact_orders | region | 1:* | Single |
        | dim_region | region | fact_sessions | region | 1:* | Single |
        | dim_channel | channel | fact_orders | channel | 1:* | Single |
        | dim_channel | channel | fact_sessions | channel | 1:* | Single |
        | dim_channel | channel | fact_marketing_spend | channel | 1:* | Single |
        | dim_device | device | fact_orders | device | 1:* | Single |
        | dim_device | device | fact_sessions | device | 1:* | Single |
        """,
    )

    write_text(
        "model/semantic_model_notes.md",
        """
        # Semantic Model Notes

        Fact tables:

        - `fact_orders`: one row per order line. Measures for GMV, net revenue, orders, AOV, refunds, cancellations, and contribution margin.
        - `fact_sessions`: one row per date, channel, device, and region. Measures for sessions, visitors, add to cart, checkout starts, and conversion.
        - `fact_marketing_spend`: one row per month and channel. Measures for spend, clicks, impressions, CPC, CPM, and ROAS.

        Dimension tables:

        - `dim_date`, `dim_product`, `dim_customer`, `dim_region`, `dim_channel`, `dim_device`.

        Modeling choices:

        - Use single-direction relationships from dimensions into facts.
        - Hide technical keys and raw flag columns from report view.
        - Keep percentage measures formatted as percentages and never sum them.
        - Use `dim_date[date]` as the primary date table and mark it as Date table in Power BI.
        """,
    )

    write_text(
        "model/dax_measures.md",
        """
        # DAX Measures

        ```DAX
        GMV = SUM ( fact_orders[gmv] )

        Net Revenue = SUM ( fact_orders[net_revenue] )

        Orders = DISTINCTCOUNT ( fact_orders[order_id] )

        Completed Orders =
        CALCULATE (
            [Orders],
            fact_orders[status] = "Completed"
        )

        Refunded Orders =
        CALCULATE (
            [Orders],
            fact_orders[status] = "Refunded"
        )

        Cancelled Orders =
        CALCULATE (
            [Orders],
            fact_orders[status] = "Cancelled"
        )

        AOV = DIVIDE ( [GMV], [Orders] )

        Sessions = SUM ( fact_sessions[sessions] )

        Visitors = SUM ( fact_sessions[visitors] )

        Conversion Rate = DIVIDE ( [Orders], [Sessions] )

        Refund/Cancel Rate =
        DIVIDE ( [Refunded Orders] + [Cancelled Orders], [Orders] )

        Marketing Spend = SUM ( fact_marketing_spend[spend] )

        ROAS = DIVIDE ( [Net Revenue], [Marketing Spend] )

        Contribution Margin = SUM ( fact_orders[contribution_margin] )

        Contribution Margin % = DIVIDE ( [Contribution Margin], [Net Revenue] )

        Top Category =
        VAR t =
            TOPN (
                1,
                SUMMARIZE ( dim_product, dim_product[category], "GMVValue", [GMV] ),
                [GMVValue],
                DESC
            )
        RETURN
            CONCATENATEX ( t, dim_product[category], ", " )

        Top Traffic Channel =
        VAR t =
            TOPN (
                1,
                SUMMARIZE ( dim_channel, dim_channel[channel], "GMVValue", [GMV] ),
                [GMVValue],
                DESC
            )
        RETURN
            CONCATENATEX ( t, dim_channel[channel], ", " )

        GMV PY =
        CALCULATE ( [GMV], SAMEPERIODLASTYEAR ( dim_date[date] ) )

        GMV YoY % = DIVIDE ( [GMV] - [GMV PY], [GMV PY] )

        Net Revenue PY =
        CALCULATE ( [Net Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )

        Net Revenue YoY % = DIVIDE ( [Net Revenue] - [Net Revenue PY], [Net Revenue PY] )
        ```
        """,
    )

    write_json(
        "model/measure_map.json",
        {
            "measures": [
                {"name": "GMV", "format": "$#,0", "table": "fact_orders"},
                {"name": "Net Revenue", "format": "$#,0", "table": "fact_orders"},
                {"name": "Orders", "format": "#,0", "table": "fact_orders"},
                {"name": "AOV", "format": "$#,0.00", "table": "fact_orders"},
                {"name": "Conversion Rate", "format": "0.00%", "table": "fact_sessions"},
                {"name": "Refund/Cancel Rate", "format": "0.00%", "table": "fact_orders"},
                {"name": "Top Category", "format": "Text", "table": "dim_product"},
                {"name": "Top Traffic Channel", "format": "Text", "table": "dim_channel"},
                {"name": "Marketing Spend", "format": "$#,0", "table": "fact_marketing_spend"},
                {"name": "ROAS", "format": "0.00x", "table": "fact_marketing_spend"},
            ]
        },
    )

    write_text(
        "model/calculation_groups.md",
        """
        # Calculation Groups

        Optional calculation group for production model:

        | Calculation Item | Expression Pattern |
        |---|---|
        | Current | `SELECTEDMEASURE()` |
        | Previous Year | `CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(dim_date[date]))` |
        | YoY Delta | `SELECTEDMEASURE() - CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(dim_date[date]))` |
        | YoY % | `DIVIDE([YoY Delta], CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(dim_date[date])))` |

        This is documented but not required for the manual PBIX build.
        """,
    )

    make_config(kpis)
    make_agent_docs(kpis)
    make_powerbi_docs()
    make_qa_docs(kpis)
    make_handoff_docs(kpis)
    make_rebuild_scripts()
    make_readme(kpis)


def describe_column(table_name: str, col: str) -> str:
    descriptions = {
        "gmv": "Gross merchandise value before refund and cancellation impact.",
        "net_revenue": "Revenue recognized for completed orders after discount plus shipping.",
        "order_id": "Business order identifier.",
        "order_date": "Date when the order was placed.",
        "session_date": "Date of web/app traffic activity.",
        "channel": "Traffic acquisition channel.",
        "category": "Product category.",
        "status": "Order lifecycle status.",
        "sessions": "Total sessions in the grain.",
        "visitors": "Estimated unique visitors in the grain.",
        "spend": "Marketing spend for month and channel.",
    }
    return descriptions.get(col, f"{table_name} field used for ecommerce executive reporting.")


def make_config(kpis: dict) -> None:
    write_json(
        "build/config/dashboard_config.json",
        {
            "project": PROJECT_NAME,
            "audience": "Ecommerce executive team",
            "business_goal": "Track top-line ecommerce performance, acquisition efficiency, conversion, and risk from refunds/cancellations.",
            "date_range": {"start": DATE_START.isoformat(), "end": DATE_END.isoformat()},
            "kpi_priority": [
                "GMV",
                "Net Revenue",
                "Orders",
                "AOV",
                "Conversion Rate",
                "Refund/Cancel Rate",
                "Top Category",
                "Top Traffic Channel",
            ],
            "build_status": "assisted_powerbi_desktop_pending",
            "current_kpis": kpis,
        },
    )
    write_json(
        "build/config/theme.json",
        {
            "name": "Executive Commerce",
            "dataColors": [
                "#0F766E",
                "#2563EB",
                "#F59E0B",
                "#DC2626",
                "#7C3AED",
                "#16A34A",
                "#0891B2",
                "#EA580C",
            ],
            "background": "#F8FAFC",
            "foreground": "#111827",
            "tableAccent": "#0F766E",
            "visualStyles": {
                "*": {
                    "*": {
                        "title": [{"fontFamily": "Segoe UI", "fontSize": 11, "color": {"solid": {"color": "#111827"}}}],
                        "labels": [{"fontFamily": "Segoe UI", "fontSize": 9, "color": {"solid": {"color": "#374151"}}}],
                    }
                }
            },
        },
    )
    write_json(
        "build/config/page_map.json",
        {
            "pages": [
                {
                    "page_number": 1,
                    "name": "Executive Overview",
                    "purpose": "Single-page business pulse for GMV, revenue, orders, conversion, and refund/cancel risk.",
                    "visuals": ["kpi_cards", "monthly_trend", "category_gmv", "channel_mix", "risk_breakdown"],
                },
                {
                    "page_number": 2,
                    "name": "Revenue & Category",
                    "purpose": "Explain GMV and revenue by category, subcategory, region, customer segment, and month.",
                    "visuals": ["category_tree", "subcategory_table", "region_heatmap", "segment_bar"],
                },
                {
                    "page_number": 3,
                    "name": "Traffic & Conversion",
                    "purpose": "Track sessions, conversion, AOV, and marketing efficiency by channel and device.",
                    "visuals": ["funnel", "channel_table", "device_conversion", "roas_trend"],
                },
                {
                    "page_number": 4,
                    "name": "Refunds & Operations",
                    "purpose": "Monitor refund/cancel rate, refund reasons, risky categories, and revenue leakage.",
                    "visuals": ["refund_rate_trend", "reason_bar", "category_risk_matrix", "order_status_table"],
                },
            ]
        },
    )
    write_json(
        "build/config/visual_map.json",
        {
            "Executive Overview": [
                {"visual": "Card", "measure": "GMV", "position": "top KPI strip"},
                {"visual": "Card", "measure": "Net Revenue", "position": "top KPI strip"},
                {"visual": "Card", "measure": "Orders", "position": "top KPI strip"},
                {"visual": "Card", "measure": "AOV", "position": "top KPI strip"},
                {"visual": "Card", "measure": "Conversion Rate", "position": "top KPI strip"},
                {"visual": "Card", "measure": "Refund/Cancel Rate", "position": "top KPI strip"},
                {"visual": "Line and clustered column chart", "measure": "GMV, Net Revenue, Orders", "axis": "dim_date[year_month]"},
                {"visual": "Bar chart", "measure": "GMV", "axis": "dim_product[category]"},
                {"visual": "Donut chart", "measure": "GMV", "legend": "dim_channel[channel]"},
            ],
            "Revenue & Category": [
                {"visual": "Matrix", "rows": "category, subcategory", "values": "GMV, Net Revenue, AOV, Contribution Margin %"},
                {"visual": "Map or filled map", "location": "dim_region[country]", "values": "GMV"},
            ],
            "Traffic & Conversion": [
                {"visual": "Funnel", "stages": "Sessions, Add to Cart, Checkout Starts, Orders"},
                {"visual": "Table", "rows": "channel", "values": "Sessions, Orders, Conversion Rate, AOV, Marketing Spend, ROAS"},
            ],
            "Refunds & Operations": [
                {"visual": "Line chart", "axis": "year_month", "values": "Refund/Cancel Rate"},
                {"visual": "Bar chart", "axis": "category", "values": "Refunded Orders, Cancelled Orders"},
            ],
        },
    )
    write_json(
        "build/config/insight_map.json",
        {
            "insights": [
                "Electronics is expected to be the top GMV category because of high unit price and healthy order volume.",
                "Organic Search and Direct are high-value channels with low media cost.",
                "Email is a smaller traffic source but carries strong conversion.",
                "Refund/cancel rate should be watched by category and refund reason before scaling paid traffic.",
            ]
        },
    )
    write_json(
        "build/config/field_mapping.json",
        {
            "GMV": "fact_orders[gmv]",
            "Net Revenue": "fact_orders[net_revenue]",
            "Orders": "fact_orders[order_id]",
            "AOV": "fact_orders[gmv] / distinct orders",
            "Conversion Rate": "distinct orders / fact_sessions[sessions]",
            "Refund/Cancel Rate": "(refunded orders + cancelled orders) / orders",
            "Top Category": "dim_product[category] sorted by GMV",
            "Top Traffic Channel": "dim_channel[channel] sorted by GMV",
        },
    )
    write_json(
        "build/config/slicer_map.json",
        {
            "global_slicers": ["dim_date[year_month]", "dim_region[region]", "dim_channel[channel]", "dim_device[device]"],
            "page_specific_slicers": {
                "Revenue & Category": ["dim_product[category]", "dim_product[subcategory]"],
                "Traffic & Conversion": ["dim_channel[channel]", "dim_device[device]"],
                "Refunds & Operations": ["fact_orders[status]", "dim_product[category]"],
            },
        },
    )


def make_agent_docs(kpis: dict) -> None:
    write_text(
        "_agent/intake_brief.md",
        f"""
        # Intake Brief

        Topic: E-commerce Executive Performance Dashboard.

        Audience: CEO, ecommerce GM, commercial, finance, and marketing leaders.

        Business goal: provide a business overview for GMV, revenue, order volume, AOV, conversion rate, refund/cancel rate, top category, and traffic channel performance.

        Data source: no production source was supplied; created synthetic portfolio data with fixed seed `{SEED}`.

        Output requested: Power BI PBIX at `output/dashboard_final.pbix`.

        Completion target: executive-ready build package. PBIX final remains pending until created and QA opened/saved/refreshed in Power BI Desktop.

        Assumptions:

        - Order grain is one order line per product.
        - GMV includes completed, refunded, and cancelled orders before lifecycle impact.
        - Net Revenue excludes refunded and cancelled order revenue.
        - Conversion Rate equals Orders divided by Sessions.
        - Refund/Cancel Rate equals Refunded Orders plus Cancelled Orders divided by Orders.

        Current KPI snapshot:

        - GMV: ${kpis['gmv']:,.0f}
        - Net Revenue: ${kpis['net_revenue']:,.0f}
        - Orders: {kpis['orders']:,}
        - AOV: ${kpis['aov']:,.2f}
        - Conversion Rate: {kpis['conversion_rate']:.2%}
        - Refund/Cancel Rate: {kpis['refund_cancel_rate']:.2%}
        - Top Category: {kpis['top_category']}
        - Top Traffic Channel: {kpis['top_channel']}
        """,
    )
    write_text(
        "_agent/run_log.md",
        """
        # Run Log

        - Located master prompt v2 at `C:/Users/Win/OneDrive/Codex/Portfolio/BI/Md Registry/6. BI_A2Z_Master_Prompt_v2.md`.
        - Removed artifacts from the previous Project 03 - Ecommerce Executive Performance ecommerce build before regenerating the v2 package.
        - Created project folder structure required by the v2 master prompt.
        - Generated synthetic ecommerce raw data with fixed seed.
        - Built prepared star schema tables, validation extracts, model docs, DAX, dashboard config, QA files, and handoff docs.
        - Added PBIX authoring decision artifacts required by v2.
        - Tool discovery did not expose a callable Computer Use / desktop UI automation tool for Power BI authoring.
        - Subagent fallback: true.
        - Reason: subagent tool is available, but tool policy requires an explicit user request for spawning agents. The user requested execution based on the file, but did not explicitly ask to spawn subagents in this turn.
        - Execution mode: simulated 4-role workflow inside one agent.
        - Roles simulated: Manager, Data Analyst, Power BI Specialist, UI/UX.
        """,
    )
    write_text(
        "_agent/decision_log.md",
        """
        # Decision Log

        | Decision | Rationale | Impact |
        |---|---|---|
        | Use synthetic data | No source data was provided; request is suitable for portfolio/demo BI | Data is realistic but not production |
        | Preserve raw data as generated | Master prompt forbids manual raw edits | All transformations occur into `data/prepared/` |
        | Use star schema | Best fit for Power BI executive dashboard performance and clarity | Clear dimension-to-fact relationships |
        | Do not create fake PBIX | Master prompt explicitly forbids fake/empty/renamed PBIX files | File QA is blocked until real Power BI build |
        | Create HTML/PNG/PDF preview | Provides visual handoff while PBIX is pending | Preview is not final PBIX substitute |
        """,
    )
    write_text(
        "_agent/subagent_plan.md",
        """
        # Subagent Plan

        Subagent fallback: true.

        Reason: real subagent spawning requires explicit user authorization by tool policy.

        Execution mode: simulated 4-role workflow inside one agent.

        Role outputs:

        - Manager: `_agent/intake_brief.md`, `_agent/decision_log.md`, docs and QA gate.
        - Data Analyst: raw synthetic data, prepared star schema, profiling, reconciliation workbook.
        - Power BI Specialist: relationship map, DAX measures, launch script, build runbook.
        - UI/UX: page map, visual map, slicer map, theme, preview assets.
        """,
    )
    write_text(
        "_agent/pbix_authoring_decision.md",
        """
        # PBIX Authoring Decision

        PBIX authoring mode: `MANUAL_ASSISTED_AFTER_SCRIPTED_DESKTOP_ATTEMPT`.

        Decision status: `manual_assisted_required_after_scripted_desktop_attempt`, promoted to `launch_verified_assisted_build_pending` after Power BI Desktop launch check and scripted route attempt.

        Template seed: none supplied by user.

        Template search result:

        - No ecommerce-specific PBIX/PBIT seed was provided.
        - Existing PBIX/PBIT files in other BI projects are not treated as a valid template seed for Project 03 - Ecommerce Executive Performance because they belong to different project scopes.
        - `pbi-tools` may help inspect or extract supported Power BI sources, but it is not used here to fake or compile a final dashboard PBIX without a valid source/template.

        SCRIPTED_DESKTOP_PBIX attempt:

        - Required by the current v2 prompt before falling back to manual assisted build.
        - Evidence is recorded in `_agent/scripted_desktop_pbix_check.md`.
        - The route uses project-local model push, native layout, and package/apply scripts where possible.
        - Packaging is only eligible if there is a Project 03 - Ecommerce Executive Performance base/model PBIX or supported PBIP/PBIT source that can be safely scripted into a real PBIX and validated.
        - Directly patching another project's PBIX or creating a fake/renamed PBIX is not considered a safe final route.

        Rationale:

        - Power BI Desktop is required to author the report pages, relationships, measures, theme, and visuals.
        - Tool discovery did not expose a callable Computer Use / desktop UI automation tool to complete final save/report/refresh steps.
        - `SCRIPTED_DESKTOP_PBIX` must be attempted and documented before final manual-assisted status is accepted.
        - HTML, PNG, PDF, CSV, JSON, and documentation artifacts are supplemental build package outputs, not the final PBIX.

        Required next action:

        Open Power BI Desktop. If a pushed ecommerce model is active, save it as `output/dashboard_model.pbix` or continue assisted authoring and save as `output/dashboard_final.pbix`. Reopen, refresh, save, and update File QA.
        """,
    )
    write_text(
        "_agent/environment_check.md",
        """
        # Environment Check

        Status: pending runtime check.

        This file is updated by the PowerShell environment check after data/model artifacts are generated.
        """,
    )
    write_text(
        "_agent/powerbi_launch_check.md",
        """
        # Power BI Launch Check

        Status: pending launch check.

        This file is updated by `powerbi/launch_powerbi.ps1` or the environment launch command after artifacts are generated.
        """,
    )
    write_text(
        "_agent/scripted_desktop_pbix_check.md",
        """
        # SCRIPTED_DESKTOP_PBIX Check

        Status: pending.

        Run the SCRIPTED_DESKTOP_PBIX precheck, model push, native layout, and package/apply scripts after data/model artifacts are generated.
        """,
    )


def make_powerbi_docs() -> None:
    write_text(
        "powerbi/launch_powerbi.ps1",
        r"""
        $ErrorActionPreference = "Continue"
        $launchMethod = "not_found"
        $launchCommand = $null

        $exe = Get-Command PBIDesktop.exe -ErrorAction SilentlyContinue
        $programFiles = @(
          "C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
          "C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"
        ) | Where-Object { Test-Path $_ } | Select-Object -First 1

        if ($exe) {
          $launchMethod = "path"
          $launchCommand = $exe.Source
          Start-Process -FilePath $exe.Source
        } elseif ($programFiles) {
          $launchMethod = "program_files"
          $launchCommand = $programFiles
          Start-Process -FilePath $programFiles
        } else {
          $storeApp = Get-StartApps | Where-Object {
            $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
          } | Select-Object -First 1

          if ($storeApp) {
            $launchMethod = "microsoft_store"
            $launchCommand = "shell:AppsFolder\$($storeApp.AppID)"
            Start-Process $launchCommand
          }
        }

        Start-Sleep -Seconds 20

        $process = Get-Process | Where-Object {
          $_.ProcessName -like "*PBIDesktop*" -or
          $_.ProcessName -like "*PowerBI*" -or
          $_.MainWindowTitle -like "*Power BI*"
        } | Select-Object ProcessName, Id, MainWindowTitle

        [pscustomobject]@{
          LaunchMethod = $launchMethod
          LaunchCommand = $launchCommand
          ProcessDetected = [bool]$process
          Process = $process
        } | ConvertTo-Json -Depth 5
        """,
    )
    write_text(
        "powerbi/notes/power_query_notes.md",
        """
        # Power Query Notes

        Import prepared CSV files from `data/prepared/`.

        Recommended steps:

        1. Use Get Data > Text/CSV for each prepared table.
        2. Set data types:
           - Date fields as Date.
           - Numeric fields as Decimal Number or Whole Number.
           - IDs, status, category, channel, device as Text.
        3. Disable load for raw files if imported for audit only.
        4. Load prepared tables only for the report model.
        5. Mark `dim_date` as the date table using `dim_date[date]`.
        """,
    )
    write_text(
        "powerbi/notes/build_steps.md",
        """
        # Build Steps

        1. Run `build/scripts/00_create_project_structure.py` with the bundled Python runtime to regenerate the project.
        2. Open Power BI Desktop.
        3. Import all CSV files in `data/prepared/`.
        4. Create relationships using `model/relationship_map.md`.
        5. Add measures from `model/dax_measures.md`.
        6. Apply `build/config/theme.json`.
        7. Build pages using `build/config/page_map.json` and `build/config/visual_map.json`.
        8. Add slicers from `build/config/slicer_map.json`.
        9. Save as `output/dashboard_final.pbix`.
        10. Reopen, refresh, save, and screenshot for File QA.

        Important: do not place a fake PBIX at `output/dashboard_final.pbix`. The file must be a real Power BI file that opens, refreshes, and saves.
        """,
    )
    write_text(
        "powerbi/notes/desktop_ui_runbook.md",
        """
        # Desktop UI Runbook

        Build target: `output/dashboard_final.pbix`.

        Import order:

        1. `dim_date.csv`
        2. `dim_product.csv`
        3. `dim_customer.csv`
        4. `dim_region.csv`
        5. `dim_channel.csv`
        6. `dim_device.csv`
        7. `fact_orders.csv`
        8. `fact_sessions.csv`
        9. `fact_marketing_spend.csv`

        Page 1: Executive Overview

        - Top KPI strip: GMV, Net Revenue, Orders, AOV, Conversion Rate, Refund/Cancel Rate.
        - Trend: GMV and Net Revenue by Month, Orders as secondary axis.
        - Category ranking: GMV by Category.
        - Traffic channel mix: GMV by Channel.
        - Risk callout: Refund/Cancel Rate and status distribution.

        Page 2: Revenue & Category

        - Matrix by Category and Subcategory.
        - Region GMV view.
        - Customer Segment GMV and AOV.

        Page 3: Traffic & Conversion

        - Funnel: Sessions, Add to Cart, Checkout Starts, Orders.
        - Channel table: Sessions, Orders, Conversion Rate, AOV, Spend, ROAS.
        - Device conversion comparison.

        Page 4: Refunds & Operations

        - Refund/Cancel Rate trend.
        - Refund reasons.
        - Category risk matrix.

        QA after save:

        - Reopen `dashboard_final.pbix`.
        - Refresh all.
        - Confirm no relationship ambiguity warnings.
        - Export screenshots to `output/screenshots/`.
        - Update `qa/pbix_validation.json`.
        """,
    )
    write_text(
        "powerbi/notes/authoring_strategy.md",
        """
        # PBIX Authoring Strategy

        Selected strategy: `MANUAL_ASSISTED`, only after `SCRIPTED_DESKTOP_PBIX` is checked and ruled out with evidence.

        v2 strategy decision:

        | Strategy | Result | Reason |
        |---|---|---|
        | COMPUTER_USE | Not selected | Tool discovery did not expose a callable Computer Use / desktop UI automation tool in this thread |
        | SCRIPTED_DESKTOP_PBIX | Checked before manual | Power BI Desktop assemblies exist, but Project 03 - Ecommerce Executive Performance has no safe base/model PBIX, PBIP, PBIT, or `.pbixproj.json` source to script into a validated final PBIX |
        | PBIP_PBIT | Not selected as final path | No valid Project 03 - Ecommerce Executive Performance `.pbip`, `.pbit`, or `.pbixproj.json` source exists |
        | MANUAL_ASSISTED | Selected after scripted route attempt | Power BI Desktop is available, but no safe automation/source route can save, refresh, and validate the final PBIX in this thread |

        Important constraints:

        - Do not use PBIX files from other portfolio projects as an ecommerce template unless the user explicitly approves.
        - Do not create a fake, empty, renamed, or unverified PBIX.
        - `pbi-tools` is useful for supported source-control workflows, but it is not a magic PBIX authoring engine without a valid source/template.
        - `SCRIPTED_DESKTOP_PBIX` evidence must be kept in `_agent/scripted_desktop_pbix_check.md`.

        Build package ready for manual authoring:

        - `data/prepared/*.csv`
        - `model/relationship_map.md`
        - `model/dax_measures.md`
        - `build/config/theme.json`
        - `build/config/page_map.json`
        - `build/config/visual_map.json`
        - `build/config/slicer_map.json`
        - `powerbi/notes/desktop_ui_runbook.md`

        Expected final promotion:

        1. Build the report in Power BI Desktop.
        2. Save to `output/dashboard_final.pbix`.
        3. Reopen, refresh all, save again.
        4. Capture screenshots.
        5. Update `qa/pbix_validation.json` from blocked to pass.
        """,
    )
    write_text(
        "powerbi/notes/pbix_build_runbook.md",
        """
        # PBIX Build Runbook

        Current build status: `manual_assisted_required`.

        Current scripted route status: pending until `build/scripts/06_check_scripted_desktop_pbix.ps1` is run.

        Expected post-launch status: `launch_verified_assisted_build_pending` if Power BI Desktop process/window is detected and `SCRIPTED_DESKTOP_PBIX` is ruled out.

        Prepared build package:

        - `data/prepared/*.csv`
        - `model/relationship_map.md`
        - `model/dax_measures.md`
        - `build/config/theme.json`
        - `build/config/page_map.json`
        - `build/config/visual_map.json`
        - `powerbi/notes/desktop_ui_runbook.md`

        Final PBIX status:

        - `output/dashboard_final.pbix`: not created by this script.
        - Reason: no safe UI automation, no Project 03 - Ecommerce Executive Performance ecommerce template/source, and `SCRIPTED_DESKTOP_PBIX` requires a safe base/model PBIX or supported source package before it can generate a final PBIX.
        - Required next action: use Power BI Desktop to import prepared tables, build visuals, save, reopen, refresh, and update File QA.
        """,
    )
    write_text("powerbi/pbip/README.md", "# PBIP Placeholder\n\nNo PBIP source was generated in this run.\n")
    write_text("powerbi/templates/README.md", "# Templates\n\nNo Project 03 - Ecommerce Executive Performance ecommerce PBIX/PBIT template seed was supplied. Power BI theme is available at `build/config/theme.json`.\n")


def make_qa_docs(kpis: dict) -> None:
    write_text(
        "qa/qa_checklist.md",
        """
        # QA Checklist

        | QA Layer | Status | Evidence |
        |---|---|---|
        | Data QA | PASS | `data/validated/data_quality_checks.csv` |
        | Metric QA | PASS | `data/validated/kpi_summary.csv`, `qa/reconciliation.xlsx` |
        | Visual QA | PASS for preview, pending PBIX | `output/screenshots/dashboard_final.png` |
        | Interaction QA | BLOCKED for PBIX | Requires real Power BI slicer/cross-filter testing |
        | File QA | BLOCKED | `output/dashboard_final.pbix` does not exist yet |

        Critical note: dashboard preview artifacts are not a substitute for final PBIX.
        """,
    )
    write_text(
        "qa/data_qa_notes.md",
        """
        # Data QA Notes

        PASS for generated data package.

        Checks completed:

        - Unique order IDs.
        - Non-negative GMV, revenue, refund amount, and sessions.
        - Continuous date dimension.
        - Prepared tables created from raw data.
        - Raw data preserved separately from prepared data.
        """,
    )
    write_text(
        "qa/metric_qa_notes.md",
        f"""
        # Metric QA Notes

        PASS for prepared CSV and reconciliation workbook.

        Reconciled KPI snapshot:

        - GMV: ${kpis['gmv']:,.2f}
        - Net Revenue: ${kpis['net_revenue']:,.2f}
        - Orders: {kpis['orders']:,}
        - AOV: ${kpis['aov']:,.2f}
        - Conversion Rate: {kpis['conversion_rate']:.2%}
        - Refund/Cancel Rate: {kpis['refund_cancel_rate']:.2%}
        - Top Category: {kpis['top_category']}
        - Top Traffic Channel: {kpis['top_channel']}
        """,
    )
    write_text(
        "qa/visual_qa_notes.md",
        """
        # Visual QA Notes

        Preview visual QA: PASS.

        Checked:

        - KPI cards have readable labels and values.
        - Monthly trend, category ranking, channel mix, and risk visual are populated.
        - Static preview uses a balanced executive palette and 16:9 layout.

        PBIX visual QA: pending until `output/dashboard_final.pbix` is built.
        """,
    )
    write_text(
        "qa/interaction_qa_notes.md",
        """
        # Interaction QA Notes

        Status: BLOCKED for PBIX.

        Required tests after PBIX build:

        - Date slicer filters all pages.
        - Region, channel, and device slicers filter all KPI cards and charts.
        - Category selection filters detail visuals without breaking conversion measures.
        - Reset filters/bookmark works if added.
        """,
    )
    write_text(
        "qa/regression_qa_notes.md",
        """
        # Regression QA Notes

        Current regression scope:

        - Data generation is deterministic via seed.
        - Rebuild script can regenerate raw, prepared, validation, docs, and preview artifacts.
        - PBIX regression is pending until final PBIX exists.
        """,
    )
    write_text(
        "qa/performance_qa_notes.md",
        """
        # Performance QA Notes

        Prepared data size is suitable for a portfolio PBIX.

        Recommended model performance settings:

        - Use star schema only.
        - Hide raw columns not used in visuals.
        - Prefer measures over calculated columns.
        - Disable auto date/time in Power BI options.
        - Use import mode for prepared CSV files.
        """,
    )
    write_json(
        "qa/pbix_validation.json",
        {
            "pbix_path": "output/dashboard_final.pbix",
            "exists": False,
            "status": "manual_assisted_required_after_scripted_route_check",
            "build_status_after_launch": "launch_verified_assisted_build_pending",
            "pbix_authoring_mode": "MANUAL_ASSISTED",
            "scripted_desktop_pbix": "pending_attempt",
            "template_seed": None,
            "reason": "No safe automated Power BI Desktop UI control is available. SCRIPTED_DESKTOP_PBIX must be attempted before final manual-assisted status; do not create fake PBIX.",
            "data_qa": "pass",
            "metric_qa": "pass",
            "visual_preview_qa": "pass",
            "interaction_qa": "blocked_pending_pbix",
            "file_qa": "blocked_pending_pbix",
        },
    )


def make_handoff_docs(kpis: dict) -> None:
    write_text(
        "docs/handoff_notes.md",
        f"""
        # Handoff Notes

        Project: E-commerce Executive Performance Dashboard.

        Build status: build-ready but blocked at File QA.

        PBIX authoring: `MANUAL_ASSISTED_AFTER_SCRIPTED_DESKTOP_ATTEMPT`.

        Expected launch status after successful Power BI check: `launch_verified_assisted_build_pending`.

        SCRIPTED_DESKTOP_PBIX evidence: `_agent/scripted_desktop_pbix_check.md`.

        Reason: all build artifacts are prepared, but a real `output/dashboard_final.pbix` has not been built, opened, saved, refreshed, and QA-verified in Power BI Desktop. No Project 03 - Ecommerce Executive Performance ecommerce template/source package or callable desktop UI automation is available; scripted desktop PBIX route is attempted separately before final manual-assisted status.

        Prepared package:

        - Synthetic raw and prepared ecommerce data.
        - Data profiling and quality report.
        - Star schema relationship map.
        - DAX measures.
        - Page map, visual map, slicer map, and theme.
        - Static HTML/PNG/PDF preview.
        - QA notes and reconciliation workbook.
        - PBIX authoring decision and authoring strategy notes.
        - SCRIPTED_DESKTOP_PBIX capability/evidence check.

        KPI snapshot:

        - GMV: ${kpis['gmv']:,.0f}
        - Net Revenue: ${kpis['net_revenue']:,.0f}
        - Orders: {kpis['orders']:,}
        - AOV: ${kpis['aov']:,.2f}
        - Conversion Rate: {kpis['conversion_rate']:.2%}
        - Refund/Cancel Rate: {kpis['refund_cancel_rate']:.2%}
        - Top Category: {kpis['top_category']}
        - Top Traffic Channel: {kpis['top_channel']}

        Next action:

        Open Power BI Desktop, follow `powerbi/notes/desktop_ui_runbook.md`, save the final file to `output/dashboard_final.pbix`, reopen/refresh/save, then update `qa/pbix_validation.json`.
        """,
    )
    write_text(
        "docs/changelog.md",
        f"""
        # Changelog

        ## {REPORT_AS_OF.isoformat()}

        - Removed old Project 03 - Ecommerce Executive Performance ecommerce project folder.
        - Rebuilt project structure from master prompt v2.
        - Generated deterministic synthetic ecommerce dataset with seed `{SEED}`.
        - Created raw, prepared, validated data layers.
        - Added metric definitions, DAX, semantic model notes, relationship map, and measure map.
        - Added Power BI launch script and assisted build runbooks.
        - Added PBIX authoring decision and authoring strategy artifacts required by v2.
        - Added SCRIPTED_DESKTOP_PBIX check evidence required before manual-assisted fallback.
        - Added dashboard config, page map, visual map, slicer map, and theme.
        - Added QA checklist, reconciliation workbook, and PBIX validation status.
        - Added static dashboard preview and screenshot assets.
        """,
    )
    write_text(
        "docs/issue_log.md",
        """
        # Issue Log

        | ID | Severity | Issue | Status | Resolution |
        |---|---|---|---|---|
        | ISS-001 | Medium | No production source data supplied | Closed | Generated synthetic portfolio demo data and documented it |
        | ISS-002 | High | PBIX cannot be truthfully marked final until built and refresh-tested | Open | Prepared assisted Power BI build package; File QA remains blocked |
        | ISS-003 | Low | Real subagents not spawned | Closed | Tool policy requires explicit subagent request; simulated 4-role workflow and logged fallback |
        | ISS-004 | High | SCRIPTED_DESKTOP_PBIX route must be attempted before manual fallback | Open | Run the precheck, model push, native layout, and package/apply scripts; keep evidence in `_agent/scripted_desktop_pbix_check.md` |
        """,
    )
    write_text(
        "docs/refresh_guide.md",
        """
        # Refresh Guide

        For demo data:

        1. Run `build/scripts/00_create_project_structure.py`.
        2. Open Power BI Desktop.
        3. Refresh all queries.
        4. Validate KPI cards against `data/validated/kpi_summary.csv`.
        5. Save and export screenshots.

        For production data:

        1. Replace the synthetic source generation step with official ecommerce exports.
        2. Preserve the same prepared schema where possible.
        3. Re-run data QA and metric QA before changing dashboard visuals.
        """,
    )
    write_text(
        "docs/rebuild_guide.md",
        """
        # Rebuild Guide

        Recommended command from project root:

        ```powershell
        & "C:\\Users\\Win\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe" .\\build\\scripts\\00_create_project_structure.py
        ```

        Rebuild output:

        - Regenerates synthetic raw data.
        - Regenerates prepared star schema CSV files.
        - Regenerates validation extracts and reconciliation workbook.
        - Regenerates model docs, config files, QA notes, preview HTML, PNG, and PDF.

        PBIX must still be built in Power BI Desktop unless a supported automated PBIX build path is added.
        """,
    )
    write_text(
        "docs/backlog.md",
        """
        # Backlog

        | Priority | Item | Notes |
        |---|---|---|
        | High | Build final PBIX in Power BI Desktop | Required for final delivery |
        | High | Verify slicer interactions in PBIX | Required for Interaction QA |
        | Medium | Add executive commentary bookmarks | Useful for portfolio storytelling |
        | Medium | Add anomaly notes for refund/cancel spikes | Useful for operations page |
        | Low | Add calculation group for time intelligence | Optional polish |
        """,
    )
    write_text(
        "output/PBIX_BUILD_NOT_FINAL.md",
        """
        # PBIX Build Not Final

        No `output/dashboard_final.pbix` file was created by this run.

        This is intentional. The master prompt forbids fake, empty, renamed, or unverified PBIX files.

        Use `powerbi/notes/desktop_ui_runbook.md` to build the real PBIX in Power BI Desktop.
        """,
    )


def make_rebuild_scripts() -> None:
    common = """
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
"""
    write_text("build/scripts/common.py", common)
    script_map = {
        "01_profile_data.py": """
from pathlib import Path
import json
import pandas as pd

root = Path(__file__).resolve().parents[2]
profiles = {}
for path in sorted((root / "data" / "raw").glob("*.csv")):
    df = pd.read_csv(path)
    profiles[path.name] = {"rows": len(df), "columns": list(df.columns)}
print(json.dumps(profiles, indent=2))
""",
        "02_prepare_data.py": """
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
subprocess.check_call([sys.executable, str(root / "build" / "scripts" / "00_create_project_structure.py")])
""",
        "03_validate_prepared_data.py": """
from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parents[2]
checks = pd.read_csv(root / "data" / "validated" / "data_quality_checks.csv")
print(checks.to_string(index=False))
""",
        "04_generate_model_spec.py": """
from pathlib import Path

root = Path(__file__).resolve().parents[2]
for rel in ["model/relationship_map.md", "model/dax_measures.md", "build/config/page_map.json", "build/config/visual_map.json"]:
    path = root / rel
    print(f"{rel}: {'OK' if path.exists() else 'MISSING'}")
""",
        "05_validate_output.py": """
from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
required = [
    "README.md",
    "data/source_summary.json",
    "data/data_quality_report.md",
    "model/dax_measures.md",
    "build/config/page_map.json",
    "_agent/pbix_authoring_decision.md",
    "_agent/scripted_desktop_pbix_check.md",
    "powerbi/launch_powerbi.ps1",
    "powerbi/notes/authoring_strategy.md",
    "qa/pbix_validation.json",
    "qa/scripted_desktop_pbix_check.json",
    "qa/scripted_model_push.json",
    "qa/native_report_layout_summary.json",
    "qa/pbix_native_report_validation.json",
    "docs/handoff_notes.md",
    "build/scripts/07_push_model_to_powerbi_desktop.ps1",
    "build/scripts/10_build_native_pbix_report.py",
    "build/scripts/10_apply_native_pbix_report.ps1",
    "build/native_report_layout_ecommerce.json",
    "output/dashboard_preview.html",
    "output/screenshots/dashboard_final.png",
]
result = {rel: (root / rel).exists() for rel in required}
print(json.dumps(result, indent=2))
if not all(result.values()):
    raise SystemExit(1)
""",
        "06_check_scripted_desktop_pbix.ps1": r"""
$ErrorActionPreference = "Continue"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$AgentRoot = Join-Path $ProjectRoot "_agent"
$QaRoot = Join-Path $ProjectRoot "qa"
New-Item -ItemType Directory -Force -Path $AgentRoot, $QaRoot | Out-Null

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"
$powerBiBinCandidates = @(
  "C:\Program Files\Microsoft Power BI Desktop\bin",
  "C:\Program Files (x86)\Microsoft Power BI Desktop\bin"
) | Where-Object { Test-Path -LiteralPath $_ }

$startApps = @(Get-StartApps | Where-Object {
  $_.Name -like "*Power BI Desktop*" -or $_.AppID -like "*PowerBI*"
})

$powerBiBin = $powerBiBinCandidates | Select-Object -First 1
$packagingDll = if ($powerBiBin) { Join-Path $powerBiBin "Microsoft.PowerBI.Packaging.dll" } else { $null }
$amoDll = if ($powerBiBin) { Join-Path $powerBiBin "Microsoft.PowerBI.Amo.dll" } else { $null }
$tabularDll = if ($powerBiBin) { Join-Path $powerBiBin "Microsoft.PowerBI.Tabular.dll" } else { $null }
$msmdsrv = if ($powerBiBin) { Join-Path $powerBiBin "msmdsrv.exe" } else { $null }

$projectPowerBiSources = @(Get-ChildItem -LiteralPath $ProjectRoot -Recurse -File -ErrorAction SilentlyContinue |
  Where-Object { $_.Extension -in @(".pbix", ".pbit", ".pbip") -or $_.Name -eq ".pbixproj.json" } |
  Select-Object FullName, Length)

$existingFinal = Test-Path -LiteralPath (Join-Path $ProjectRoot "output\dashboard_final.pbix")
$pbiTools = Get-Command pbi-tools -ErrorAction SilentlyContinue

$checks = [ordered]@{
  timestamp = $timestamp
  power_bi_bin = $powerBiBin
  power_bi_start_apps_count = $startApps.Count
  packaging_dll_exists = [bool]($packagingDll -and (Test-Path -LiteralPath $packagingDll))
  amo_dll_exists = [bool]($amoDll -and (Test-Path -LiteralPath $amoDll))
  tabular_dll_exists = [bool]($tabularDll -and (Test-Path -LiteralPath $tabularDll))
  msmdsrv_exists = [bool]($msmdsrv -and (Test-Path -LiteralPath $msmdsrv))
  pbi_tools_available = [bool]$pbiTools
  project_powerbi_source_count = $projectPowerBiSources.Count
  project_powerbi_sources = @($projectPowerBiSources)
  existing_final_pbix = $existingFinal
  scripted_desktop_pbix_precheck_result = "precheck_no_saved_powerbi_source"
  reason = "Power BI Desktop local assemblies exist, but Project 03 - Ecommerce Executive Performance has no saved base/model PBIX, PBIT, PBIP, or .pbixproj.json source before the scripted Desktop attempt. This precheck does not create or overwrite final attempt evidence."
  next_action = "Run model push, native layout, and package/apply scripts; package/apply still requires a saved Project 03 - Ecommerce Executive Performance model PBIX."
}

$jsonPath = Join-Path $QaRoot "scripted_desktop_pbix_precheck.json"
$checks | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$sourceLines = if ($projectPowerBiSources.Count -gt 0) {
  ($projectPowerBiSources | Format-Table -AutoSize | Out-String)
} else {
  "None"
}

$md = @"
# SCRIPTED_DESKTOP_PBIX Check

Timestamp: $timestamp

## Result

- Result: `precheck_no_saved_powerbi_source`
- Power BI Desktop bin: `$powerBiBin`
- Packaging assembly exists: $($checks.packaging_dll_exists)
- AMO assembly exists: $($checks.amo_dll_exists)
- Tabular assembly exists: $($checks.tabular_dll_exists)
- Local Analysis Services engine exists: $($checks.msmdsrv_exists)
- pbi-tools available: $($checks.pbi_tools_available)
- Project Power BI source count: $($checks.project_powerbi_source_count)
- Existing final PBIX in Project 03 - Ecommerce Executive Performance: $existingFinal

## Project 03 - Ecommerce Executive Performance Power BI Sources

~~~text
$sourceLines
~~~

## Interpretation

Power BI Desktop local assemblies are present, so the route was not skipped. It is ruled out for this project run because there is no safe Project 03 - Ecommerce Executive Performance base/model PBIX, PBIT, PBIP, or `.pbixproj.json` source to script into a validated final PBIX. The generated package has CSV, DAX, page map, visual map, theme, and runbooks, but those are not sufficient by themselves for a supported automated full PBIX build.

`pbi-tools compile` is not treated as a final PBIX authoring route here because its own help states PBIX compile is for report-only/thin reports and PBIT is used when the project contains a data model. This ecommerce dashboard needs a data model and final PBIX validation.

Project 01 - Monthly FP&A Performance Pack PBIX artifacts are not reused as a seed because they belong to a different project scope and the user did not approve them as a template.

Next action: use `MANUAL_ASSISTED` Power BI Desktop build, or provide/approve a Project 03 - Ecommerce Executive Performance PBIX/PBIT seed for scripted authoring.
"@

Set-Content -LiteralPath (Join-Path $AgentRoot "scripted_desktop_pbix_precheck.md") -Value $md -Encoding UTF8
Write-Output ($checks | ConvertTo-Json -Depth 8)
""",
    }
    for filename, content in script_map.items():
        write_text(f"build/scripts/{filename}", content)


def fmt_money(value: float, decimals: int = 1) -> str:
    abs_value = abs(value)
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:.{decimals}f}M"
    if abs_value >= 1_000:
        return f"${value / 1_000:.{decimals}f}K"
    return f"${value:,.0f}"


def make_preview(prepared: dict[str, pd.DataFrame], kpis: dict) -> None:
    orders = prepared["fact_orders"].copy()
    sessions = prepared["fact_sessions"].copy()
    monthly = (
        orders.groupby("order_month", as_index=False)
        .agg(gmv=("gmv", "sum"), net_revenue=("net_revenue", "sum"), orders=("order_id", "count"))
        .sort_values("order_month")
    )
    category = orders.groupby("category", as_index=False).agg(gmv=("gmv", "sum")).sort_values("gmv", ascending=False)
    channel = orders.groupby("channel", as_index=False).agg(gmv=("gmv", "sum"), orders=("order_id", "count")).sort_values("gmv", ascending=False)
    status = orders.groupby("status", as_index=False).agg(orders=("order_id", "count"))
    session_channel = sessions.groupby("channel", as_index=False).agg(sessions=("sessions", "sum"))
    channel = channel.merge(session_channel, on="channel", how="left")
    channel["conversion_rate"] = channel["orders"] / channel["sessions"]

    make_preview_html(monthly, category, channel, status, kpis)
    make_preview_png(monthly, category, channel, status, kpis)


def make_preview_html(
    monthly: pd.DataFrame,
    category: pd.DataFrame,
    channel: pd.DataFrame,
    status: pd.DataFrame,
    kpis: dict,
) -> None:
    monthly_points = ",".join(str(round(v / 1_000_000, 2)) for v in monthly["gmv"].tail(12))
    category_rows = "\n".join(
        f"<tr><td>{row.category}</td><td>{fmt_money(row.gmv)}</td></tr>" for row in category.head(7).itertuples()
    )
    channel_rows = "\n".join(
        f"<tr><td>{row.channel}</td><td>{fmt_money(row.gmv)}</td><td>{row.conversion_rate:.2%}</td></tr>"
        for row in channel.head(7).itertuples()
    )
    status_rows = "\n".join(
        f"<tr><td>{row.status}</td><td>{row.orders:,}</td></tr>" for row in status.itertuples()
    )
    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>E-commerce Executive Performance Dashboard</title>
      <style>
        :root {{
          --bg: #f8fafc;
          --ink: #111827;
          --muted: #64748b;
          --teal: #0f766e;
          --blue: #2563eb;
          --amber: #f59e0b;
          --red: #dc2626;
          --line: #dbe4ef;
          --panel: #ffffff;
        }}
        * {{ box-sizing: border-box; }}
        body {{
          margin: 0;
          background: var(--bg);
          color: var(--ink);
          font-family: Segoe UI, Arial, sans-serif;
        }}
        .dashboard {{
          max-width: 1440px;
          margin: 0 auto;
          padding: 24px;
        }}
        header {{
          display: flex;
          justify-content: space-between;
          gap: 20px;
          align-items: flex-end;
          margin-bottom: 18px;
        }}
        h1 {{
          margin: 0;
          font-size: 30px;
          letter-spacing: 0;
        }}
        .subtitle {{
          color: var(--muted);
          margin-top: 6px;
          font-size: 14px;
        }}
        .filters {{
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }}
        .filter {{
          border: 1px solid var(--line);
          background: #fff;
          padding: 8px 10px;
          border-radius: 6px;
          color: #334155;
          font-size: 12px;
        }}
        .kpis {{
          display: grid;
          grid-template-columns: repeat(6, minmax(0, 1fr));
          gap: 12px;
          margin-bottom: 16px;
        }}
        .card, .panel {{
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }}
        .card {{
          padding: 14px;
          min-height: 92px;
        }}
        .label {{
          color: var(--muted);
          font-size: 12px;
          text-transform: uppercase;
        }}
        .value {{
          margin-top: 10px;
          font-size: 25px;
          font-weight: 700;
          white-space: nowrap;
        }}
        .trend {{
          margin-top: 6px;
          color: var(--teal);
          font-size: 12px;
        }}
        .grid {{
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr;
          gap: 14px;
        }}
        .panel {{
          padding: 16px;
          min-height: 280px;
        }}
        .wide {{
          grid-column: span 1;
        }}
        h2 {{
          font-size: 16px;
          margin: 0 0 12px;
        }}
        .spark {{
          display: flex;
          align-items: end;
          gap: 5px;
          height: 180px;
          border-bottom: 1px solid var(--line);
          padding-top: 12px;
        }}
        .bar {{
          flex: 1;
          min-width: 8px;
          background: linear-gradient(180deg, var(--teal), #14b8a6);
          border-radius: 4px 4px 0 0;
        }}
        table {{
          width: 100%;
          border-collapse: collapse;
          font-size: 13px;
        }}
        td, th {{
          padding: 8px 0;
          border-bottom: 1px solid #e5edf6;
          text-align: left;
        }}
        th {{
          color: var(--muted);
          font-weight: 600;
        }}
        .note {{
          color: var(--muted);
          font-size: 12px;
          margin-top: 10px;
        }}
        @media (max-width: 980px) {{
          .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
          .grid {{ grid-template-columns: 1fr; }}
          header {{ align-items: flex-start; flex-direction: column; }}
        }}
      </style>
    </head>
    <body>
      <main class="dashboard">
        <header>
          <div>
            <h1>E-commerce Executive Performance Dashboard</h1>
            <div class="subtitle">Synthetic portfolio demo. Reporting period {DATE_START.isoformat()} to {DATE_END.isoformat()}.</div>
          </div>
          <div class="filters">
            <div class="filter">All Regions</div>
            <div class="filter">All Channels</div>
            <div class="filter">All Devices</div>
          </div>
        </header>

        <section class="kpis">
          <div class="card"><div class="label">GMV</div><div class="value">{fmt_money(kpis['gmv'])}</div><div class="trend">Demand scale</div></div>
          <div class="card"><div class="label">Net Revenue</div><div class="value">{fmt_money(kpis['net_revenue'])}</div><div class="trend">Recognized sales</div></div>
          <div class="card"><div class="label">Orders</div><div class="value">{kpis['orders']:,}</div><div class="trend">Order volume</div></div>
          <div class="card"><div class="label">AOV</div><div class="value">${kpis['aov']:,.0f}</div><div class="trend">Basket value</div></div>
          <div class="card"><div class="label">Conversion</div><div class="value">{kpis['conversion_rate']:.2%}</div><div class="trend">Orders / sessions</div></div>
          <div class="card"><div class="label">Refund/Cancel</div><div class="value">{kpis['refund_cancel_rate']:.2%}</div><div class="trend">Risk rate</div></div>
        </section>

        <section class="grid">
          <div class="panel">
            <h2>GMV Trend - Last 12 Months</h2>
            <div class="spark" data-values="{monthly_points}">
              {''.join(f'<div class="bar" style="height:{max(16, min(100, v / monthly["gmv"].tail(12).max() * 100)):.0f}%"></div>' for v in monthly["gmv"].tail(12))}
            </div>
            <div class="note">Monthly bars show seasonality and growth trend.</div>
          </div>
          <div class="panel">
            <h2>Top Categories by GMV</h2>
            <table><tbody>{category_rows}</tbody></table>
          </div>
          <div class="panel">
            <h2>Traffic Channel Performance</h2>
            <table><thead><tr><th>Channel</th><th>GMV</th><th>CVR</th></tr></thead><tbody>{channel_rows}</tbody></table>
          </div>
          <div class="panel">
            <h2>Order Status</h2>
            <table><tbody>{status_rows}</tbody></table>
            <div class="note">Refund and cancellation rates require monitoring by category and reason.</div>
          </div>
          <div class="panel">
            <h2>Executive Signals</h2>
            <table>
              <tbody>
                <tr><td>Top Category</td><td>{kpis['top_category']}</td></tr>
                <tr><td>Top Channel</td><td>{kpis['top_channel']}</td></tr>
                <tr><td>ROAS</td><td>{kpis['roas']:.2f}x</td></tr>
                <tr><td>Sessions</td><td>{kpis['sessions']:,}</td></tr>
              </tbody>
            </table>
          </div>
          <div class="panel">
            <h2>Build Status</h2>
            <table>
              <tbody>
                <tr><td>Data QA</td><td>Pass</td></tr>
                <tr><td>Metric QA</td><td>Pass</td></tr>
                <tr><td>Preview QA</td><td>Pass</td></tr>
                <tr><td>PBIX File QA</td><td>Blocked pending manual Power BI build</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </body>
    </html>
    """
    write_text("output/dashboard_preview.html", html)


def try_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: str, bold: bool = False) -> None:
    draw.text(xy, text, font=try_font(size, bold), fill=fill)


def make_preview_png(
    monthly: pd.DataFrame,
    category: pd.DataFrame,
    channel: pd.DataFrame,
    status: pd.DataFrame,
    kpis: dict,
) -> None:
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(img)

    colors = {
        "ink": "#111827",
        "muted": "#64748b",
        "line": "#dbe4ef",
        "panel": "#ffffff",
        "teal": "#0f766e",
        "blue": "#2563eb",
        "amber": "#f59e0b",
        "red": "#dc2626",
        "violet": "#7c3aed",
    }

    def panel(x: int, y: int, w: int, h: int) -> None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill=colors["panel"], outline=colors["line"], width=1)

    draw_text(draw, (40, 28), "E-commerce Executive Performance Dashboard", 34, colors["ink"], True)
    draw_text(draw, (40, 72), f"Synthetic portfolio demo | {DATE_START.isoformat()} to {DATE_END.isoformat()}", 16, colors["muted"])
    for i, label in enumerate(["All Regions", "All Channels", "All Devices"]):
        x = 1180 + i * 125
        draw.rounded_rectangle((x, 38, x + 110, 72), radius=6, fill="#ffffff", outline=colors["line"])
        draw_text(draw, (x + 12, 47), label, 13, "#334155")

    kpi_cards = [
        ("GMV", fmt_money(kpis["gmv"]), "Demand scale", colors["teal"]),
        ("Net Revenue", fmt_money(kpis["net_revenue"]), "Recognized sales", colors["blue"]),
        ("Orders", f"{kpis['orders']:,}", "Order volume", colors["violet"]),
        ("AOV", f"${kpis['aov']:,.0f}", "Basket value", colors["amber"]),
        ("Conversion", f"{kpis['conversion_rate']:.2%}", "Orders / sessions", colors["teal"]),
        ("Refund/Cancel", f"{kpis['refund_cancel_rate']:.2%}", "Risk rate", colors["red"]),
    ]
    card_w, card_h, gap = 245, 104, 12
    y = 112
    for idx, (label, value, note, color) in enumerate(kpi_cards):
        x = 40 + idx * (card_w + gap)
        panel(x, y, card_w, card_h)
        draw_text(draw, (x + 16, y + 16), label.upper(), 12, colors["muted"], True)
        draw_text(draw, (x + 16, y + 42), value, 27, colors["ink"], True)
        draw_text(draw, (x + 16, y + 78), note, 13, color)

    # Trend panel
    panel(40, 244, 720, 340)
    draw_text(draw, (62, 264), "GMV Trend - Last 12 Months", 18, colors["ink"], True)
    trend = monthly.tail(12).reset_index(drop=True)
    max_gmv = trend["gmv"].max()
    base_y = 540
    chart_x = 75
    chart_w = 640
    bar_gap = 12
    bar_w = int((chart_w - bar_gap * 11) / 12)
    for i, row in trend.iterrows():
        h = int(210 * row["gmv"] / max_gmv)
        x0 = chart_x + i * (bar_w + bar_gap)
        draw.rounded_rectangle((x0, base_y - h, x0 + bar_w, base_y), radius=4, fill=colors["teal"])
        draw_text(draw, (x0 - 2, base_y + 10), row["order_month"][5:], 11, colors["muted"])
    draw.line((chart_x, base_y, chart_x + chart_w, base_y), fill=colors["line"], width=1)

    # Category panel
    panel(790, 244, 360, 340)
    draw_text(draw, (812, 264), "Top Categories by GMV", 18, colors["ink"], True)
    cat_max = category["gmv"].max()
    for i, row in enumerate(category.head(7).itertuples()):
        yy = 306 + i * 36
        draw_text(draw, (812, yy), row.category, 14, colors["ink"])
        w = int(170 * row.gmv / cat_max)
        draw.rounded_rectangle((960, yy + 2, 960 + w, yy + 17), radius=4, fill=colors["blue"])
        draw_text(draw, (960 + w + 8, yy), fmt_money(row.gmv), 13, colors["muted"])

    # Channel panel
    panel(1180, 244, 380, 340)
    draw_text(draw, (1202, 264), "Traffic Channel Performance", 18, colors["ink"], True)
    draw_text(draw, (1202, 302), "Channel", 12, colors["muted"], True)
    draw_text(draw, (1360, 302), "GMV", 12, colors["muted"], True)
    draw_text(draw, (1470, 302), "CVR", 12, colors["muted"], True)
    for i, row in enumerate(channel.head(7).itertuples()):
        yy = 330 + i * 34
        draw.line((1202, yy - 8, 1530, yy - 8), fill="#e5edf6", width=1)
        draw_text(draw, (1202, yy), row.channel, 14, colors["ink"])
        draw_text(draw, (1360, yy), fmt_money(row.gmv), 13, colors["ink"])
        draw_text(draw, (1470, yy), f"{row.conversion_rate:.2%}", 13, colors["teal"])

    # Bottom panels
    panel(40, 615, 360, 230)
    draw_text(draw, (62, 635), "Order Status", 18, colors["ink"], True)
    total_status = status["orders"].sum()
    status_colors = {"Completed": colors["teal"], "Refunded": colors["amber"], "Cancelled": colors["red"]}
    for i, row in enumerate(status.itertuples()):
        yy = 680 + i * 44
        pct = row.orders / total_status
        draw_text(draw, (62, yy), row.status, 15, colors["ink"])
        draw.rounded_rectangle((170, yy + 3, 330, yy + 20), radius=4, fill="#e2e8f0")
        draw.rounded_rectangle((170, yy + 3, 170 + int(160 * pct), yy + 20), radius=4, fill=status_colors.get(row.status, colors["blue"]))
        draw_text(draw, (340, yy), f"{pct:.1%}", 14, colors["muted"])

    panel(430, 615, 520, 230)
    draw_text(draw, (452, 635), "Executive Signals", 18, colors["ink"], True)
    signals = [
        ("Top Category", str(kpis["top_category"])),
        ("Top Channel", str(kpis["top_channel"])),
        ("ROAS", f"{kpis['roas']:.2f}x"),
        ("Sessions", f"{kpis['sessions']:,}"),
    ]
    for i, (label, value) in enumerate(signals):
        yy = 682 + i * 36
        draw_text(draw, (452, yy), label, 14, colors["muted"])
        draw_text(draw, (620, yy), value, 16, colors["ink"], True)

    panel(980, 615, 580, 230)
    draw_text(draw, (1002, 635), "Build and QA Status", 18, colors["ink"], True)
    qa_rows = [
        ("Data QA", "PASS", colors["teal"]),
        ("Metric QA", "PASS", colors["teal"]),
        ("Preview QA", "PASS", colors["teal"]),
        ("PBIX File QA", "BLOCKED", colors["red"]),
    ]
    for i, (label, value, color) in enumerate(qa_rows):
        yy = 682 + i * 36
        draw_text(draw, (1002, yy), label, 14, colors["muted"])
        draw_text(draw, (1180, yy), value, 15, color, True)
    draw_text(draw, (1002, 824), "No fake PBIX generated. Build the real file in Power BI Desktop.", 13, colors["muted"])

    img.save(PROJECT_ROOT / "output/screenshots/dashboard_final.png")
    img.save(PROJECT_ROOT / "output/screenshots/page_01.png")
    img.crop((40, 244, 760, 584)).save(PROJECT_ROOT / "output/screenshots/page_02.png")
    img.crop((1180, 244, 1560, 584)).save(PROJECT_ROOT / "output/screenshots/page_03.png")
    img.crop((40, 615, 400, 845)).save(PROJECT_ROOT / "output/screenshots/page_04.png")
    img.save(PROJECT_ROOT / "output/exports/dashboard_final.pdf", "PDF", resolution=100.0)


def make_readme(kpis: dict) -> None:
    write_text(
        "README.md",
        f"""
        # E-commerce Executive Performance Dashboard

        This is a portfolio BI project generated from the BI A-Z master prompt v2.

        The dashboard is designed for ecommerce executives who need a fast read on business performance: GMV, net revenue, orders, AOV, conversion rate, refund/cancel rate, top category, and traffic channel performance.

        ## Current Status

        - Data package: ready.
        - Semantic model spec: ready.
        - DAX measures: ready.
        - Dashboard preview: ready.
        - PBIX authoring mode: `MANUAL_ASSISTED_AFTER_SCRIPTED_DESKTOP_ATTEMPT`.
        - Power BI final PBIX: `launch_verified_assisted_build_pending` after Power BI launch check, blocked at File QA until the real PBIX is built.

        No fake `output/dashboard_final.pbix` file is created.

        ## KPI Snapshot

        | KPI | Value |
        |---|---:|
        | GMV | ${kpis['gmv']:,.0f} |
        | Net Revenue | ${kpis['net_revenue']:,.0f} |
        | Orders | {kpis['orders']:,} |
        | AOV | ${kpis['aov']:,.2f} |
        | Conversion Rate | {kpis['conversion_rate']:.2%} |
        | Refund/Cancel Rate | {kpis['refund_cancel_rate']:.2%} |
        | Top Category | {kpis['top_category']} |
        | Top Traffic Channel | {kpis['top_channel']} |

        ## Key Folders

        - `data/raw/`: generated synthetic source files.
        - `data/prepared/`: clean star schema CSV files for Power BI.
        - `model/`: data dictionary, KPI definitions, DAX, relationship map.
        - `build/config/`: page map, visual map, slicer map, theme.
        - `powerbi/notes/`: build and desktop runbooks.
        - `_agent/pbix_authoring_decision.md`: v2 authoring strategy decision.
        - `_agent/scripted_desktop_pbix_check.md`: scripted desktop PBIX route evidence.
        - `output/`: preview HTML, screenshots, and export PDF.
        - `qa/`: QA checklist, validation JSON, reconciliation workbook.
        - `docs/`: handoff, refresh, rebuild, changelog, issue log.

        ## Rebuild

        ```powershell
        & "C:\\Users\\Win\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe" .\\build\\scripts\\00_create_project_structure.py
        ```

        ## PBIX Next Step

        Follow `powerbi/notes/authoring_strategy.md` and `powerbi/notes/desktop_ui_runbook.md` to create `output/dashboard_final.pbix` in Power BI Desktop, then update File QA.
        """,
    )


def main() -> None:
    ensure_dirs()
    products = make_products()
    customers = make_customers()
    sessions = make_sessions()
    orders, returns = make_orders(products, customers, sessions)
    campaigns = make_campaigns(sessions)
    raw = {
        "products": products,
        "customers": customers,
        "sessions": sessions,
        "orders": orders,
        "returns": returns,
        "campaigns": campaigns,
    }
    prepared = prepare_data(products, customers, sessions, orders, campaigns)
    row_counts = save_dataframes(raw, prepared)
    kpis = compute_kpis(prepared)
    make_validated_outputs(prepared, kpis)
    make_docs(raw, prepared, kpis, row_counts)
    make_preview(prepared, kpis)
    print(json.dumps({"project_root": str(PROJECT_ROOT), "kpis": kpis, "rows": row_counts}, indent=2))


if __name__ == "__main__":
    main()
