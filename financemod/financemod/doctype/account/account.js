// Copyright (c) 2021, subin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Account', {
	refresh: function(frm) {
		frm.toggle_display('account_name', frm.is_new());

		// hide fields if group
		frm.toggle_display('account_type', cint(frm.doc.is_group) == 0);

		// disable fields
		// frm.toggle_enable('is_group', false);


		if(!frm.is_new()) {
			if (!frm.doc.parent_account) {
				frm.set_read_only();
				frm.set_intro(__("This is a root account and cannot be edited."));
			} else {
				// credit days and type if customer or supplier
				frm.set_intro(null);
				frm.trigger('account_type');
			}
			
		}
	}
});

