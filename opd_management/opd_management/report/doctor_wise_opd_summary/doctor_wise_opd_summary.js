frappe.query_reports["Doctor-wise OPD Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "doctor",
			"label": __("Doctor"),
			"fieldtype": "Link",
			"options": "Doctor"
		},
		{
			"fieldname": "department",
			"label": __("Department"),
			"fieldtype": "Link",
			"options": "Department"
		},
		{
			"fieldname": "company",
			"label": __("Hospital/Clinic"),
			"fieldtype": "Link",
			"options": "Company"
		}
	]
};
