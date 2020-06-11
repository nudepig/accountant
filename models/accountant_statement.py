# -*- coding: utf-8 -*-

from odoo import models, fields, api



class AccountantCustomerGross(models.Model):
    _description = 'this is stock brand gross'
    _name = 'accountant.customer.gross'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    line_ids = fields.One2many('accountant.customer.gross.line', 'move_id', string='客户毛利率',
                               copy=True, readonly=True, ondelete="Cascade")


    def customer_gross_open_table(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        name = self.name
        startDate = self.startDate
        endDate = self.endDate
        company_id = self.company_id.id
        move_id = self.id

        # vals = {
        #     'name': name,
        #     'startDate': startDate,
        #     'endDate' : endDate,
        #     'company_id' : company_id,
        # }
        # self.create(vals)
        self.env['accountant.customer.gross.line'].accountant_stock_category(name, startDate, endDate, company_id, move_id)

    # @api.model_create_multi
    # def create(self, values):
    #     return super(AccountantCustomerGross, self).create(values)



class AccountantCustomerGrossLine(models.Model):
    _description = 'this is stock brand gross line'
    _name = 'accountant.customer.gross.line'
    name = fields.Char(string="报表名称", required=True)
    partner_id_name = fields.Char(string="合作伙伴名称", store=True, readonly=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    income = fields.Monetary(default=0.0, string="收入",
                             store=True, currency_field='company_currency_id', readonly=True)
    cost = fields.Monetary(default=0.0, string="成本",
                           store=True, currency_field='company_currency_id', readonly=True)
    gross_profit = fields.Monetary(default=0.0, string="毛利额",
                                   store=True, currency_field='company_currency_id', readonly=True)
    gross_rate = fields.Float(digits=(10, 2), string="毛利率", readonly=True)
    move_id = fields.Many2one('accountant.customer.gross', string='库存周转', ondelete="Cascade",
                              help="The move of this entry line.", index=True, auto_join=True)

    def accountant_stock_category(self, name, startDate, endDate, company_id, move_id):
        partner = self.env['res.partner'].search([]).mapped('id')
        for partner_id in partner:
            partner_id_name = self.env['res.partner'].search([('id', '=', partner_id)]).name
            income = sum(self.env['account.move.line'].search([('company_id', '=', company_id),
                                                               ('date', '>=', startDate),
                                                               ('date', '<=', endDate),
                                                               ('partner_id', '=', partner_id),
                                                               ('account_id', '=', 62)]).mapped('balance'))
            income = income * -1

            cost = sum(self.env['account.move.line'].search([('company_id', '=', company_id),
                                                             ('date', '>=', startDate),
                                                             ('date', '<=', endDate),
                                                             ('partner_id', '=', partner_id),
                                                             ('account_id', '=', 67)]).mapped('balance'))
            gross_profit = income - cost
            if gross_profit and income:
                gross_rate = gross_profit / income
                # gross_rate = '%.2f' % gross_rate + "%"
            else:
                gross_rate = None
            if gross_rate:
                values = {
                    'move_id': move_id,
                    'name': name,
                    'income': income,
                    'cost': cost,
                    'gross_profit': gross_profit,
                    'gross_rate': gross_rate,
                    'company_id': company_id,
                    'partner_id_name': partner_id_name
                }
                self.create(values)

    @api.model_create_multi
    def create(self, values):
        return super(AccountantCustomerGrossLine, self).create(values)





class AccountantStatement(models.Model):
    _description = 'this is invoice statement'
    _name = 'accountant.statement'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    partner_id = fields.Many2one('res.partner', string='客户', change_default=True, readonly=False,
                                 track_visibility='always', ondelete='restrict', store=True, required=True)
    balance_sum = fields.Monetary(string="本期余额", store=True,
                              currency_field='company_currency_id', readonly=True)
    balance_first = fields.Monetary(string="期初余额", store=True,
                              currency_field='company_currency_id', readonly=True)
    balance_end = fields.Monetary(string="期末余额", store=True,
                              currency_field='company_currency_id', readonly=True)
    line_ids = fields.One2many('accountant.statement.line','move_id',string='本期明细', copy=True, readonly=True, ondelete='Cascade')

    def accountant_statement(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        partner_id = self.partner_id.id
        invoice_list = self.env['account.invoice'].search([('partner_id', '=', partner_id),
                                                           ('company_id', '=', self.company_id.id),
                                                           ('date_invoice', '>=', self.startDate),
                                                           ('date_invoice', '<=', self.endDate)]).ids
        balance_sum = 0
        for invoice_id in invoice_list:
            state = self.env['account.invoice'].search([('id', '=', invoice_id)]).state
            number = self.env['account.invoice'].search([('id', '=', invoice_id)]).number
            date = self.env['account.invoice'].search([('id', '=', invoice_id)]).date_invoice
            user_id = self.env['account.invoice'].search([('id', '=', invoice_id)]).user_id.partner_id.name
            team_id = self.env['account.invoice'].search([('id', '=', invoice_id)]).team_id.name
            origin = self.env['account.invoice'].search([('id', '=', invoice_id)]).origin
            stock_picking_list = self.env['stock.picking'].search([('origin', '=', origin)]).mapped('name')
            stock_picking = ' '.join(stock_picking_list)  # 注意引号内有空格
            receivable = sum(self.env['account.move.line'].search([('invoice_id', '=', invoice_id),
                                                                  ('account_id', '=', 5)]).mapped('balance'))
            residual_signed = self.env['account.invoice'].search([('id', '=', invoice_id)]).residual_signed
            balance_sum += residual_signed
            sql = 'select payment_id from account_invoice_payment_rel where invoice_id = %s' % invoice_id
            self.env.cr.execute(sql)
            result = self.env.cr.dictfetchall()
            payment_ids = [x['payment_id'] for x in result]
            discount = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
                                                                 ('account_id', '=', 420)]).mapped('balance'))
            # receivable_income_s = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
            #                                                                ('account_id', '=', 5)]).mapped('balance'))
            # receivable_income_e = sum(self.env['account.move.line'].search([('payment_id', 'in', payment_ids),
            #                                                               ('account_id', '=', 5)]).mapped('amount_residual'))
            # receivable_income = (receivable_income_s - receivable_income_e) * -1 - discount  # 用payment_id 找对应的应收
            receivable_income = sum(self.env['account.move.line'].search([('invoice_id', '=', invoice_id),
                                                                          ('account_id', '=', 5)]).mapped('balance_cash_basis'))
            vals = {
                'move_id': self.id,
                'company_id': self.company_id.id,
                'partner_id': partner_id,
                'partner_id_name': self.partner_id.name,
                'state': state,
                'number': number,
                'date': date,
                'user_id': user_id,
                'team_id': team_id,
                'origin': origin,
                'stock_picking': stock_picking,
                'receivable': receivable,
                'receivable_income': receivable_income,
                'balance': residual_signed,
                'discount': discount,
            }
            self.env['accountant.statement.line'].create(vals)

        self.balance_sum = balance_sum

        invoice_list_last = self.env['account.invoice'].search([('partner_id', '=', partner_id),
                                                           ('company_id', '=', self.company_id.id),
                                                           ('date_invoice', '<', self.startDate)]).ids
        balance_first = 0
        for list_last in invoice_list_last:
            balance_first += self.env['account.invoice'].search([('id', '=', list_last)]).residual_signed
        self.balance_first = balance_first
        self.balance_end = self.balance_first + self.balance_sum

class AccountantStatementLine(models.Model):
    _description = 'this is statement line'
    _name = 'accountant.statement.line'
    move_id = fields.Many2one('accountant.statement', string='本期明细', ondelete='Cascade', index=True, auto_join=True)
    partner_id = fields.Many2one('res.partner', string='客户', change_default=True, readonly=False,
                                 track_visibility='always', ondelete='restrict', store=True, required=True)
    partner_id_name = fields.Char(string='客户名称', store=True, copy=False)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    state = fields.Selection([
        ('draft', '草稿'),
        ('open', '打开'),
        ('in_payment', '正在付款'),
        ('paid', '已支付'),
        ('cancel', '取消'),
    ], string='发票状态', index=True, readonly=True,
        track_visibility='onchange', copy=False,)
    number = fields.Char(string='发票名称', store=True, readonly=True, copy=False)
    date = fields.Date(string='日期', copy=False, readonly=True)
    user_id = fields.Char(string='销售员', store=True, readonly=True, copy=False)
    team_id = fields.Char(string='销售团队', store=True, readonly=True, copy=False)
    origin = fields.Char(string='源文档', store=True, readonly=True, copy=False)
    receivable = fields.Monetary(string="应收", store=True,
                                 currency_field='company_currency_id', readonly=True)
    receivable_income = fields.Monetary(string="已收", store=True,
                                        currency_field='company_currency_id', readonly=True)
    discount_receivable = fields.Monetary(string="应收折让", store=True,
                                          currency_field='company_currency_id', readonly=True)
    balance = fields.Monetary(string="余额", store=True,
                              currency_field='company_currency_id', readonly=True)
    total = fields.Float(string='合计', digits=(10, 2))
    stock_picking = fields.Char(string='送货单号', store=True, copy=False)
    discount = fields.Float(string='折扣', digits=(10, 2))

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantStatementLine, self).create(values)
        return lines




















