frappe.ui.form.on('OPD Form', {
	setup: function(frm) {
		frm.set_query('doctor_session', function() {
			return {
				query: 'opd_management.opd_management.doctype.opd_form.opd_form.get_doctor_sessions',
				filters: {
					'parent': frm.doc.doctor
				}
			};
		});
	},

	phone_no: function(frm) {
		var digits = (frm.doc.phone_no || '').replace(/[^0-9]/g, '');
		if (digits.length >= 10) {
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Patient',
					filters: { phone_no: frm.doc.phone_no.trim() },
					fieldname: ['name', 'patient_name', 'gender', 'company']
				},
				callback: function(r) {
					if (r.message && r.message.name) {
						frm.set_value('patient', r.message.name);
						frm.set_value('patient_name', r.message.patient_name);
						if (r.message.gender) frm.set_value('gender', r.message.gender);
						if (r.message.company) frm.set_value('company', r.message.company);
						frappe.show_alert({
							message: __('Existing Patient found: {0}', [r.message.patient_name]),
							indicator: 'green'
						});
					} else {
						frm.set_value('patient', '');
						frappe.show_alert({
							message: __('New Patient. Enter Patient Name & Gender.'),
							indicator: 'blue'
						});
					}
				}
			});
		} else if (digits.length === 0) {
			frm.set_value('patient', '');
		}
	},

	doctor: function(frm) {
		frm.set_value('doctor_session', '');
		frm.set_value('checkup_fee', 0);
		frm.get_field('doctor_session').set_description('');
	},

	doctor_session: function(frm) {
		if (frm.doc.doctor && frm.doc.doctor_session) {
			frappe.call({
				method: 'opd_management.opd_management.doctype.opd_form.opd_form.get_session_details',
				args: {
					doctor: frm.doc.doctor,
					session: frm.doc.doctor_session
				},
				callback: function(r) {
					if (r.message) {
						if (r.message.session_name) frm.set_value('session_name', r.message.session_name);
						if (r.message.from_time) frm.set_value('from_time', r.message.from_time);
						if (r.message.to_time) frm.set_value('to_time', r.message.to_time);
						if (r.message.checkup_fee !== undefined) frm.set_value('checkup_fee', r.message.checkup_fee);

						var desc = '<b>Session:</b> ' + (r.message.session_name || '');
						if (r.message.from_time && r.message.to_time) {
							desc += ' (' + r.message.from_time + ' - ' + r.message.to_time + ')';
						}
						frm.get_field('doctor_session').set_description(desc);
					}
				}
			});
		} else {
			frm.set_value('session_name', '');
			frm.set_value('from_time', '');
			frm.set_value('to_time', '');
			frm.set_value('checkup_fee', 0);
			frm.get_field('doctor_session').set_description('');
		}
	},

	refresh: function(frm) {
		frm.trigger('update_session_description');

		if (frm.doc.docstatus === 1) {
			if (!frm.doc.sales_invoice) {
				frm.add_custom_button(__('Generate Sales Invoice'), function() {
					frappe.call({
						method: 'opd_management.opd_management.doctype.opd_form.opd_form.create_sales_invoice',
						args: { opd_form_name: frm.doc.name },
						callback: function(r) {
							if (r.message) {
								frappe.msgprint(__('Sales Invoice created: {0}', [r.message]));
								frm.reload_doc();
							}
						}
					});
				}, __('Actions')).addClass('btn-primary');
			}

			if (frm.doc.status !== 'Completed') {
				frm.add_custom_button(__('Create Patient Encounter'), function() {
					frappe.call({
						method: 'opd_management.opd_management.doctype.patient_encounter.patient_encounter.create_patient_encounter',
						args: { opd_form_name: frm.doc.name },
						callback: function(r) {
							if (r.message) {
								frappe.set_route('Form', 'Patient Encounter', r.message);
							}
						}
					});
				}, __('Actions')).addClass('btn-success');
			}
		}
	},

	update_session_description: function(frm) {
		if (frm.doc.doctor && frm.doc.doctor_session) {
			frappe.call({
				method: 'opd_management.opd_management.doctype.opd_form.opd_form.get_session_details',
				args: {
					doctor: frm.doc.doctor,
					session: frm.doc.doctor_session
				},
				callback: function(r) {
					if (r.message) {
						var desc = '<b>Session:</b> ' + (r.message.session_name || '');
						if (r.message.from_time && r.message.to_time) {
							desc += ' (' + r.message.from_time + ' - ' + r.message.to_time + ')';
						}
						frm.get_field('doctor_session').set_description(desc);
					}
				}
			});
		} else {
			frm.get_field('doctor_session').set_description('');
		}
	}
});
