import frappe
from frappe import _
from frappe.model.document import Document

class OPDForm(Document):
	def validate(self):
		self.handle_existing_patient_lookup()
		self.fetch_session_details()
		self.check_session_capacity()

	def handle_existing_patient_lookup(self):
		if not self.phone_no:
			return

		existing_patient = frappe.db.get_value(
			"Patient",
			{"phone_no": self.phone_no.strip()},
			["name", "patient_name", "gender", "company"],
			as_dict=True
		)

		if existing_patient:
			self.patient = existing_patient.name
			self.patient_name = existing_patient.patient_name
			self.gender = existing_patient.gender
			if existing_patient.company:
				self.company = existing_patient.company

	def fetch_session_details(self):
		if self.doctor_session:
			sess = frappe.db.get_value("Doctor Session", self.doctor_session, ["session_name", "from_time", "to_time", "checkup_fee"], as_dict=True)
			if sess:
				self.session_name = sess.session_name
				self.from_time = sess.from_time
				self.to_time = sess.to_time
				if sess.checkup_fee is not None:
					self.checkup_fee = sess.checkup_fee

	def check_session_capacity(self):
		if not self.doctor or not self.date or not self.doctor_session:
			return

		session_doc = frappe.get_doc("Doctor Session", self.doctor_session)
		max_patients = session_doc.max_patients or 0

		if max_patients > 0:
			existing_tokens = frappe.db.sql("""
				SELECT count(name)
				FROM `tabOPD Form`
				WHERE doctor = %s
				  AND date = %s
				  AND doctor_session = %s
				  AND docstatus = 1
				  AND name != %s
			""", (self.doctor, self.date, self.doctor_session, self.name))[0][0] or 0

			if existing_tokens >= max_patients:
				frappe.throw(_(f"The session's max patients are {max_patients} and {existing_tokens} tokens are already generated."))

	def on_submit(self):
		self.ensure_patient_record()
		self.validate_capacity_and_generate_token()

	def ensure_patient_record(self):
		if not self.patient and self.phone_no:
			existing_patient = frappe.db.get_value("Patient", {"phone_no": self.phone_no.strip()}, "name")
			if existing_patient:
				self.patient = existing_patient
			else:
				new_patient = frappe.get_doc({
					"doctype": "Patient",
					"patient_name": self.patient_name or self.phone_no.strip(),
					"gender": self.gender or "Other",
					"phone_no": self.phone_no.strip(),
					"company": self.company
				})
				new_patient.insert(ignore_permissions=True)
				self.patient = new_patient.name

			frappe.db.set_value("OPD Form", self.name, "patient", self.patient)

	def validate_capacity_and_generate_token(self):
		if not self.doctor or not self.date or not self.doctor_session:
			frappe.throw(_("Doctor, Date, and Doctor Session are required for token generation."))

		session_doc = frappe.get_doc("Doctor Session", self.doctor_session)
		max_patients = session_doc.max_patients or 0

		# Lock key for serialized concurrency
		lock_key = f"opd_token_{self.doctor}_{self.date}_{self.doctor_session}"
		frappe.db.sql(f"SELECT GET_LOCK('{lock_key}', 10)")

		try:
			existing_tokens = frappe.db.sql("""
				SELECT count(name)
				FROM `tabOPD Form`
				WHERE doctor = %s
				  AND date = %s
				  AND doctor_session = %s
				  AND docstatus = 1
				  AND name != %s
			""", (self.doctor, self.date, self.doctor_session, self.name))[0][0] or 0

			if max_patients > 0 and existing_tokens >= max_patients:
				frappe.throw(_(f"The session's max patients are {max_patients} and {existing_tokens} tokens are already generated."))

			next_token = existing_tokens + 1
			self.token_no = next_token
			self.status = "Waiting"

			frappe.db.set_value("OPD Form", self.name, {
				"token_no": next_token,
				"status": "Waiting"
			})

			# Update patient visit count
			if self.patient:
				total_visits = frappe.db.sql("""
					SELECT count(name) FROM `tabOPD Form`
					WHERE patient = %s AND docstatus = 1
				""", (self.patient,))[0][0] or 1

				frappe.db.set_value("Patient", self.patient, "visits", total_visits)

		finally:
			frappe.db.sql(f"SELECT RELEASE_LOCK('{lock_key}')")

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_doctor_sessions(doctype, txt, searchfield, start, page_len, filters):
	doctor = filters.get("parent") if filters else None
	if not doctor:
		return []

	query = """
		SELECT name, CONCAT(session_name, ' (', TIME_FORMAT(from_time, '%%H:%%i'), ' - ', TIME_FORMAT(to_time, '%%H:%%i'), ')') as label
		FROM `tabDoctor Session`
		WHERE parent = %s
	"""
	params = [doctor]
	if txt:
		query += " AND (session_name LIKE %s OR day LIKE %s)"
		params.extend([f"%{txt}%", f"%{txt}%"])

	query += " ORDER BY idx ASC LIMIT %s, %s"
	params.extend([int(start), int(page_len)])

	return frappe.db.sql(query, tuple(params))

@frappe.whitelist()
def get_session_details(doctor, session):
	if not doctor or not session:
		return {}

	doc = frappe.get_doc("Doctor Session", session)
	return {
		"session_name": doc.session_name or "",
		"checkup_fee": doc.checkup_fee or 0.0,
		"room": doc.room or "",
		"max_patients": doc.max_patients or 0,
		"from_time": str(doc.from_time) if doc.from_time else "",
		"to_time": str(doc.to_time) if doc.to_time else ""
	}

@frappe.whitelist()
def create_sales_invoice(opd_form_name):
	opd = frappe.get_doc("OPD Form", opd_form_name)
	if opd.sales_invoice:
		frappe.throw(_(f"A Sales Invoice '{opd.sales_invoice}' already exists for this OPD Form."))

	# Get or create Customer
	customer_name = frappe.db.get_value("Customer", {"customer_name": opd.patient_name})
	if not customer_name:
		customer_group = frappe.db.get_value("Customer Group", {"is_group": 0, "name": "Individual"}, "name") or frappe.db.get_value("Customer Group", {"is_group": 0}, "name") or "Individual"
		cust = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": opd.patient_name,
			"customer_type": "Individual",
			"customer_group": customer_group,
			"territory": "All Territories"
		})
		cust.insert(ignore_permissions=True)
		customer_name = cust.name

	# Ensure OPD Consultation Item exists
	if not frappe.db.exists("Item", "OPD Consultation"):
		item = frappe.get_doc({
			"doctype": "Item",
			"item_code": "OPD Consultation",
			"item_name": "OPD Consultation",
			"item_group": "Services",
			"is_stock_item": 0,
			"is_sales_item": 1
		})
		item.insert(ignore_permissions=True)

	sinv = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": customer_name,
		"company": opd.company,
		"posting_date": opd.date,
		"items": [{
			"item_code": "OPD Consultation",
			"qty": 1,
			"rate": opd.checkup_fee
		}]
	})
	sinv.insert(ignore_permissions=True)

	frappe.db.set_value("OPD Form", opd.name, "sales_invoice", sinv.name)
	return sinv.name
