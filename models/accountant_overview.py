# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date

from odoo import models, api, _, fields
from odoo.osv import expression
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, safe_eval
from odoo.tools.misc import formatLang



class AccountantOverview(models.Model):
    _name = "accountant.overview"

    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",
                                  oldname='currency')
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id,
                                 help="Company related to this")
    name = fields.Char(string='名称')
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    color = fields.Integer("Color Index", default=0)


    @api.one
    def _kanban_dashboard(self):
        self.kanban_dashboard = json.dumps(self.get_journal_dashboard_datas())

    @api.multi
    def get_journal_dashboard_datas(self):
        currency = self.currency_id or self.company_id.currency_id
        title = '今日销售订单统计'
        today = fields.Date.today()
        # sum_sale_order = sum(self.env['sale.order'].search([('state', '=', 'sale'), ('date_order', '<=', today),('date_order', '>=', today)]).mapped('total'))
        # print('888'*100)
        # print(today)
        # print('%.2f' %sum_sale_order)
        company_id = self.env.user.company_id.id
        sq='''SELECT total FROM sale_order WHERE state = %s AND date_order >= %s AND company_id = %s;
        '''
        self.env.cr.execute(sq, ('sale', today, company_id))
        sale_result = self.env.cr.dictfetchall()
        (sale_count, sale_sum) = self._sale_sum_results(sale_result)

        return {
            'sum_sale_order' : formatLang(self.env, currency.round(sale_sum) + 0.0, currency_obj=currency),
            'title' : title,
            'sale_count' : sale_count
        }

    def _sale_sum_results(self, result_dict):
        rslt_count = 0
        rslt_sum = 0.0
        for result in result_dict:
            rslt_sum += result.get('total')
            rslt_count += 1
        return  (rslt_count, rslt_sum)