frappe.ui.form.on('Patient Encounter', {
	refresh: function(frm) {
		if (frm.doc.opd_form) {
			frm.set_df_property('patient', 'read_only', 1);
			frm.set_df_property('patient_name', 'read_only', 1);
			frm.set_df_property('doctor', 'read_only', 1);
			frm.set_df_property('doctor_session', 'read_only', 1);
			frm.set_df_property('opd_form', 'read_only', 1);
			frm.set_df_property('status', 'read_only', 1);
		}

		if (frm.doc.patient) {
			frm.add_custom_button(__('View Patient History'), function() {
				frappe.call({
					method: 'opd_management.opd_management.doctype.patient_encounter.patient_encounter.get_patient_history',
					args: { patient: frm.doc.patient },
					callback: function(r) {
						var history = r.message || [];
						var html = '<table class="table table-bordered"><thead><tr><th>Date</th><th>Doctor</th><th>Diagnoses</th><th>Prescriptions</th></tr></thead><tbody>';

						if (history.length === 0) {
							html += '<tr><td colspan="4" class="text-center">No previous encounter history found.</td></tr>';
						} else {
							history.forEach(function(h) {
								var rx = h.prescriptions.map(function(p) {
									return p.medication + ' (' + p.dosage + ', ' + p.period + ')';
								}).join('<br>') || '-';
								html += '<tr><td>' + h.date + '</td><td>' + h.doctor + '</td><td>' + h.diagnoses + '</td><td>' + rx + '</td></tr>';
							});
						}
						html += '</tbody></table>';

						var d = new frappe.ui.Dialog({
							title: __('Patient History — ') + (frm.doc.patient_name || frm.doc.patient),
							fields: [{ fieldtype: 'HTML', fieldname: 'history_html', options: html }],
							primary_action_label: __('Close'),
							primary_action: function() { d.hide(); }
						});
						d.show();
					}
				});
			});
		}
	}
});

frappe.ui.form.on('Encounter Prescription', {
	medication: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.medication) {
			frappe.db.get_value('Medication', row.medication, 'drug_code', function(r) {
				if (r && r.drug_code) {
					frappe.model.set_value(cdt, cdn, 'drug_code', r.drug_code);
				}
			});
		}
	}
});
