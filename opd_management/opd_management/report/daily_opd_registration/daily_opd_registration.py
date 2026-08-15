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
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 110},
		{"label": _("Token No"), "fieldname": "token_no", "fieldtype": "Int", "width": 90},
		{"label": _("OPD Form"), "fieldname": "name", "fieldtype": "Link", "options": "OPD Form", "width": 140},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 160},
		{"label": _("Gender"), "fieldname": "gender", "fieldtype": "Data", "width": 90},
		{"label": _("Phone No"), "fieldname": "phone_no", "fieldtype": "Data", "width": 120},
		{"label": _("Doctor"), "fieldname": "doctor", "fieldtype": "Link", "options": "Doctor", "width": 160},
		{"label": _("Doctor Session"), "fieldname": "doctor_session", "fieldtype": "Data", "width": 260},
		{"label": _("Checkup Fee"), "fieldname": "checkup_fee", "fieldtype": "Currency", "width": 120},
		{"label": _("Hospital/Clinic"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 140},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Link", "options": "Sales Invoice", "width": 140},
		{"label": _("Invoice Status"), "fieldname": "invoice_status", "fieldtype": "Data", "width": 130}
	]

def get_data(filters):
	conditions = ["docstatus = 1"]
	values = {}

	if filters.get("date"):
		conditions.append("date = %(date)s")
		values["date"] = filters.get("date")

	if filters.get("doctor"):
		conditions.append("doctor = %(doctor)s")
		values["doctor"] = filters.get("doctor")

	if filters.get("doctor_session"):
		conditions.append("doctor_session = %(doctor_session)s")
		values["doctor_session"] = filters.get("doctor_session")

	if filters.get("status"):
		conditions.append("status = %(status)s")
		values["status"] = filters.get("status")

	if filters.get("company"):
		conditions.append("company = %(company)s")
		values["company"] = filters.get("company")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			date,
			token_no,
			name,
			patient_name,
			gender,
			phone_no,
			doctor,
			doctor_session,
			session_name,
			from_time,
			to_time,
			checkup_fee,
			company,
			status,
			sales_invoice
		FROM `tabOPD Form`
		WHERE {where_clause}
		ORDER BY date DESC, token_no DESC, creation DESC
	"""

	data = frappe.db.sql(query, values, as_dict=True)

	for d in data:
		s_name = d.get("session_name")
		f_time = str(d.get("from_time")) if d.get("from_time") else ""
		t_time = str(d.get("to_time")) if d.get("to_time") else ""

		if not s_name and d.get("doctor_session"):
			sess_doc = frappe.db.get_value("Doctor Session", d.get("doctor_session"), ["session_name", "from_time", "to_time"], as_dict=True)
			if sess_doc:
				s_name = sess_doc.session_name
				f_time = str(sess_doc.from_time) if sess_doc.from_time else ""
				t_time = str(sess_doc.to_time) if sess_doc.to_time else ""

		if s_name:
			if f_time and t_time:
				d["doctor_session"] = f"Session: {s_name} ({f_time} - {t_time})"
			else:
				d["doctor_session"] = f"Session: {s_name}"

		if d.get("sales_invoice"):
			inv_status = frappe.db.get_value("Sales Invoice", d.get("sales_invoice"), "status")
			d["invoice_status"] = inv_status or _("Draft")
		else:
			d["invoice_status"] = _("Not Generated")

	return data

def get_report_summary(data):
	total_registered = len(data)
	waiting_count = sum(1 for d in data if d.get("status") == "Waiting")
	in_consultation_count = sum(1 for d in data if d.get("status") == "In Consultation")
	completed_count = sum(1 for d in data if d.get("status") == "Completed")
	total_revenue = sum(d.get("checkup_fee") or 0 for d in data)

	return [
		{
			"value": total_registered,
			"indicator": "Blue",
			"label": _("Total Registered Patients"),
			"datatype": "Int"
		},
		{
			"value": waiting_count,
			"indicator": "Orange",
			"label": _("Waiting Patients"),
			"datatype": "Int"
		},
		{
			"value": in_consultation_count,
			"indicator": "Cyan",
			"label": _("In Consultation"),
			"datatype": "Int"
		},
		{
			"value": completed_count,
			"indicator": "Green",
			"label": _("Completed Consultations"),
			"datatype": "Int"
		},
		{
			"value": total_revenue,
			"indicator": "Green",
			"label": _("Total OPD Revenue"),
			"datatype": "Currency"
		}
	]

def get_chart(data):
	waiting_count = sum(1 for d in data if d.get("status") == "Waiting")
	in_consultation_count = sum(1 for d in data if d.get("status") == "In Consultation")
	completed_count = sum(1 for d in data if d.get("status") == "Completed")

	return {
		"data": {
			"labels": [_("Waiting"), _("In Consultation"), _("Completed")],
			"datasets": [
				{
					"name": _("Patients"),
					"values": [waiting_count, in_consultation_count, completed_count]
				}
			]
		},
		"type": "donut",
		"height": 280,
		"colors": ["#ed8936", "#00b5d8", "#38a169"]
	}
