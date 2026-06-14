from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREPARED = PROJECT_ROOT / "data" / "prepared"
OUT = PROJECT_ROOT / "data" / "powerbi_template_compat"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dim_date = pd.read_csv(PREPARED / "dim_date.csv")
    dim_product = pd.read_csv(PREPARED / "dim_product.csv")
    dim_channel = pd.read_csv(PREPARED / "dim_channel.csv")
    dim_device = pd.read_csv(PREPARED / "dim_device.csv")
    sessions = pd.read_csv(PREPARED / "fact_sessions.csv")
    orders = pd.read_csv(PREPARED / "fact_orders.csv")
    spend = pd.read_csv(PREPARED / "fact_marketing_spend.csv")

    product_lookup = dim_product.set_index("product_key").to_dict(orient="index")
    channel_lookup = dim_channel.set_index("channel_key").to_dict(orient="index")
    device_lookup = dim_device.set_index("device_key").to_dict(orient="index")

    compat_date = dim_date[
        ["date", "year", "quarter", "month_number", "month_name", "year_month", "week_start", "day_of_week", "is_weekend"]
    ].copy()

    compat_product = dim_product.rename(
        columns={
            "product_key": "product_id",
            "product": "product_name",
            "unit_price": "base_price",
        }
    )[["product_id", "product_name", "category", "subcategory", "brand", "base_price", "launch_date"]].copy()
    compat_product["unit_cost"] = (compat_product["base_price"] * 0.58).round(2)
    compat_product["active_flag"] = 1

    users = (
        sessions[["user_id", "region", "new_returning"]]
        .drop_duplicates("user_id")
        .rename(columns={"user_id": "customer_id", "new_returning": "customer_segment"})
    )
    users["signup_date"] = "2024-01-01"
    users["country"] = "United States"
    users["marketing_opt_in"] = 1

    regions = pd.DataFrame({"region": sorted(sessions["region"].dropna().unique())})
    regions["country"] = "United States"

    compat_channel = dim_channel.rename(columns={"channel_group": "channel_type"})[
        ["channel", "channel_type"]
    ].copy()
    compat_channel["default_conversion_rate"] = 0.10

    compat_device = dim_device[["device"]].copy()

    order_rows = []
    for idx, row in orders.reset_index(drop=True).iterrows():
        product = product_lookup[row["product_key"]]
        channel = channel_lookup[row["channel_key"]]["channel"]
        device = device_lookup[row["device_key"]]["device"]
        status = row["order_status"]
        gmv = float(row["gross_revenue"])
        net_revenue = float(row["net_revenue"])
        contribution_margin = net_revenue * float(product.get("gross_margin_rate", 0.42))
        order_rows.append(
            {
                "order_key": idx + 1,
                "order_id": row["order_id"],
                "order_date": row["order_date"],
                "customer_id": row["user_id"],
                "product_id": row["product_key"],
                "category": product["category"],
                "subcategory": product["subcategory"],
                "region": row["region"],
                "channel": channel,
                "device": device,
                "customer_segment": "Returning",
                "customer_home_region": row["region"],
                "status": status,
                "quantity": int(row["quantity"]),
                "unit_price": round(float(row["unit_price"]), 2),
                "discount_amount": round(float(row["discount_amount"]), 2),
                "shipping_fee": 0.0,
                "tax_amount": 0.0,
                "gmv": round(gmv, 2),
                "net_revenue": round(net_revenue, 2),
                "refund_amount": round(float(row["refund_amount"]), 2),
                "contribution_margin": round(contribution_margin, 2),
                "payment_method": "Card",
                "is_first_order": 0,
                "order_month": pd.to_datetime(row["order_date"]).strftime("%Y-%m"),
                "completed_order_flag": 1 if status == "Completed" else 0,
                "refund_order_flag": 1 if status == "Refunded" else 0,
                "cancel_order_flag": 0,
            }
        )
    compat_orders = pd.DataFrame(order_rows)

    session_joined = sessions.copy()
    session_joined["channel"] = session_joined["channel_key"].map(lambda key: channel_lookup[key]["channel"])
    session_joined["device"] = session_joined["device_key"].map(lambda key: device_lookup[key]["device"])
    compat_sessions = (
        session_joined.groupby(["session_date", "channel", "device", "region", "session_month"], as_index=False)
        .agg(
            sessions=("session_id", "nunique"),
            visitors=("user_id", "nunique"),
            add_to_cart=("add_to_cart_flag", "sum"),
            checkout_starts=("checkout_flag", "sum"),
        )
        .sort_values(["session_date", "channel", "device", "region"])
    )
    compat_sessions.insert(0, "session_key", range(1, len(compat_sessions) + 1))

    spend_joined = spend.copy()
    spend_joined["channel"] = spend_joined["channel_key"].map(lambda key: channel_lookup[key]["channel"])
    spend_joined["month"] = pd.to_datetime(spend_joined["date"]).dt.strftime("%Y-%m")
    compat_spend = (
        spend_joined.groupby(["month", "channel"], as_index=False)
        .agg(spend=("spend", "sum"), impressions=("impressions", "sum"), clicks=("clicks", "sum"))
        .sort_values(["month", "channel"])
    )

    outputs = {
        "dim_date.csv": compat_date,
        "dim_product.csv": compat_product,
        "dim_customer.csv": users,
        "dim_region.csv": regions,
        "dim_channel.csv": compat_channel,
        "dim_device.csv": compat_device,
        "fact_orders.csv": compat_orders,
        "fact_sessions.csv": compat_sessions,
        "fact_marketing_spend.csv": compat_spend,
    }
    for name, frame in outputs.items():
        frame.to_csv(OUT / name, index=False, encoding="utf-8-sig")

    print(
        {
            "status": "compat_csvs_created",
            "folder": str(OUT),
            "tables": {name: len(frame) for name, frame in outputs.items()},
        }
    )


if __name__ == "__main__":
    main()
