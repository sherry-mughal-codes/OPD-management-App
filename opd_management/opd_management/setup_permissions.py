import frappe

def setup_roles_and_permissions():
	roles = ["OPD Receptionist", "OPD Doctor", "OPD Manager"]

	for role in roles:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({
				"doctype": "Role",
				"role_name": role,
				"desk_access": 1
			}).insert(ignore_permissions=True)

	permissions = [
		# OPD Receptionist
		{"parent": "OPD Form", "role": "OPD Receptionist", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 0},
		{"parent": "Patient", "role": "OPD Receptionist", "read": 1, "write": 1, "create": 1},
		{"parent": "Sales Invoice", "role": "OPD Receptionist", "read": 1, "write": 1, "create": 1},
		{"parent": "Doctor", "role": "OPD Receptionist", "read": 1},
		{"parent": "Doctor Session", "role": "OPD Receptionist", "read": 1},
		{"parent": "Patient Encounter", "role": "OPD Receptionist", "read": 1},

		# OPD Doctor
		{"parent": "Patient Encounter", "role": "OPD Doctor", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 0},
		{"parent": "OPD Form", "role": "OPD Doctor", "read": 1},
		{"parent": "Patient", "role": "OPD Doctor", "read": 1},
		{"parent": "Doctor", "role": "OPD Doctor", "read": 1},
		{"parent": "Doctor Session", "role": "OPD Doctor", "read": 1},
		{"parent": "Medication", "role": "OPD Doctor", "read": 1},
		{"parent": "Diagnosis", "role": "OPD Doctor", "read": 1},

		# OPD Manager
		{"parent": "OPD Form", "role": "OPD Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
		{"parent": "Patient Encounter", "role": "OPD Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
		{"parent": "Patient", "role": "OPD Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Doctor", "role": "OPD Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Doctor Session", "role": "OPD Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Medication", "role": "OPD Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Diagnosis", "role": "OPD Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Room", "role": "OPD Manager", "read": 1, "write": 1, "create": 1},

		# System Manager
		{"parent": "OPD Form", "role": "System Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
		{"parent": "Patient Encounter", "role": "System Manager", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
		{"parent": "Patient", "role": "System Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Doctor", "role": "System Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Doctor Session", "role": "System Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Medication", "role": "System Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Diagnosis", "role": "System Manager", "read": 1, "write": 1, "create": 1},
		{"parent": "Room", "role": "System Manager", "read": 1, "write": 1, "create": 1}
	]

	for perm in permissions:
		exists = frappe.db.exists("Custom DocPerm", {
			"parent": perm["parent"],
			"role": perm["role"]
		})
		if not exists:
			doc = frappe.get_doc({
				"doctype": "Custom DocPerm",
				"parent": perm["parent"],
				"role": perm["role"],
				"read": perm.get("read", 0),
				"write": perm.get("write", 0),
				"create": perm.get("create", 0),
				"submit": perm.get("submit", 0),
				"cancel": perm.get("cancel", 0),
				"permlevel": 0
			})
			doc.insert(ignore_permissions=True)

	frappe.db.commit()
	print("Roles and permissions set up successfully.")

if __name__ == '__main__':
	setup_roles_and_permissions()
