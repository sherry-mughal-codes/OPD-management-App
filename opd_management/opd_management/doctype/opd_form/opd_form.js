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

	onload: function(frm) {
		frm.trigger('setup_phone_autocomplete');
	},

	setup_phone_autocomplete: function(frm) {
		if (!frm.fields_dict.phone_no || !frm.fields_dict.phone_no.$input) return;
		var $input = frm.fields_dict.phone_no.$input;
		if ($input.data('has_phone_autocomplete')) return;
		$input.data('has_phone_autocomplete', true);

		var awesomplete = new Awesomplete($input[0], {
			minChars: 2,
			maxItems: 10,
			autoFirst: true,
			data: function(item) {
				return {
					label: item.phone_no + ' — ' + item.patient_name,
					value: item.phone_no,
					patient_data: item
				};
			}
		});

		$input.on('input', function() {
			var val = $(this).val();
			if (val && val.length >= 2) {
				frappe.call({
					method: 'opd_management.opd_management.doctype.opd_form.opd_form.get_phone_suggestions',
					args: { txt: val },
					callback: function(r) {
						if (r.message && r.message.length) {
							awesomplete.list = r.message;
						}
					}
				});
			}
		});

		$input.on('awesomplete-selectcomplete', function(e) {
			var selected = e.text;
			var phone_val = (selected && selected.value) ? selected.value : $input.val();
			frm.set_value('phone_no', phone_val);
		});
	},

	phone_no: function(frm) {
		var current_phone = (frm.doc.phone_no || '').trim();
		if (frm._last_checked_phone && frm._last_checked_phone === current_phone) return;

		var digits = current_phone.replace(/[^0-9]/g, '');
		if (digits.length >= 7) {
			frm._last_checked_phone = current_phone;
			frappe.call({
				method: 'frappe.client.get_value',
				args: {
					doctype: 'Patient',
					filters: { phone_no: current_phone },
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
			frm._last_checked_phone = '';
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
		frm.trigger('setup_phone_autocomplete');
		frm.trigger('update_session_description');

		if (frm.doc.docstatus === 1) {
			frm.add_custom_button(__('Print Slip'), function() {
				frappe.call({
					method: 'opd_management.opd_management.doctype.opd_form.opd_form.increment_print_count',
					args: { docname: frm.doc.name },
					callback: function() {
						frm.print_doc();
					}
				});
			}, __('Actions')).addClass('btn-info');

			if (!frm.doc.sales_invoice) {
				frm.add_custom_button(__('Generate Sales Invoice'), function() {
					frappe.call({
						method: 'opd_management.opd_management.doctype.opd_form.opd_form.create_sales_invoice',
						args: { opd_form_name: frm.doc.name },
						callback: function(r) {
							if (r.message) {
								frappe.msgprint(__('Sales Invoice created and marked as Paid: {0}', [r.message]));
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

