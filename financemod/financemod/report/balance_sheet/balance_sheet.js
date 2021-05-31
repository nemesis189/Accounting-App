// Copyright (c) 2016, subin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Balance Sheet"] = {
	"filters": [
		{
			fieldname: "filter_based_on",
			label: "Filter Based On",
			fieldtype: "Select",
			// mandatory: true,
			options: ['Fiscal Year', 'Date Range'],
			default: 'Fiscal Year',
			on_change: function() {
				let filter_based_on = frappe.query_report.get_filter_value('filter_based_on');
				frappe.query_report.toggle_filter_display('start_year', filter_based_on === 'Date Range');
				frappe.query_report.toggle_filter_display('end_year', filter_based_on === 'Date Range');
				frappe.query_report.toggle_filter_display('period_start_date', filter_based_on === 'Fiscal Year');
				frappe.query_report.toggle_filter_display('period_end_date', filter_based_on === 'Fiscal Year');

				frappe.query_report.refresh();
			}
		},
		{
			fieldname: "start_year",
			label: "Start Year",
			fieldtype: "Link",
			// mandatory: true,
			options: 'Fiscal Year',
			// default: 'Fiscal Year',
			reqd:1
		},
		{
			fieldname: "end_year",
			label: "End Year",
			fieldtype: "Link",
			// mandatory: true,
			options: 'Fiscal Year',
			// default: 'Fiscal Year',
			reqd:1
		},
		{
			fieldname: "from_date",
			label: "From Date",
			fieldtype: "Date",
			// mandatory: true,
			default: frappe.datetime.year_start(),
			hidden: 1,
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: "To Date",
			fieldtype: "Date",
			// mandatory: true,
			default: frappe.datetime.year_end(),
			hidden: 1,
			reqd: 1
		},
		{
			fieldname: "periodicity",
			label: "Periodicity",
			fieldtype: 'Select',
			options: [ 'Monthly', 'Quarterly', 'Yearly'],
			mandatory: true,
			default: 'Yearly'
		}
		  
	]
};
