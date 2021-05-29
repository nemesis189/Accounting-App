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

	columns = get_columns(filters)

	gle_list = entries_as_per_group(gl_entries,filters)
	data = calculate_totals_for_group(filters, gle_list)



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



def get_totals_row():

	def get_row(title):
		return _dict(
				account = title,
				debit_amount = 0.0,
				credit_amount = 0.0
			)
		
	return _dict(
		opening = get_row('Opening'),
		total = get_row('Total'),
		closing = get_row('Closing (Total + Opening'),

	)

def map_by_group(gl_entries, grp_key):
	accounts = OrderedDict()
	for gle in gl_entries:
		accounts.setdefault(gle.get(grp_key), []).append(gle)
	return accounts
		
def get_key_for_group(filters):
	if filters['group_by'] in ['Group by Voucher (Consolidated)', 'Group by Voucher']:
		return 'voucher_no'
	else: return 'account'




def entries_as_per_group(gl_entries, filters):
	gle_list = {}
	key_list = []
	grp_key = get_key_for_group(filters)
	accounts_by_voucher = map_by_group(gl_entries, grp_key)
	consolidated = 1 if filters['group_by'] == 'Group by Voucher (Consolidated)' else 0
	if consolidated:
		for vno in list(accounts_by_voucher):
			for gle in accounts_by_voucher[vno]:
				key = (vno, gle['account'])
				if key not in key_list:
					key_list.append(key)
					gle_list[key] = gle
				else:
					gle_list[key]['debit_amount']+= gle[debit_amount]
					gle_list[key]['credit_amount']+= gle[credit_amount]

					if gle_list[key]['against'] and gle['against']:
						gle_list[key]['against'] += ' ,'+gle['against']
		final_gle_list = { x: [gle_list[x]] for x in gle_list}
		return final_gle_list
	else:
		return accounts_by_voucher 


def calculate_totals_for_group(filters,gle_list):
	data = []
	consolidated_total = get_totals_row()
	consolidated = 1 if filters['group_by'] == 'Group by Voucher (Consolidated)' else 0

	for row in gle_list:
		if not consolidated:
			data.append({})
		totals = get_totals_row()
		for entries in gle_list[row]:
			totals['total']['debit_amount']  += entries['debit_amount']
			totals['total']['credit_amount']  += entries['credit_amount']

		totals['closing']['debit_amount']  = totals['opening']['debit_amount'] + totals['total']['debit_amount']
		totals['closing']['credit_amount'] = totals['opening']['credit_amount'] + totals['total']['credit_amount']

		consolidated_total['total']['debit_amount'] += totals['total']['debit_amount']
		consolidated_total['total']['credit_amount'] += totals['total']['credit_amount']

		if not consolidated:
			if filters['group_by'] != 'Group by Voucher':
				data.append(totals['opening'])
			data += gle_list[row]
			if not consolidated:
				data += [totals['total'],totals['closing'] ]

		else:
			data += gle_list[row]
			
	consolidated_total['closing']['debit_amount']  = consolidated_total['opening']['debit_amount'] + consolidated_total['total']['debit_amount']
	consolidated_total['closing']['credit_amount'] = consolidated_total['opening']['credit_amount'] + consolidated_total['total']['credit_amount']
	
	data.append({})
	data += [consolidated_total['total'],consolidated_total['closing'] ]
	data = [ consolidated_total['opening']] + data
	return data


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
		
	])


	return columns