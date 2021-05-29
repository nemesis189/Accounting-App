# -*- coding: utf-8 -*-
# Copyright (c) 2021, subin and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class PurchaseInvoice(Document):
	def get_item_accounts(self):
		item_accounts = {}

		for j in range(len(self.item)):
			if self.item[j].debit_to in item_accounts.keys():
				item_accounts[self.item[j].debit_to] += int(self.item[j].amount)
			else:
				item_accounts.update({self.item[j].debit_to : int(self.item[j].amount)})
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

		#create entries for debt accounts			
		for  ac,am in item_accounts.items():
			acct = ac
			acct_against = self.credit_to
			debt_amount = am
			cred_amount = 0
			is_cancel = False 
			# is_credit = False

		#if reverse entry the reverse the account details
			if cancel_entry:
				# acct, acct_against = acct_against, acct
				debt_amount,cred_amount = cred_amount,debt_amount
				is_cancel = True 
				# is_credit = True

				self.enable_is_cancel()


			# for debiting item entries
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
				# 'is_credit':is_credit
			})
			doc.insert()

		#for crediting payment from account
		doc = frappe.get_doc({
				'doctype': 'GL Entry',
				'posting_date':self.date,
				'posting_time':self.posting_time,
				'account': self.credit_to,
				'debit_amount': sum([float(b) for a,b in item_accounts.items()]) if is_cancel else 0,
				'credit_amount': 0 if is_cancel else sum([float(b) for a,b in item_accounts.items()]) ,
				'against': ' ,'.join(list(a for a,b in item_accounts.items())),
				'voucher_type':self.doctype,
				'voucher_no':self.name,
				'is_cancelled': True if cancel_entry else False,
				# 'is_credit': True if not cancel_entry else False
		})
		doc.insert()
		self.reload()

	def on_submit(self):
		self.create_gl_entry(0)
		self.reload()

	def on_cancel(self):
		self.create_gl_entry(1)
		self.reload()
