import frappe
from frappe import _
from frappe.model.document import Document

class PatientEncounter(Document):
	def validate(self):
		self.fetch_medication_drug_codes()

	def fetch_medication_drug_codes(self):
		for row in self.get("prescriptions"):
			if row.medication and not row.drug_code:
				drug_code = frappe.db.get_value("Medication", row.medication, "drug_code")
				if drug_code:
					row.drug_code = drug_code

	def on_submit(self):
		self.status = "Completed"
		frappe.db.set_value("Patient Encounter", self.name, "status", "Completed")

		if self.opd_form:
			frappe.db.set_value("OPD Form", self.opd_form, "status", "Completed")

@frappe.whitelist()
def create_patient_encounter(opd_form_name):
	opd = frappe.get_doc("OPD Form", opd_form_name)

	# Check if encounter already exists for this OPD Form
	existing = frappe.db.get_value("Patient Encounter", {"opd_form": opd_form_name}, "name")
	if existing:
		return existing

	enc = frappe.get_doc({
		"doctype": "Patient Encounter",
		"opd_form": opd.name,
		"patient": opd.patient,
		"patient_name": opd.patient_name,
		"doctor": opd.doctor,
		"doctor_name": frappe.db.get_value("Doctor", opd.doctor, "doctor_name") or opd.doctor,
		"doctor_session": opd.doctor_session,
		"encounter_date": opd.date,
		"status": "In Consultation",
		"company": opd.company
	})
	enc.insert(ignore_permissions=True)

	# Update OPD Form status to In Consultation
	frappe.db.set_value("OPD Form", opd.name, "status", "In Consultation")

	return enc.name

@frappe.whitelist()
def get_patient_history(patient):
	if not patient:
		return []

	encounters = frappe.db.get_all(
		"Patient Encounter",
		filters={"patient": patient, "docstatus": 1},
		fields=["name", "encounter_date", "doctor", "status"],
		order_by="encounter_date desc"
	)

	history = []
	for enc in encounters:
		diagnoses = frappe.get_all("Encounter Diagnosis", filters={"parent": enc.name}, pluck="diagnosis")
		prescriptions = frappe.get_all("Encounter Prescription", filters={"parent": enc.name}, fields=["medication", "dosage", "period", "dosage_form"])

		doctor_name = frappe.db.get_value("Doctor", enc.doctor, "doctor_name") or enc.doctor

		history.append({
			"encounter": enc.name,
			"date": str(enc.encounter_date),
			"doctor": doctor_name,
			"diagnoses": ", ".join(diagnoses) if diagnoses else "-",
			"prescriptions": prescriptions
		})

	return history
