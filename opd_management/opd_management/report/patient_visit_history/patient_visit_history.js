frappe.query_reports["Patient Visit History"] = {
	"filters": [
		{
			"fieldname": "patient",
			"label": __("Patient"),
			"fieldtype": "Link",
			"options": "Patient"
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "doctor",
			"label": __("Doctor"),
			"fieldtype": "Link",
			"options": "Doctor"
		}
	]
};
