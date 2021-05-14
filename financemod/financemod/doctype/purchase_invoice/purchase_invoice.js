// Copyright (c) 2021, subin and contributors
// For license information, please see license.txt

var calculate_total_rate_and_quantity = function(frm){
	var doc = frm.doc
	let total_quantity = 0.0;
	let total_rate = 0.0
	if(doc.item){
		$.each(doc.item, function(index, data){
			total_quantity += data.accepted_quantity;
			total_rate += data.rate * data.accepted_quantity;
			data.amount = data.rate * data.accepted_quantity;
			
		})
	}
	frm.refresh_field('item')
	frm.set_value('total_quantity',total_quantity); 	
	frm.set_value('total_rate',total_rate);
}

frappe.ui.form.on('Purchase Invoice', {
	
	refresh: function(frm) {
		frm.refresh_field('item');		
	}
});

frappe.ui.form.on('Purchase Invoice Item', {

	quantity: function(frm) {
		calculate_total_rate_and_quantity(frm);
	},

	rate: function(frm) {
		calculate_total_rate_and_quantity(frm);
	}
});