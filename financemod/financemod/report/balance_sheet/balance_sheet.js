// Copyright (c) 2016, subin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Balance Sheet"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			mandatory: true,
			default: frappe.datetime.year_start(),
		  },
		  {
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			mandatory: true,
			default: frappe.datetime.year_end(),
		  }
	]
};
