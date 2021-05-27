# Copyright (c) 2013, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import datetime
import frappe
from frappe.utils import flt, cint
from frappe import _



def execute(filters=None, filter_by_date=True):

	assets = get_data_to_display('Asset','Debit',filters)
	liabilities = get_data_to_display('Liability','Credit',filters)
	provisional_profit_loss, total_credit = get_provisional_profit_loss(assets, liabilities)

	data = []	
	columns = get_columns()
	data.extend(assets)
	data.extend(liabilities)

	if provisional_profit_loss:
		data.append(provisional_profit_loss)
	if total_credit:
		data.append(total_credit)
	
	report_summary = get_report_summary(assets, liabilities, provisional_profit_loss, total_credit)
	chart = get_chart(assets, liabilities, columns)

	return columns,data,[],chart, report_summary


def get_data_to_display(root_type, balance_must_be,filters):
	accounts = get_accounts(root_type)
	gle_by_accounts = get_gle_accounts(filters,root_type)
	accounts, accounts_by_name, parent_child_accs = filter_parent_child(accounts)

	calculate_values(accounts_by_name,gle_by_accounts,filters)

	output = prepare_data_row(accounts, balance_must_be,filters)
	output = filter_out_zero_value_rows(output, parent_child_accs)

	if output :
		output = add_total_row(output, root_type, balance_must_be)
		output = parent_child_arrangement(output)
		output = bold_and_currency_formatting(output)
	return output


def calculate_values(accounts_by_name, gle_by_accounts,filters):
	abn = accounts_by_name
	for entries in gle_by_accounts.values():
		for entry in entries:
			d = accounts_by_name.get(entry['account'])
			if not d:
				frappe.msgprint(
					_("Could not retrieve information for {0}.").format(entry['account']), title="Error",
					raise_exception=1
				)
			if (entry['posting_date'] <= datetime.strptime(filters['to_date'],'%Y-%m-%d').date()) and (entry['posting_date'] >= datetime.strptime(filters['from_date'],'%Y-%m-%d').date()):
				d['acc_balance'] = d.get('acc_balance', 0.0) + flt(entry['debit_amount']) - flt(entry['credit_amount'])

				
def prepare_data_row(accounts, balance_must_be,filters):
	data = []

	for acc in accounts:
		# add to output
		has_value = False
		total = 0
		row = frappe._dict({
			"account": _(acc['name']),
			"parent_account": _(acc['parent_account']) if acc['parent_account'] else '',
			"indent": flt(acc['indent']),
			"is_group": acc['is_group'],
			"account_name": ('%s' %( _(acc['account_name'])))
		})
		if acc.get('acc_balance') and balance_must_be == "Credit":
			# change sign based on Debit or Credit, since calculation is done using (debit - credit)
			acc['acc_balance'] *= -1

		row['acc_balance'] = flt(acc.get('acc_balance', 0.0), 3)

		if abs(row['acc_balance']) >= 0.005:
			# ignore zero values
			has_value = True
			total += flt(row['acc_balance'])

		row["has_value"] = has_value
		row["total"] = total
		data.append(row)

	return data


def add_total_row(output, root_type, balance_must_be):

	total_row = {
		"account_name": _("Total {0} ({1})").format(_(root_type), _(balance_must_be)),
		"account": _("Total {0} ({1})").format(_(root_type), _(balance_must_be)),
	}

	for row in output:
		if  row.get("parent_account") == 'e5c3e1d569':
			total_row.setdefault('acc_balance', 0.0)
			total_row['acc_balance'] += row.get('acc_balance', 0.0)
			row['acc_balance'] = row.get('acc_balance', 0.0)

			total_row.setdefault("total", 0.0)
			total_row["total"] += flt(row["total"])
			row["total"] = ""

	output = sorted(output, key = lambda k: k['indent'])
	if "total" in total_row:
		output.append(total_row)
		# blank row after Total
		output.append({})
	return output



def filter_out_zero_value_rows(data, parent_children_map, show_zero_values=False):
	data = sorted(data, key = lambda k:k['indent'], reverse = True)
	data_with_value = []
	for _ in range(len(data)):
		for d in data:
			if (show_zero_values or d.get("has_value")) and \
					d.get("account") not in [x['account'] for x in data_with_value] :
				data_with_value.append(d)
			else:
				children = [child['name'] for child in parent_children_map.get(d.get("account")) or []]
				children_dict_list = [child for child in data if child['account'] in children]
				if children:
					for row in data:
						row['currency'] = 'INR'
						if row.get("account") in children and row.get("has_value"):
							if d.get('account') not in [x['account'] for x in data_with_value]:
								
								data_with_value.append(d)
								d['has_value'] = True
								d['acc_balance'] += sum([flt(x.get('acc_balance')) for x in children_dict_list])
								if 'currency' not in d:
									d['currency'] = 'INR'

							break

	return data_with_value



def filter_parent_child(accounts, depth=20):
	parent_children_map = {}
	accounts_by_name = {}
	for acc in accounts:
		accounts_by_name[acc['name']] = acc
		parent_children_map.setdefault(acc['parent_account'] or None, []).append(acc)
	
	accounts_with_level = []

	def add_to_list(parent, level):
		if level < depth:
			children = parent_children_map.get(parent) or []
			for child in children:
				child['indent'] = level
				accounts_with_level.append(child)
				add_to_list(child['name'], level + 1) 
	add_to_list('e5c3e1d569',0)

	return accounts_with_level, accounts_by_name, parent_children_map



def parent_child_arrangement(output):
	op = output[:len(output)-2]
	children_list = [ x for x in op if x['indent']>1]
	new_op = [ y for y in op if y['indent']<2]

	for row in children_list:
		parents_index_list = { x['account']: new_op.index(x) for x in new_op}
		par_index = parents_index_list[row['parent_account']]
		new_op = new_op[ :par_index+1] + [row] + new_op[par_index+1 : ]
	new_op.extend(output[-2:])
	return new_op


def get_provisional_profit_loss(asset, liability):
	provisional_profit_loss = {}
	total_row = {}
	if asset and liability:
		total = total_row_total=0
		currency = 'INR'
		total_row = {
			"account_name": "Total (Credit)",
			"account": "Total (Credit)",
			"warn_if_negative": True,
			"currency": currency
		}
		has_value = False

		key = 'acc_balance'
		effective_liability = 0.0
		if liability:
			effective_liability = flt(liability[-2].get(key))
		
		provisional_profit_loss[key] = flt(asset[-2].get(key)) - effective_liability
		total_row[key] = effective_liability + provisional_profit_loss[key]

		if provisional_profit_loss[key]:
			has_value = True

		total += flt(provisional_profit_loss[key])
		provisional_profit_loss["total"] = total

		total_row_total += flt(total_row[key])
		total_row["total"] = total_row_total

		if has_value:
			provisional_profit_loss.update({
				"account_name": "Provisional Profit / Loss (Credit)",
				"account": "Provisional Profit / Loss (Credit)",
				"warn_if_negative": True,
				"currency": 'INR'
			})

	return provisional_profit_loss, total_row


def get_report_summary(asset, liability, provisional_profit_loss, total_credit):

	net_asset, net_liability, net_provisional_profit_loss = 0.0, 0.0, 0.0

	key = 'acc_balance'
	if asset:
		net_asset = asset[-2].get(key)
	if liability:
		net_liability = liability[-2].get(key)
	if provisional_profit_loss:
		net_provisional_profit_loss = provisional_profit_loss.get(key)

	return [
		{
			"value": net_asset,
			"label": "Total Asset",
			"datatype": "Currency",
			"currency": 'INR'
		},
		{
			"value": net_liability,
			"label": "Total Liability",
			"datatype": "Currency",
			"currency": 'INR'
		},
		{
			"value": net_provisional_profit_loss,
			"label": "Provisional Profit / Loss (Credit)",
			"indicator": "Green" if net_provisional_profit_loss > 0 else "Red",
			"datatype": "Currency",
			"currency": 'INR'
		}
	]


def get_chart(asset,liability, columns):
	labels = [ col.get('label') for col in columns ]

	asset_data, liability_data = [], []

	for c in columns:
		if asset:
			asset_data.append(asset[-2].get(c.get("fieldname")))
		if liability:
			liability_data.append(liability[-2].get(c.get("fieldname")))
		
	datasets = []
	if asset_data:
		datasets.append({'name': 'Assets', 'values': asset_data})
	if liability_data:
		datasets.append({'name': 'Liabilities', 'values': liability_data})

	chart = {
		"data": {
			'labels': labels,
			'datasets': datasets
		},
		"type": 'line'
	}

	return chart



def get_columns():
	columns = [{
			"fieldname": "account",
			"label": _("Account"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 300
		},
		
		{
			"fieldname": "acc_balance",
			"label": "Balance",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		}]
	

	return columns


def get_accounts(root_type):
	query = f""" SELECT 
					name, 
					account_name, 
					parent_account, 
					is_group, 
					root_type, 
					lft, 
					rgt, 
					report_type
				FROM 
					tabAccount   
				WHERE 
					tabAccount.root_type ="{root_type}"
				ORDER BY 
					is_group DESC """
	return frappe.db.sql(query, as_dict=True)

def get_gle_accounts(filters, root_type,filter_by_date=True):
	query = f""" SELECT 
					`tabGL Entry`.account, 
					`tabGL Entry`.credit_amount, 
					`tabGL Entry`.debit_amount, 
					`tabGL Entry`.is_credit, 
					`tabGL Entry`.posting_date, 
					`tabAccount`.account_name, 
					`tabAccount`.parent_account,
					`tabGL Entry`.is_cancelled 
				FROM 
					`tabGL Entry` , `tabAccount`
				WHERE 
					`tabGL Entry`.account = tabAccount.name 
				AND
					`tabGL Entry`.is_cancelled = 0 
				AND 
					tabAccount.report_type="Balance Sheet" 
				AND 
					tabAccount.root_type ="{root_type}"  """
	if filter_by_date:
		query += f""" AND 
						`tabGL Entry`.posting_date 
					BETWEEN 
					  	"{filters['from_date']}" 
					AND 
						"{filters['to_date']}" """
	
	entry_list = frappe.db.sql(query,as_dict=True)
	entries_by_account = {}

	for entry in entry_list:
		entries_by_account.setdefault(entry['account'] or None, []).append(entry)

	return entries_by_account


def bold_and_currency_formatting(output):
	for d in output:
		if d.get('account') and d['account'] in ['Assets' , 'Liabilities', 'Total Asset (Debit)', 'Total Liability (Credit)']:
			d['account'] = frappe.bold(d['account'])
		
		if d.get('currency'):
			d['acc_balance'] = frappe.format(d['acc_balance'], 'Currency')
		
	return output








