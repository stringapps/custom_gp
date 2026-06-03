app_name = "custom_gp"
app_title = "Custom Gp"
app_publisher = "String IT"
app_description = "Custom Gross Profit Report for ERPNext"
app_email = "admin@stringit.pro"
app_license = "MIT"

# Fixtures — imported during bench migrate
fixtures = [
    {
        "doctype": "Report",
        "filters": [["name", "in", ["Custom Gross Profit"]]]
    },
    {
        "doctype": "Workspace",
        "filters": [["name", "in", ["Custom Gp"]]]
    },
]
