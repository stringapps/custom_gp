import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    if not filters:
        filters = {}
    columns = _get_columns()
    data = _get_data(filters)
    summary = _make_summary(data)
    return columns, data, None, None, summary


def _get_columns():
    return [
        {"label": _("Invoice"),          "fieldname": "invoice",              "fieldtype": "Link",     "options": "Sales Invoice", "width": 160},
        {"label": _("Date"),             "fieldname": "posting_date",         "fieldtype": "Date",                                 "width": 95},
        {"label": _("Customer"),         "fieldname": "customer",             "fieldtype": "Link",     "options": "Customer",      "width": 150},
        {"label": _("Customer Group"),   "fieldname": "customer_group",       "fieldtype": "Link",     "options": "Customer Group","width": 130},
        {"label": _("Territory"),        "fieldname": "territory",            "fieldtype": "Link",     "options": "Territory",     "width": 110},
        {"label": _("Sales Person"),     "fieldname": "sales_person",         "fieldtype": "Data",                                 "width": 130},
        {"label": _("Owner"),            "fieldname": "owner",                "fieldtype": "Data",                                 "width": 110},
        {"label": _("Return?"),          "fieldname": "is_return",            "fieldtype": "Data",                                 "width": 65},
        {"label": _("Return Against"),   "fieldname": "return_against",       "fieldtype": "Link",     "options": "Sales Invoice", "width": 160},
        {"label": _("Item Code"),        "fieldname": "item_code",            "fieldtype": "Link",     "options": "Item",          "width": 140},
        {"label": _("Item Name"),        "fieldname": "item_name",            "fieldtype": "Data",                                 "width": 180},
        {"label": _("Item Group"),       "fieldname": "item_group",           "fieldtype": "Link",     "options": "Item Group",    "width": 120},
        {"label": _("Brand"),            "fieldname": "brand",                "fieldtype": "Link",     "options": "Brand",         "width": 100},
        {"label": _("Warehouse"),        "fieldname": "warehouse",            "fieldtype": "Link",     "options": "Warehouse",     "width": 140},
        {"label": _("UOM"),              "fieldname": "uom",                  "fieldtype": "Link",     "options": "UOM",           "width": 70},
        {"label": _("Qty"),              "fieldname": "qty",                  "fieldtype": "Float",                                "width": 80},
        {"label": _("Price List Rate"),  "fieldname": "price_list_rate",      "fieldtype": "Currency",                             "width": 120},
        {"label": _("Rate"),             "fieldname": "rate",                 "fieldtype": "Currency",                             "width": 100},
        {"label": _("Sales Amount"),     "fieldname": "base_amount",          "fieldtype": "Currency",                             "width": 120},
        {"label": _("Item Discount"),    "fieldname": "item_discount",        "fieldtype": "Currency",                             "width": 110},
        {"label": _("Net Sales"),        "fieldname": "net_sales",            "fieldtype": "Currency",                             "width": 120},
        {"label": _("COGS"),             "fieldname": "buying_amount",        "fieldtype": "Currency",                             "width": 120},
        {"label": _("Gross Profit"),     "fieldname": "gross_profit",         "fieldtype": "Currency",                             "width": 120},
        {"label": _("GP %"),             "fieldname": "gross_profit_percent", "fieldtype": "Percent",                              "width": 80},
    ]


def _get_data(filters):
    from_date = filters.get("from_date")
    to_date   = filters.get("to_date")
    company   = filters.get("company")
    customer  = filters.get("customer")
    item_code = filters.get("item_code")
    territory = filters.get("territory")
    warehouse = filters.get("warehouse")

    conditions = []
    params = {"from_date": from_date, "to_date": to_date}

    if company:
        conditions.append("si.company = %(company)s")
        params["company"] = company
    if customer:
        conditions.append("si.customer = %(customer)s")
        params["customer"] = customer
    if item_code:
        conditions.append("sii.item_code = %(item_code)s")
        params["item_code"] = item_code
    if territory:
        conditions.append("si.territory = %(territory)s")
        params["territory"] = territory
    if warehouse:
        conditions.append("sii.warehouse = %(warehouse)s")
        params["warehouse"] = warehouse

    where_extra = ("AND " + " AND ".join(conditions)) if conditions else ""

    rows = frappe.db.sql("""
        SELECT
            si.name                         AS invoice,
            si.posting_date                 AS posting_date,
            si.customer,
            si.customer_group,
            si.territory,
            si.owner,
            si.is_return,
            si.return_against,

            (SELECT GROUP_CONCAT(DISTINCT st.sales_person SEPARATOR ', ')
             FROM `tabSales Team` st
             WHERE st.parent = si.name AND st.parenttype = 'Sales Invoice'
            )                               AS sales_person,

            sii.item_code,
            sii.item_name,
            sii.item_group,
            i.brand,
            sii.warehouse,
            sii.uom,

            CASE WHEN si.is_return = 1 THEN -ABS(sii.qty)         ELSE sii.qty         END AS qty,
            sii.price_list_rate,
            sii.rate,
            CASE WHEN si.is_return = 1 THEN -ABS(sii.base_amount)  ELSE sii.base_amount  END AS base_amount,
            CASE WHEN si.is_return = 1 THEN -ABS(sii.discount_amount) ELSE sii.discount_amount END AS item_discount,

            COALESCE((
                SELECT sle.stock_value_difference
                FROM `tabStock Ledger Entry` sle
                WHERE sle.voucher_type       = 'Sales Invoice'
                  AND sle.voucher_no         = si.name
                  AND sle.voucher_detail_no  = sii.name
                  AND sle.item_code          = sii.item_code
                  AND sle.warehouse          = sii.warehouse
                  AND sle.is_cancelled       = 0
                LIMIT 1
            ), 0) AS stock_value_diff

        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN  `tabItem` i                 ON i.name    = sii.item_code
        WHERE si.docstatus = 1
          AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
          {where_extra}
        ORDER BY si.posting_date, si.name, sii.idx
    """.format(where_extra=where_extra), params, as_dict=True)

    data = []
    for row in rows:
        svd = flt(row.stock_value_diff)

        if row.is_return:
            cogs = -abs(svd) if svd else 0
        else:
            cogs = abs(svd) if svd else 0

        net_sales     = flt(row.base_amount) - flt(row.item_discount)
        gross_profit  = net_sales - cogs
        gp_percent    = (gross_profit / net_sales * 100) if net_sales else 0

        data.append({
            "invoice":              row.invoice,
            "posting_date":         row.posting_date,
            "customer":             row.customer,
            "customer_group":       row.customer_group,
            "territory":            row.territory,
            "sales_person":         row.sales_person or "",
            "owner":                row.owner,
            "is_return":            "Yes" if row.is_return else "No",
            "return_against":       row.return_against or "",
            "item_code":            row.item_code,
            "item_name":            row.item_name,
            "item_group":           row.item_group,
            "brand":                row.brand or "",
            "warehouse":            row.warehouse,
            "uom":                  row.uom,
            "qty":                  flt(row.qty, 3),
            "price_list_rate":      flt(row.price_list_rate, 2),
            "rate":                 flt(row.rate, 2),
            "base_amount":          flt(row.base_amount, 2),
            "item_discount":        flt(row.item_discount, 2),
            "net_sales":            flt(net_sales, 2),
            "buying_amount":        flt(cogs, 2),
            "gross_profit":         flt(gross_profit, 2),
            "gross_profit_percent": flt(gp_percent, 2),
        })

    return data


def _make_summary(data):
    total_sales = sum(flt(d.get("net_sales"))    for d in data)
    total_cogs  = sum(flt(d.get("buying_amount")) for d in data)
    total_gp    = sum(flt(d.get("gross_profit"))  for d in data)
    gp_pct      = (total_gp / total_sales * 100) if total_sales else 0

    return [
        {"label": _("Total Sales"),  "value": flt(total_sales, 2), "indicator": "Blue"},
        {"label": _("Total COGS"),   "value": flt(total_cogs, 2),  "indicator": "Red"},
        {"label": _("Gross Profit"), "value": flt(total_gp, 2),    "indicator": "Green"},
        {"label": _("GP Margin %"),  "value": "{:.2f}%".format(gp_pct),
         "indicator": "Green" if gp_pct > 0 else "Red"},
    ]


@frappe.whitelist()
def get_report_data(from_date, to_date, company=None, customer=None,
                    item_code=None, territory=None, warehouse=None):
    """Whitelisted API — called by JS Print PDF button."""
    filters = {
        "from_date": from_date,
        "to_date":   to_date,
        "company":   company,
        "customer":  customer,
        "item_code": item_code,
        "territory": territory,
        "warehouse": warehouse,
    }
    data    = _get_data(filters)
    summary = _make_summary(data)
    return {"data": data, "summary": summary}
