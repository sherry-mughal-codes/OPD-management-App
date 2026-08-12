frappe.query_reports["Daily OPD Registration"] = {
	"filters": [
		{
			"fieldname": "date",
			"label": __("Date"),
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
			"fieldname": "doctor_session",
			"label": __("Doctor Session"),
			"fieldtype": "Link",
			"options": "Doctor Session"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nWaiting\nIn Consultation\nCompleted"
		},
		{
			"fieldname": "company",
			"label": __("Hospital/Clinic"),
			"fieldtype": "Link",
			"options": "Company"
		}
	]
};
