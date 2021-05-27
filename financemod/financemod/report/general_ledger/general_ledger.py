# Copyright (c) 2013, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, _dict
from collections import OrderedDict
from frappe.utils import getdate, cstr, flt, fmt_money


def execute(filters=None):
	columns, data = [], []
	gl_entries = get_gl_entries(filters)
	data = get_data_with_opening_closing(filters, gl_entries)

	columns = get_columns(filters)
	return columns, data


def get_gl_entries(filters):

	order_by_statement= ''
	if filters.get("group_by") == _("Group by Voucher"):
		order_by_statement = "order by posting_date, voucher_type, voucher_no"

	gl_entries = frappe.db.sql(
		"""
		SELECT
			name as gl_entry, posting_date, account, voucher_type, voucher_no, against, debit_amount, credit_amount
		FROM `tabGL Entry` 
		WHERE
			posting_date >= %(from_date)s AND posting_date <= %(to_date)s
			
			{conditions}
		
		""".format(
			from_date = filters['from_date'],to_date = filters['to_date'],conditions=get_conditions(filters),order_by_statement=order_by_statement
		),
		filters, as_dict=1)
	return gl_entries


def get_conditions(filters):
	conditions =[]
	
	if filters.get('account'):
		conditions.append(''' AND account = %(account)s  ''')

	if filters.get("voucher_no"):
		conditions.append(" AND voucher_no=%(voucher_no)s")

	if not filters.get("show_cancelled_entries"):
		conditions.append(" AND is_cancelled = 0")
	
	return ''.join(conditions)



def get_data_with_opening_closing(filters, gl_entries):
	data = []

	gle_map = get_gle_map(gl_entries, filters)

	totals, entries = calculate_gle_open_close_totals(gl_entries, gle_map, filters)

	# Opening for filtered account
	data.append(totals.opening)

	if filters.get("group_by") != _('Group by Voucher (Consolidated)'):
		for acc, acc_dict in gle_map.items():
			# acc
			if acc_dict.entries:
				# opening
				data.append({})
				if filters.get("group_by") != _("Group by Voucher"):
					data.append(acc_dict.totals.opening)

				data += acc_dict.entries

				# totals
				data.append(acc_dict.totals.total)

				# closing
				if filters.get("group_by") != _("Group by Voucher"):
					data.append(acc_dict.totals.closing)
		data.append({})
	else:
		data += entries

	# totals
	data.append(totals.total)

	# closing
	data.append(totals.closing)

	return data


def get_totals_dict():
	def _get_debit_credit_dict(label):
		return _dict(
			account="'{0}'".format(label),
			debit_amount = 0.0,
			credit_amount = 0.0,
			debit_in_account_currency=0.0,
			credit_in_account_currency=0.0
		)
	return _dict(
		opening = _get_debit_credit_dict(_('Opening')),
		total = _get_debit_credit_dict(_('Total')),
		closing = _get_debit_credit_dict(_('Closing (Opening + Total)'))
	)		
	
def group_by_field(group_by):
	if group_by in [_('Group by Voucher (Consolidated)'), _('Group by Account')]:
		return 'account'
	else:
		return 'voucher_no'

def get_gle_map(gl_entries, filters):
	gle_map = OrderedDict()
	group_by = group_by_field(filters.get('group_by'))

	for gle in gl_entries:
		gle_map.setdefault(gle.get(group_by), _dict(totals=get_totals_dict(), entries=[]))
	# print("GLE MAP  :::::: ",gle_map)
	return gle_map


def calculate_gle_open_close_totals(gl_entries, gle_map, filters,):
	totals = get_totals_dict()
	entries = []
	consolidated_gle = OrderedDict()
	group_by = group_by_field(filters.get('group_by'))

	def update_value_in_dict(data, key, gle):
		data[key]['debit_amount'] += flt(gle.debit_amount)
		data[key]['credit_amount'] += flt(gle.credit_amount)

		if data[key].against_voucher and gle.against_voucher:
			data[key].against_voucher += ', ' + gle.against_voucher
		

	for gle in gl_entries:
		update_value_in_dict(gle_map[gle.get(group_by)].totals, 'total', gle)
		update_value_in_dict(totals, 'total', gle)

		if filters.get("group_by") != _('Group by Voucher (Consolidated)'):
			gle_map[gle.get(group_by)].entries.append(gle)
		elif filters.get("group_by") == _('Group by Voucher (Consolidated)'):
			keylist = [gle.get("voucher_type"), gle.get("voucher_no"), gle.get("account")]
			key = tuple(keylist)
			if key not in consolidated_gle:
				consolidated_gle.setdefault(key, gle)
			else:
				print()
				update_value_in_dict(consolidated_gle, key, gle)
		
		update_value_in_dict(gle_map[gle.get(group_by)].totals, 'closing', gle)
		update_value_in_dict(totals, 'closing', gle)
	
	for key, value in consolidated_gle.items():
		entries.append(value)
	
	return totals, entries


def get_columns(filters):
	
	currency = 'INR'

	columns = [
		{
			"label": _("GL Entry"),
			"fieldname": "gl_entry",
			"fieldtype": "Link",
			"options": "GL Entry",
			"hidden": 1
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 90
		},
		{
			"label": _("Account"),
			"fieldname": "account",
			"fieldtype": "Link",
			"options": "Account",
			"width": 180
		},
		{
			"label": _("Debit ({0})").format(currency),
			"fieldname": "debit_amount",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Credit ({0})").format(currency),
			"fieldname": "credit_amount",
			"fieldtype": "Float",
			"width": 100
		},
	# 	{
	# 		"label": _("Balance ({0})").format(currency),
	# 		"fieldname": "balance",
	# 		"fieldtype": "Float",
	# 		"width": 130
	# 	}
	]

	columns.extend([
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"width": 120
		},
		{
			"label": _("Voucher No"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 180
		},
		{
			"label": _("Against Account"),
			"fieldname": "against",
			"width": 120
		},
		# {
		# 	"label": _("Party Type"),
		# 	"fieldname": "party_type",
		# 	"width": 100
		# },
		# {
		# 	"label": _("Party"),
		# 	"fieldname": "party",
		# 	"width": 100
		# },
		# {
		# 	"label": _("Project"),
		# 	"options": "Project",
		# 	"fieldname": "project",
		# 	"width": 100
		# }
	])

	# if filters.get("include_dimensions"):
	# 	for dim in get_accounting_dimensions(as_list = False):
	# 		columns.append({
	# 			"label": _(dim.label),
	# 			"options": dim.label,
	# 			"fieldname": dim.fieldname,
	# 			"width": 100
	# 		})

	# columns.extend([
	# 	{
	# 		"label": _("Cost Center"),
	# 		"options": "Cost Center",
	# 		"fieldname": "cost_center",
	# 		"width": 100
	# 	},
	# 	{
	# 		"label": _("Against Voucher Type"),
	# 		"fieldname": "against_voucher_type",
	# 		"width": 100
	# 	},
	# 	{
	# 		"label": _("Against Voucher"),
	# 		"fieldname": "against_voucher",
	# 		"fieldtype": "Dynamic Link",
	# 		"options": "against_voucher_type",
	# 		"width": 100
	# 	},
	# 	{
	# 		"label": _("Supplier Invoice No"),
	# 		"fieldname": "bill_no",
	# 		"fieldtype": "Data",
	# 		"width": 100
	# 	},
	# 	{
	# 		"label": _("Remarks"),
	# 		"fieldname": "remarks",
	# 		"width": 400
	# 	}
	# ])

	return columns