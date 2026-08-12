import frappe
from frappe import _

def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	report_summary = get_report_summary(data)
	chart = get_chart(data)
	return columns, data, None, chart, report_summary

def get_columns():
	return [
		{"label": _("Doctor"), "fieldname": "doctor_name", "fieldtype": "Data", "width": 180},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 160},
		{"label": _("Total Patients"), "fieldname": "total_patients", "fieldtype": "Int", "width": 120},
		{"label": _("Waiting"), "fieldname": "waiting_count", "fieldtype": "Int", "width": 110},
		{"label": _("In Consultation"), "fieldname": "in_consultation_count", "fieldtype": "Int", "width": 130},
		{"label": _("Completed"), "fieldname": "completed_count", "fieldtype": "Int", "width": 110},
		{"label": _("Total Fees"), "fieldname": "total_fees", "fieldtype": "Currency", "width": 140}
	]

def get_data(filters):
	conditions = ["o.docstatus = 1"]
	values = {}

	if filters.get("from_date"):
		conditions.append("o.date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("o.date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("doctor"):
		conditions.append("o.doctor = %(doctor)s")
		values["doctor"] = filters.get("doctor")

	if filters.get("company"):
		conditions.append("o.company = %(company)s")
		values["company"] = filters.get("company")

	if filters.get("department"):
		conditions.append("d.department = %(department)s")
		values["department"] = filters.get("department")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			COALESCE(d.doctor_name, o.doctor) AS doctor_name,
			d.department,
			COUNT(o.name) AS total_patients,
			SUM(CASE WHEN o.status = 'Waiting' THEN 1 ELSE 0 END) AS waiting_count,
			SUM(CASE WHEN o.status = 'In Consultation' THEN 1 ELSE 0 END) AS in_consultation_count,
			SUM(CASE WHEN o.status = 'Completed' THEN 1 ELSE 0 END) AS completed_count,
			SUM(o.checkup_fee) AS total_fees
		FROM `tabOPD Form` o
		LEFT JOIN `tabDoctor` d ON d.name = o.doctor
		WHERE {where_clause}
		GROUP BY o.doctor
		ORDER BY total_patients DESC, total_fees DESC
	"""

	return frappe.db.sql(query, values, as_dict=True)

def get_report_summary(data):
	doctor_count = len(data)
	total_patients = sum(d.get("total_patients") or 0 for d in data)
	completed_count = sum(d.get("completed_count") or 0 for d in data)
	total_fees = sum(d.get("total_fees") or 0 for d in data)

	return [
		{
			"value": doctor_count,
			"indicator": "Blue",
			"label": _("Active Doctors"),
			"datatype": "Int"
		},
		{
			"value": total_patients,
			"indicator": "Purple",
			"label": _("Total OPD Patients"),
			"datatype": "Int"
		},
		{
			"value": completed_count,
			"indicator": "Green",
			"label": _("Completed Consultations"),
			"datatype": "Int"
		},
		{
			"value": total_fees,
			"indicator": "Green",
			"label": _("Total Consultation Revenue"),
			"datatype": "Currency"
		}
	]

def get_chart(data):
	labels = [d.get("doctor_name") for d in data[:10]]
	patient_counts = [d.get("total_patients") for d in data[:10]]
	revenue = [d.get("total_fees") for d in data[:10]]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{
					"name": _("Total Patients"),
					"values": patient_counts
				},
				{
					"name": _("Total Revenue (PKR)"),
					"values": revenue
				}
			]
		},
		"type": "bar",
		"height": 300,
		"colors": ["#3182ce", "#38a169"]
	}
