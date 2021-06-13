# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.website.website_generator import WebsiteGenerator
import json
from frappe.utils import flt, cint


@frappe.whitelist()
def clickmethod(customer,quantity,item):
	item_dict = json.loads(item)
	item_name = get_item_name(item_dict)
	q = float(quantity)
	total = q * flt(item_dict['rate'])
	customer = check_customer(customer)
	
	if customer is None:
		return 'error'

	si,si_doc = find_drafted_si(customer)
	print('SI_1, SIDOC_1 :::::::::',si,si_doc)


	cart = {'item_name': item_name['name'], 'rate': item_dict['rate'], 'quantity':quantity, 'total':total}
	idx = 1
	# try:
	if not si:
		idx += 1
		doc = frappe.get_doc({
			'doctype' : 'Sales Invoice',
			'series' : 'ACC-SINV-.YYYY.-',
			'item' : [ cart ],
			'customer' : customer,
			'total_quantity' : cart['quantity'],
			'total_rate' : cart['total'],
		})
		doc.save(ignore_permissions = True)

	else:
		idx+=1
		print('INSIDE HERRREEEEEEE::::::::',si_doc.docstatus, si_doc.name)
		si_item_fields = {
			'doctype': 'Sales Invoice Item',
			'docstatus' : si_doc.docstatus,
			'parent' : si_doc.name,
			'parentfield' : 'item',
			'parenttype' : 'Sales Invoice',
			'idx' : idx
			
		}

		si_item_fields.update(cart)

		si_item = frappe.get_doc(si_item_fields)
		
		print('BEFORE::::::::',si_doc.total_rate)
		si_doc.total_rate = float(si_doc.total_rate) + float(cart['total'])
		print('AFTER::::::::',si_doc.total_rate)

		si_doc.total_quantity = float(si_doc.total_quantity) + float(cart['quantity'])
		si_doc.save(ignore_permissions = True)
		si_item.save(ignore_permissions = True)
	
	return

@frappe.whitelist()
def check_customer(customer):
	c = frappe.db.sql(''' Select name,first_name,last_name from tabCustomer''', as_dict=True)
	# print(c)
	cust_list = { x.first_name +' '+x.last_name : x.name for x in c}
	if customer not in cust_list:
		return None
	else:
		return cust_list[customer]


@frappe.whitelist()
def insert_customer(fname,lname,cid):
	# print(fname,lname,cid)
	customer = frappe.get_doc({
		'doctype':'Customer',
		'first_name':fname,
		'last_name':lname,
		'customer_id':cid
	})
	# customer.save()
	customer.insert(ignore_permissions = True)
	return 1


	
@frappe.whitelist()
def find_drafted_si(customer):
	si = frappe.db.sql(f'''
		SELECT * from `tabSales Invoice`
		WHERE customer = '{customer}'
		AND docstatus = 0
	''', as_dict=True)
	if si:
		si_doc = frappe.get_doc('Sales Invoice', si[0]['name'])
		return si[0],si_doc 
	return None,None

	

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
