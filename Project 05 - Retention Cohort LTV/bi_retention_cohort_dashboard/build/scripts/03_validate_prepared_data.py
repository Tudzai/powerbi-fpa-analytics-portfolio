from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
orders_raw = pd.read_csv(ROOT / 'data/raw/orders_raw.csv')
dim_user = pd.read_csv(ROOT / 'data/prepared/DimUser.csv')
fact_orders = pd.read_csv(ROOT / 'data/prepared/FactOrders.csv')
fact_user_month = pd.read_csv(ROOT / 'data/prepared/FactUserMonth.csv')
cohort = pd.read_csv(ROOT / 'data/prepared/CohortRetention.csv')
monthly = pd.read_csv(ROOT / 'data/prepared/MonthlyKPIs.csv')
completed_raw = orders_raw[orders_raw['OrderStatus'] == 'Completed'].merge(dim_user[['UserID']], on='UserID', how='inner')
checks = [
    {'check': 'DimUser user grain unique', 'status': 'pass' if dim_user['UserID'].is_unique else 'fail'},
    {'check': 'FactOrders order grain unique', 'status': 'pass' if fact_orders['OrderID'].is_unique else 'fail'},
    {'check': 'Completed order row count reconciles', 'status': 'pass' if len(completed_raw) == len(fact_orders) else 'fail', 'raw': int(len(completed_raw)), 'prepared': int(len(fact_orders))},
    {'check': 'Completed net revenue reconciles', 'status': 'pass' if abs(round(completed_raw['NetRevenue'].sum(),2)-round(fact_orders['NetRevenue'].sum(),2)) < 0.01 else 'fail', 'raw': round(float(completed_raw['NetRevenue'].sum()),2), 'prepared': round(float(fact_orders['NetRevenue'].sum()),2)},
    {'check': 'FactUserMonth grain unique', 'status': 'pass' if not fact_user_month.duplicated(['UserID','MonthStart']).any() else 'fail'},
    {'check': 'Retention rate bounded', 'status': 'pass' if cohort['RetentionRate'].between(0,1).all() else 'fail'},
    {'check': 'Repeat purchase rate bounded', 'status': 'pass' if monthly['RepeatPurchaseRate'].between(0,1).all() else 'fail'},
]
result = {'status': 'pass' if all(c['status'] == 'pass' for c in checks) else 'fail', 'checks': checks}
(ROOT / 'qa' / 'prepared_data_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
