# Custom GP — ERPNext v15

Custom Gross Profit Script Report for ERPNext **v15**.

## Reports included

| Report Name | Ref DocType |
|---|---|
| Custom Gross Profit | Sales Invoice |

## Installation

```bash
# From your frappe-bench directory
bench get-app custom_gp /path/to/custom_gp   # or git URL
bench --site [site-name] install-app custom_gp
bench --site [site-name] migrate
bench restart
```

## Git branches

| Branch | ERPNext |
|---|---|
| `main` / `v15` | ERPNext v15 |

For v16 use the **custom_gp_v16** repository.

## Filters

- From Date / To Date (required)
- Company, Customer, Item, Territory, Warehouse (optional)

## Features

- Item-level Gross Profit using exact Stock Ledger COGS
- Returns handled (negative qty/amount)
- Sales Person from Sales Team child table
- Summary bar: Total Sales, COGS, GP, GP%
- Print PDF button
