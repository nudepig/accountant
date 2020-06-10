# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountantSalesPercentage(models.Model):
    _description = 'this is sales'
    _name = 'accountant.sales.percentage'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    user_id = fields.Many2one('res.users', string='销售员', readonly=False, required=True, copy=False)
    line_ids = fields.One2many('accountant.sales.percentage.line', 'move_id', string='客户毛利率',
                               copy=True, readonly=True, ondelete="Cascade")
    total_receivable_income = fields.Float(string='已收合计', digits=(10, 2))
    total_discount = fields.Float(string='折扣合计', digits=(10, 2))
    total_balance = fields.Float(string='余额合计', digits=(10, 2))

    def sales_percentage_open_table(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        startDate = self.startDate
        endDate = self.endDate
        company_id = self.company_id
        user_id = self.user_id
        move_id = self.id

        vals = self.env['accountant.sales.percentage.line'].accountant_sales_percentage(startDate, endDate, company_id, user_id, move_id)
        return self.write(vals)

    @api.multi
    def write(self, vals):
        return super(AccountantSalesPercentage, self).write(vals)





class AccountantSalesPercentageLine(models.Model):
    _description = 'this is sales line'
    _name = 'accountant.sales.percentage.line'
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    partner_id = fields.Char(string='合作伙伴', store=True, readonly=True, copy=False)
    partner_id_name = fields.Char(string='客户名称', store=True, copy=False)

    state = fields.Selection([
        ('draft', '草稿'),
        ('open', '打开'),
        ('in_payment', '正在付款'),
        ('paid', '已支付'),
        ('cancel', '取消'),
    ], string='发票状态', index=True, readonly=True,
        track_visibility='onchange', copy=False, )

    number = fields.Char(string='发票名称', store=True, readonly=True, copy=False)
    date = fields.Date(string='日期', copy=False, readonly=True)
    user_id = fields.Many2one('res.users', string='销售员', readonly=False, required=True, copy=False)
    user_id_name = fields.Char(string='销售人员', store=True, readonly=True, copy=False)
    # team_id = fields.Many2one('crm.team', string='销售团队')
    team_id = fields.Char(string='销售团队', store=True, readonly=True, copy=False)
    origin = fields.Char(string='源文档', store=True, readonly=True, copy=False)
    receivable = fields.Monetary(string="应收", store=True,
                                 currency_field='company_currency_id', readonly=True)
    receivable_income = fields.Monetary(string="已收", store=True,
                                        currency_field='company_currency_id', readonly=True)
    balance = fields.Monetary(string="余额", store=True,
                              currency_field='company_currency_id', readonly=True)

    stock_picking = fields.Char(string='送货单号', store=True, copy=False)
    discount = fields.Float(string='折扣', digits=(10, 2))
    move_id = fields.Many2one('accountant.sales.percentage', string='销售提成', ondelete="Cascade", index=True, auto_join=True)

    @api.multi
    def accountant_sales_percentage(self, startDate, endDate, company_id, user_id, move_id):
        payment_ids = self.env['account.payment'].search([('payment_date', '>=', startDate),
                                                               ('payment_date', '<=', endDate)]).ids

        sql = 'select invoice_id from account_invoice_payment_rel where payment_id in {}'.format(tuple(payment_ids))
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        invoice_ids = [x['invoice_id'] for x in result]
        invoice_list = self.env['account.invoice'].search([('id', 'in', invoice_ids),
                                                           ('user_id', '=', user_id.id),
                                                           ('company_id', '=', company_id.id)]).ids

        total_receivable_income = 0
        total_discount = 0
        total_balance = 0
        for invoice_id in invoice_list:
            partner_id = self.env['account.invoice'].search([('id', '=', invoice_id)]).partner_id.id
            partner_id_name = self.env['account.invoice'].search([('id', '=', invoice_id)]).partner_id.name
            state = self.env['account.invoice'].search([('id', '=', invoice_id)]).state
            number = self.env['account.invoice'].search([('id', '=', invoice_id)]).number
            date = self.env['account.invoice'].search([('id', '=', invoice_id)]).date_invoice
            user_id_name = self.env['account.invoice'].search([('id', '=', invoice_id)]).user_id.partner_id.name
            team_id = self.env['account.invoice'].search([('id', '=', invoice_id)]).team_id.name
            origin = self.env['account.invoice'].search([('id', '=', invoice_id)]).origin
            stock_picking_list = self.env['stock.picking'].search([('origin', '=', origin)]).mapped('name')
            stock_picking = ' '.join(stock_picking_list)  # 注意引号内有空格
            receivable = sum(self.env['account.move.line'].search([('invoice_id', '=', invoice_id),
                                                                  ('account_id', '=', 5)]).mapped('balance'))
            residual_signed = self.env['account.invoice'].search([('id', '=', invoice_id)]).residual_signed
            sql_pay = '''select payment_id from account_invoice_payment_rel where invoice_id = %s;'''
            self.env.cr.execute(sql_pay, (invoice_id))
            result_pay = self.env.cr.dictfetchall()
            payment = [x['payment_id'] for x in result_pay]
            discount = sum(self.env['account.move.line'].search([('payment_id', 'in', payment),
                                                                 ('account_id', '=', 420)]).mapped('balance'))
            # receivable_income_s = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
            #                                                                ('account_id', '=', 5)]).mapped('balance'))
            # receivable_income_e = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
            #                                                               ('account_id', '=', 5)]).mapped('amount_residual'))
            # receivable_income = (receivable_income_s - receivable_income_e) * -1 - discount  # 用payment_id 找对应的应收
            receivable_income = sum(self.env['account.move.line'].search([('invoice_id', '=', invoice_id),
                                                                          ('account_id', '=', 5)]).mapped('balance_cash_basis'))
            total_receivable_income += receivable_income
            total_discount += discount
            total_balance += residual_signed
            vals = {
                'partner_id': partner_id,
                'partner_id_name': partner_id_name,
                'company_id': company_id.id,
                'state': state,
                'number': number,
                'date': date,
                'user_id_name': user_id_name,
                'user_id': user_id.id,
                'team_id': team_id,
                'origin': origin,
                'stock_picking': stock_picking,
                'receivable': receivable,
                'receivable_income': receivable_income,
                'balance': residual_signed,
                'discount': discount,
                'move_id': move_id,
                'startDate': startDate,
                'endDate': endDate,
            }
            super(AccountantSalesPercentageLine, self).create(vals)

        sum_tatal = {
            'total_receivable_income' : total_receivable_income,
            'total_discount' : total_discount,
            'total_balance' : total_balance,
        }
        return sum_tatal






