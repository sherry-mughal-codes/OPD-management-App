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
		{"label": _("Date"), "fieldname": "encounter_date", "fieldtype": "Date", "width": 110},
		{"label": _("Patient Name"), "fieldname": "patient_name", "fieldtype": "Data", "width": 160},
		{"label": _("Doctor"), "fieldname": "doctor_name", "fieldtype": "Data", "width": 160},
		{"label": _("Doctor Session"), "fieldname": "doctor_session", "fieldtype": "Data", "width": 260},
		{"label": _("Token No"), "fieldname": "token_no", "fieldtype": "Int", "width": 90},
		{"label": _("Diagnoses"), "fieldname": "diagnoses", "fieldtype": "Data", "width": 200},
		{"label": _("Medication"), "fieldname": "medication", "fieldtype": "Data", "width": 160},
		{"label": _("Drug Code"), "fieldname": "drug_code", "fieldtype": "Data", "width": 110},
		{"label": _("Dosage"), "fieldname": "dosage", "fieldtype": "Data", "width": 100},
		{"label": _("Period"), "fieldname": "period", "fieldtype": "Data", "width": 110},
		{"label": _("Dosage Form"), "fieldname": "dosage_form", "fieldtype": "Data", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 110}
	]

def get_data(filters):
	conditions = ["e.docstatus = 1"]
	values = {}

	if filters.get("patient"):
		conditions.append("e.patient = %(patient)s")
		values["patient"] = filters.get("patient")

	if filters.get("from_date"):
		conditions.append("e.encounter_date >= %(from_date)s")
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions.append("e.encounter_date <= %(to_date)s")
		values["to_date"] = filters.get("to_date")

	if filters.get("doctor"):
		conditions.append("e.doctor = %(doctor)s")
		values["doctor"] = filters.get("doctor")

	where_clause = " AND ".join(conditions)

	query = f"""
		SELECT
			e.name AS encounter_id,
			e.encounter_date,
			e.patient,
			COALESCE(p.patient_name, e.patient) AS patient_name,
			COALESCE(d.doctor_name, e.doctor) AS doctor_name,
			e.doctor_session,
			o.session_name,
			o.from_time,
			o.to_time,
			o.token_no,
			e.status
		FROM `tabPatient Encounter` e
		LEFT JOIN `tabPatient` p ON p.name = e.patient
		LEFT JOIN `tabDoctor` d ON d.name = e.doctor
		LEFT JOIN `tabOPD Form` o ON o.name = e.opd_form
		WHERE {where_clause}
		ORDER BY e.encounter_date DESC, e.encounter_time DESC, e.creation DESC
	"""

	encounters = frappe.db.sql(query, values, as_dict=True)

	result = []
	for enc in encounters:
		s_name = enc.get("session_name")
		f_time = str(enc.get("from_time")) if enc.get("from_time") else ""
		t_time = str(enc.get("to_time")) if enc.get("to_time") else ""

		if not s_name and enc.get("doctor_session"):
			sess_doc = frappe.db.get_value("Doctor Session", enc.get("doctor_session"), ["session_name", "from_time", "to_time"], as_dict=True)
			if sess_doc:
				s_name = sess_doc.session_name
				f_time = str(sess_doc.from_time) if sess_doc.from_time else ""
				t_time = str(sess_doc.to_time) if sess_doc.to_time else ""

		if s_name:
			if f_time and t_time:
				session_fmt = f"Session: {s_name} ({f_time} - {t_time})"
			else:
				session_fmt = f"Session: {s_name}"
		else:
			session_fmt = enc.get("doctor_session") or ""
		# Diagnoses string
		diagnoses_list = frappe.get_all(
			"Encounter Diagnosis",
			filters={"parent": enc.encounter_id},
			pluck="diagnosis"
		)
		diag_str = ", ".join(diagnoses_list) if diagnoses_list else "-"

		# Prescriptions list
		prescriptions = frappe.get_all(
			"Encounter Prescription",
			filters={"parent": enc.encounter_id},
			fields=["medication", "drug_code", "dosage", "period", "dosage_form"],
			order_by="idx asc"
		)

		if prescriptions:
			for idx, p in enumerate(prescriptions):
				result.append({
					"encounter_date": enc.encounter_date if idx == 0 else "",
					"patient_name": enc.patient_name if idx == 0 else "",
					"doctor_name": enc.doctor_name if idx == 0 else "",
					"doctor_session": session_fmt if idx == 0 else "",
					"token_no": enc.token_no if idx == 0 else "",
					"diagnoses": diag_str if idx == 0 else "",
					"medication": p.medication,
					"drug_code": p.drug_code or "-",
					"dosage": p.dosage or "-",
					"period": p.period or "-",
					"dosage_form": p.dosage_form or "-",
					"status": enc.status if idx == 0 else ""
				})
		else:
			result.append({
				"encounter_date": enc.encounter_date,
				"patient_name": enc.patient_name,
				"doctor_name": enc.doctor_name,
				"doctor_session": session_fmt,
				"token_no": enc.token_no,
				"diagnoses": diag_str,
				"medication": "-",
				"drug_code": "-",
				"dosage": "-",
				"period": "-",
				"dosage_form": "-",
				"status": enc.status
			})

	return result

def get_report_summary(data):
	unique_patients = len(set(d.get("patient_name") for d in data if d.get("patient_name")))
	total_consultations = sum(1 for d in data if d.get("encounter_date"))
	total_prescriptions = sum(1 for d in data if d.get("medication") and d.get("medication") != "-")

	return [
		{
			"value": unique_patients,
			"indicator": "Blue",
			"label": _("Unique Patients"),
			"datatype": "Int"
		},
		{
			"value": total_consultations,
			"indicator": "Purple",
			"label": _("Total Consultations"),
			"datatype": "Int"
		},
		{
			"value": total_prescriptions,
			"indicator": "Green",
			"label": _("Prescribed Medications"),
			"datatype": "Int"
		}
	]

def get_chart(data):
	date_counts = {}
	for d in data:
		dt = str(d.get("encounter_date") or "")
		if dt:
			date_counts[dt] = date_counts.get(dt, 0) + 1

	sorted_dates = sorted(date_counts.keys(), reverse=True)[:7]
	sorted_dates.reverse()

	return {
		"data": {
			"labels": sorted_dates,
			"datasets": [
				{
					"name": _("Visits"),
					"values": [date_counts[d] for d in sorted_dates]
				}
			]
		},
		"type": "line",
		"height": 280,
		"colors": ["#805ad5"]
	}
