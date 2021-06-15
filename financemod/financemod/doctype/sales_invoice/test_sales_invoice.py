# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestSalesInvoice(unittest.TestCase):
	si_doc = None
	def setUp(self):
		if not frappe.db.exists('Item',{'item_code':'cont111'}):
			create_test_item(item_code='cont111',item_name='Container1',rate='10',def_uom='units')

		if not frappe.db.exists('Customer', {'customer_id':'test123'}):
			create_test_customer(cust_id='test123', fname='Test', lname='Customer')
		self.customer = frappe.db.get_value('Customer', {'customer_id':'test123'}, 'name')
		item = [
			{'item_name': 'Container1', 'rate': '10', 'quantity':'100', 'total':'1000'},
		]
		self.si_doc = create_si(item,self.customer)


	def test_sales_invoice_total_quantity_and_rate(self):
		self.assertEqual(frappe.get_value("Sales Invoice",self.si_doc.name,"total_quantity"),100.0)
		self.assertEqual(frappe.get_value("Sales Invoice",self.si_doc.name,"total_rate"),1000.0)
	
	def test_if_sales_inv_gle_cr_db_are_equal(self):
		gle_docs = frappe.get_list('GL Entry', fields=['credit_amount','debit_amount'], filters={'voucher_no':self.si_doc.name})
		total_credit = sum([ gle.credit_amount for gle in gle_docs ])
		total_debit = sum([ gle.debit_amount for gle in gle_docs ])

		self.assertEqual(total_credit,total_debit)
		
		
	
	def tearDown(self):
		self.si_doc.cancel()
		for i in range(4):
			delete_test_doc('GL Entry', 'voucher_no',self.si_doc.name)
		delete_test_doc('Sales Invoice','customer',self.customer)
		delete_test_doc('Item','item_code','cont111')
		delete_test_doc('Customer','customer_id','test123')


def create_si(item,name):
	doc = frappe.get_doc({
		'doctype' : 'Sales Invoice',
		'series' : 'ACC-SINV-.YYYY.-',
		'item' : item,
		'customer' : name,
	})
	doc.save()
	doc.submit()
	return doc

def create_test_item(**args):
	args = frappe._dict(args)
	doc = frappe.get_doc({
		'doctype': 'Item',
		'item_name': args.item_name,
		'item_code':args.item_code,
		'rate':args.rate,
		'def_uom':args.def_uom
	}).insert()

def create_test_customer(**args):
	args = frappe._dict(args)
	doc = frappe.get_doc({
		'doctype': 'Customer',
		'customer_id': args.cust_id,
		'first_name':args.fname,
		'last_name':args.lname
	}).insert()

def delete_test_doc(dt, id_name, id):
	if frappe.db.exists(dt, {id_name:id}):
		name = frappe.db.get_value(dt,{id_name:id},"name")
		frappe.delete_doc(dt,name)