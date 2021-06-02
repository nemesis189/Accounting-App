# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
import json
from frappe.utils import flt, cint


@frappe.whitelist()
def clickmethod(quantity,item):
	# print(quantity)
	item_dict = json.loads(item)
	item_name = get_item_name(item_dict)
	q = float(quantity)
	total = q * flt(item_dict['rate'])
	# print(item_name)
	# print(filters)

	doc = frappe.get_doc({
		'doctype' : 'Sales Invoice',
		'series' : 'ACC-SINV-.YYYY.-',
		'item' : [
			{'item_name': item_name['name'], 'rate': item_dict['rate'], 'quantity':quantity, 'total':total}
		],
		'customer' : '35d7e4b50c'

	})

	doc.save()
	# doc.insert()
	return 

def get_item_name(item_dict):
	query = f'''  
		SELECT name FROM tabItem
		WHERE item_code = '{item_dict['code']}'
	'''
	item_name = frappe.db.sql(query, as_dict=True)
	return item_name[0]

def get_customer_name(item_dict):
	query = f'''  
		SELECT name FROM tabCustomer
		WHERE customer_name = '{item_dict['code']}'
	'''
	item_name = frappe.db.sql(query, as_dict=True)
	return item_name[0]


class Item(WebsiteGenerator):
	pass
