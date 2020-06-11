# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date

from odoo import models, api, _, fields
from odoo.osv import expression
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.tools.misc import formatLang
from odoo.tools import date_utils



class AccountantOverview(models.Model):
    _name = "accountant.overview"

    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",
                                  oldname='currency')
    company_id = fields.Many2one('res.company', string='Company')
    name = fields.Char(string='名称')
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')



    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(self.get_journal_dashboard_datas())

    @api.multi
    def get_journal_dashboard_datas(self):
        currency = self.env.user.company_id.currency_id
        today = fields.Date.today()
        month = date_utils.start_of(today, 'month')
        # sum_sale_order = sum(self.env['sale.order'].search([('state', '=', 'sale'), ('date_order', '<=', today),('date_order', '>=', today)]).mapped('total'))
        # print('888'*100)
        # print(today)
        # print('%.2f' %sum_sale_order)

        company_id = self.env.user.company_id.id

        sql_quotation = '''SELECT total FROM sale_order WHERE state = %s AND date_order >= %s AND company_id = %s;

               '''
        self.env.cr.execute(sql_quotation, ('draft', month, company_id))
        quotation_result = self.env.cr.dictfetchall()
        (quotation_count, quotation_sum) = self._sale_sum_results(quotation_result)


        sql_sale='''SELECT total FROM sale_order WHERE state = %s AND date_order >= %s AND company_id = %s;
        '''
        self.env.cr.execute(sql_sale, ('sale', month, company_id))
        sale_result = self.env.cr.dictfetchall()
        (sale_count, sale_sum) = self._sale_sum_results(sale_result)

        sql_invoice = '''SELECT total FROM sale_order WHERE invoice_status = %s AND date_order >= %s AND company_id = %s;
                '''
        self.env.cr.execute(sql_invoice, ('to invoice', month, company_id))
        invoice_result = self.env.cr.dictfetchall()
        (invoice_count, invoice_sum) = self._sale_sum_results(invoice_result)

        sql_collection = '''SELECT amount FROM account_payment WHERE partner_type = %s AND payment_date >= %s;
        '''
        self.env.cr.execute(sql_collection, ('customer', month))
        collection_result = self.env.cr.dictfetchall()
        (collection_count, collection_sum) = self._collection_sum_results(collection_result)

        sql_salesperson = '''SELECT rp.name, SUM(so.total) as total, COUNT(so.total) as count FROM sale_order as so, res_users as ru, res_partner as rp WHERE so.state = %s AND so.date_order >= %s AND so.company_id = %s AND so.user_id =  ru.id AND ru.partner_id = rp.id GROUP BY rp.name ORDER BY total desc LIMIT 6;
        '''
        self.env.cr.execute(sql_salesperson, ('sale', month, company_id))
        salesperson_result = self.env.cr.dictfetchall()

        sql_salesteam = '''SELECT ct.name, SUM(so.total) as total, COUNT(so.total) as count FROM sale_order as so, crm_team as ct WHERE so.state = 'sale' AND so.date_order >= '2020-6-1' AND so.company_id = 1 AND so.team_id =  ct.id GROUP BY ct.name ORDER BY total desc LIMIT 6;;
                '''
        self.env.cr.execute(sql_salesteam, ('sale', month, company_id))
        salesteam_result = self.env.cr.dictfetchall()

        return {
            'sum_sale_order' : formatLang(self.env, currency.round(sale_sum) + 0.0, currency_obj=currency),
            'sale_title' : '本月销售订单统计',
            'sale_count' : sale_count,
            'title_quotation' : '本月报价单统计',
            'quotation_sum' : formatLang(self.env, currency.round(quotation_sum) + 0.0, currency_obj=currency),
            'quotation_count' : quotation_count,
            'invoice_title' : '本月待开发票统计',
            'invoice_count' : invoice_count,
            'invoice_sum' : formatLang(self.env, currency.round(invoice_sum) + 0.0, currency_obj=currency),
            'collection_title': '本月回款统计',
            'collection_count': collection_count,
            'collection_sum': formatLang(self.env, currency.round(collection_sum) + 0.0, currency_obj=currency),
            'salesperson_result': salesperson_result,
            'salesteam_result': salesteam_result,


        }

    def _sale_sum_results(self, result_dict):
        rslt_count = 0
        rslt_sum = 0.0
        for result in result_dict:
            rslt_sum += result.get('total')
            rslt_count += 1
        return  (rslt_count, rslt_sum)

    def _collection_sum_results(self, result_dict):
        rslt_count = 0
        rslt_sum = 0.0
        for result in result_dict:
            rslt_sum += result.get('amount')
            rslt_count += 1
        return  (rslt_count, rslt_sum)