# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class SalesInvoice(Document):
	def get_item_accounts(self):
		item_accounts = {}

		for j in range(len(self.item)):
			if self.item[j].credit_to in item_accounts:
				item_accounts[self.item[j].credit_to] += float(self.item[j].total)
			else:
				item_accounts.update({self.item[j].credit_to : float(self.item[j].total)})
		return item_accounts

	def enable_is_cancel(self):
		query = f"""
				UPDATE 
					`tabGL Entry`
				SET 
					is_cancelled = 1
				WHERE 
					voucher_no = '{self.name}' 

				"""
		frappe.db.sql(query)

	def create_gl_entry(self,cancel_entry):
		item_accounts = self.get_item_accounts()

		#create entries for cred accounts			
		for  ac,am in item_accounts.items():
			acct = ac
			acct_against = self.debit_to
			cred_amount = am
			debt_amount = 0
			is_cancel = False 
			# is_credit = False

		#if reverse entry the reverse the account details
			if cancel_entry:
				cred_amount,debt_amount = debt_amount, cred_amount
				is_cancel = True 

				self.enable_is_cancel()


			# for crediting item entries
			doc = frappe.get_doc({
				'doctype': 'GL Entry',
				'posting_date':self.date,
				'posting_time':self.posting_time,
				'account': acct,
				'debit_amount': debt_amount,
				'credit_amount': cred_amount,
				'against':acct_against,
				'voucher_type':self.doctype,
				'voucher_no':self.name,
				'is_cancelled':is_cancel,
			})
			doc.insert()

		#for debiting payment from account
		doc = frappe.get_doc({
				'doctype': 'GL Entry',
				'posting_date':self.date,
				'posting_time':self.posting_time,
				'posting_due_date': self.posting_due_date,
				'account': self.debit_to,
				'credit_amount': sum([float(b) for a,b in item_accounts.items()]) if is_cancel else 0,
				'debit_amount': 0 if is_cancel else sum([float(b) for a,b in item_accounts.items()]) ,
				'against': ' ,'.join(list(a for a,b in item_accounts.items())),
				'voucher_type':self.doctype,
				'voucher_no':self.name,
				'is_cancelled': True if cancel_entry else False,
		})
		doc.insert()
		self.reload()

	def before_submit(self):
		#totals validation
		error = 'in the Sales Invoice is incorrect!'
		if self.total_quantity != sum([float(item.quantity) for item in self.item]):
			error = 'Total Quantity ' + error

		if self.total_rate != sum([float(item.total) for item in self.item]):
			error = 'Total Rate ' + error

		if error != 'in the Sales Invoice is incorrect!':
			frappe.throw(frappe._(error))


	def on_submit(self):
		self.create_gl_entry(0)
		self.reload()

	def on_cancel(self):
		self.create_gl_entry(1)
		self.reload()
