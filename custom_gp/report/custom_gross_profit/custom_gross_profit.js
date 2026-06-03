frappe.query_reports["Custom Gross Profit"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.get_today(),
        },
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
        },
        {
            fieldname: "customer",
            label: __("Customer"),
            fieldtype: "Link",
            options: "Customer",
        },
        {
            fieldname: "item_code",
            label: __("Item"),
            fieldtype: "Link",
            options: "Item",
        },
        {
            fieldname: "territory",
            label: __("Territory"),
            fieldtype: "Link",
            options: "Territory",
        },
        {
            fieldname: "warehouse",
            label: __("Warehouse"),
            fieldtype: "Link",
            options: "Warehouse",
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (!data) return value;

        if (column.fieldname === "gross_profit_percent") {
            var pct = parseFloat(data.gross_profit_percent) || 0;
            var color = pct >= 20 ? "green" : pct >= 10 ? "orange" : "red";
            value = "<span style='color:" + color + ";font-weight:bold'>" + value + "</span>";
        }
        if (data.is_return === "Yes") {
            value = "<span style='color:#d9534f'>" + value + "</span>";
        }
        return value;
    },

    onload: function (report) {
        report.page.add_action_item(__("Print PDF"), function () {
            _cgp_print(report);
        });
    },
};

/* ─── Unique prefix: _cgp_ (Custom Gross Profit) ─── */

function _cgp_print(report) {
    var f = report.get_values ? report.get_values() : {};
    if (!f.from_date || !f.to_date) {
        frappe.msgprint(__("Please set From Date and To Date."));
        return;
    }
    frappe.call({
        method: "custom_gp.custom_gp.report.custom_gross_profit.custom_gross_profit.get_report_data",
        args: {
            from_date:  f.from_date,
            to_date:    f.to_date,
            company:    f.company    || null,
            customer:   f.customer   || null,
            item_code:  f.item_code  || null,
            territory:  f.territory  || null,
            warehouse:  f.warehouse  || null,
        },
        freeze: true,
        freeze_message: __("Generating report…"),
        callback: function (r) {
            if (!r.message || !r.message.data || !r.message.data.length) {
                frappe.msgprint(__("No data found for selected filters."));
                return;
            }
            var win = window.open("", "_blank", "width=1200,height=860,scrollbars=yes");
            win.document.open();
            win.document.write(_cgp_build_html(r.message, f));
            win.document.close();
        },
    });
}

function _cgp_esc(s) {
    if (!s) return "";
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function _cgp_cur(v) {
    v = parseFloat(v) || 0;
    return v.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function _cgp_pct(v) {
    return (parseFloat(v) || 0).toFixed(2) + "%";
}

function _cgp_build_html(msg, f) {
    var rows = msg.data;
    var summary = msg.summary || [];

    /* Summary values */
    var sumMap = {};
    (summary || []).forEach(function (s) { sumMap[s.label] = s.value; });

    /* Table rows */
    var tbody = "";
    rows.forEach(function (d) {
        var rowColor = d.is_return === "Yes" ? "#fff5f5" : "";
        tbody += "<tr style='background:" + rowColor + "'>"
            + "<td>" + _cgp_esc(d.invoice)              + "</td>"
            + "<td>" + _cgp_esc(d.posting_date)         + "</td>"
            + "<td>" + _cgp_esc(d.customer)             + "</td>"
            + "<td>" + _cgp_esc(d.customer_group)       + "</td>"
            + "<td>" + _cgp_esc(d.sales_person)         + "</td>"
            + "<td>" + _cgp_esc(d.item_code)            + "</td>"
            + "<td>" + _cgp_esc(d.item_name)            + "</td>"
            + "<td>" + _cgp_esc(d.item_group)           + "</td>"
            + "<td>" + _cgp_esc(d.warehouse)            + "</td>"
            + "<td style='text-align:right'>" + _cgp_esc(d.qty)    + "</td>"
            + "<td style='text-align:right'>" + _cgp_cur(d.base_amount)   + "</td>"
            + "<td style='text-align:right'>" + _cgp_cur(d.item_discount) + "</td>"
            + "<td style='text-align:right'>" + _cgp_cur(d.net_sales)     + "</td>"
            + "<td style='text-align:right'>" + _cgp_cur(d.buying_amount) + "</td>"
            + "<td style='text-align:right'>" + _cgp_cur(d.gross_profit)  + "</td>"
            + "<td style='text-align:right'>" + _cgp_pct(d.gross_profit_percent) + "</td>"
            + "<td>" + (d.is_return === "Yes" ? "↩ Return" : "") + "</td>"
            + "</tr>";
    });

    return "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        + "<title>Custom Gross Profit</title>"
        + "<style>"
        + "body{font-family:Arial,sans-serif;font-size:12px;margin:20px}"
        + "h2{text-align:center;margin-bottom:4px}"
        + ".period{text-align:center;color:#555;margin-bottom:12px}"
        + ".summary{display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap}"
        + ".scard{border:1px solid #ddd;border-radius:6px;padding:10px 20px;min-width:140px}"
        + ".scard .lbl{font-size:11px;color:#888}"
        + ".scard .val{font-size:16px;font-weight:bold;color:#333}"
        + "table{width:100%;border-collapse:collapse}"
        + "th{background:#3d6b8c;color:#fff;padding:6px 8px;text-align:left;font-size:11px}"
        + "td{padding:5px 8px;border-bottom:1px solid #eee;font-size:11px}"
        + "tr:hover{background:#f0f4f8}"
        + "@media print{.no-print{display:none}}"
        + "</style></head><body>"
        + "<h2>Custom Gross Profit Report</h2>"
        + "<div class='period'>Period: " + _cgp_esc(f.from_date) + " to " + _cgp_esc(f.to_date)
        + (f.company ? " &nbsp;|&nbsp; " + _cgp_esc(f.company) : "") + "</div>"
        + "<div class='summary'>"
        + _cgp_scard("Total Sales",  sumMap["Total Sales"])
        + _cgp_scard("Total COGS",   sumMap["Total COGS"])
        + _cgp_scard("Gross Profit", sumMap["Gross Profit"])
        + _cgp_scard("GP Margin %",  sumMap["GP Margin %"])
        + "</div>"
        + "<table><thead><tr>"
        + "<th>Invoice</th><th>Date</th><th>Customer</th><th>Customer Group</th>"
        + "<th>Sales Person</th><th>Item Code</th><th>Item Name</th><th>Item Group</th>"
        + "<th>Warehouse</th><th>Qty</th><th>Sales Amt</th><th>Discount</th>"
        + "<th>Net Sales</th><th>COGS</th><th>GP</th><th>GP%</th><th>Return</th>"
        + "</tr></thead><tbody>" + tbody + "</tbody></table>"
        + "</body></html>";
}

function _cgp_scard(label, value) {
    return "<div class='scard'>"
        + "<div class='lbl'>" + label + "</div>"
        + "<div class='val'>" + (value !== undefined ? value : "—") + "</div>"
        + "</div>";
}
