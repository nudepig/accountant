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
    # line_ids = fields.One2many('accountant.customer.gross.line', 'move_id', string='库存周转率',
    #                            copy=True, readonly=True, ondelete="Cascade")
    # partner_id = fields.Many2one('res.partner', string='客户', change_default=True, readonly=False,
    #                              track_visibility='always', ondelete='restrict', store=True, required=True)

    def _accountant_stock_category(self, partner_id, partner_id_name):
        start_s = self.startDate
        start_e = self.endDate
        income = sum(self.env['account.move.line'].search([('company_id', '=', self.company_id.id),
                                                           ('date', '>=', start_s),
                                                           ('date', '<=', start_e),
                                                           ('partner_id', '=', partner_id),
                                                           ('account_id', '=', 62)]).mapped('balance'))
        income = income * -1

        cost = sum(self.env['account.move.line'].search([('company_id', '=', self.company_id.id),
                                                         ('date', '>=', start_s),
                                                         ('date', '<=', start_e),
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
                'income': income,
                'cost': cost,
                'gross_profit': gross_profit,
                'gross_rate': gross_rate,
                'company_id': self.company_id.id,
                'startDate': start_s,
                'endDate': start_e,
                'name': self.name,
                'partner_id_name': partner_id_name
            }
            self.create(values)

    def customer_gross_open_table(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        partner = self.env['res.partner'].search([]).mapped('id')
        for partner_id in partner:
            partner_id_name = self.env['res.partner'].search([('id', '=', partner_id)]).name
            self._accountant_stock_category(partner_id, partner_id_name)

    partner_id_name = fields.Char(string="合作伙伴名称", store=True, readonly=True)
    income = fields.Monetary(default=0.0, string="收入",
                             store=True, currency_field='company_currency_id', readonly=True)
    cost = fields.Monetary(default=0.0, string="成本",
                           store=True, currency_field='company_currency_id', readonly=True)
    gross_profit = fields.Monetary(default=0.0, string="毛利额",
                                   store=True, currency_field='company_currency_id', readonly=True)
    gross_rate = fields.Float(digits=(10, 2), string="毛利率", readonly=True)

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantCustomerGross, self).create(values)
        return lines

    def remove_data(self):
        try:
            sql = "DELETE FROM accountant_customer_gross"
            self.env.cr.execute(sql)
        except Exception:
            pass


class AccountantInvoiceStatement(models.Model):
    _description = 'this is invoice statement'
    _name = 'accountant.invoice.statement'
    name = fields.Char(string="报表名称", required=True)
    startDate = fields.Date(string="开始期间", required=True)
    endDate = fields.Date(string="结束期间", required=True)
    fast_period = fields.Datetime(string="选取期间")
    # startDate = fields.Date(string="开始期间", required=True)
    # endDate = fields.Date(string="结束期间", required=True)
    # fast_period = fields.Datetime(string="选取期间")
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Company Currency", readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='公司',
                                 store=True, index=True, readonly=False, required=True)
    partner_id = fields.Many2one('res.partner', string='客户', change_default=True, readonly=False,
                                 track_visibility='always', ondelete='restrict', store=True, required=True)

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
    # user_id = fields.Many2one('res.users', string='销售员', readonly=True, copy=False)
    user_id = fields.Char(string='销售员', store=True, readonly=True, copy=False)
    # team_id = fields.Many2one('crm.team', string='销售团队')
    team_id = fields.Char(string='销售团队', store=True, readonly=True, copy=False)
    origin = fields.Char(string='源文档', store=True, readonly=True, copy=False)
    # product_id = fields.Many2one('product.product', string='产品',
    #                              ondelete='restrict', index=True)
    product_id = fields.Char(string='产品名称', store=True, readonly=True, copy=False)
    # uom_id = fields.Many2one('uom.uom', string='计量单位',
    #                          ondelete='set null', index=True)
    uom_id = fields.Char(string='计量单位', store=True, readonly=True, copy=False)

    quantity = fields.Float(string='数量', digits=(10, 2))
    price_unit = fields.Float(string='单价', digits=(10, 2))
    receivable = fields.Monetary(string="应收", store=True,
                                       currency_field='company_currency_id', readonly=True)
    receivable_income = fields.Monetary(string="已收", store=True,
                                        currency_field='company_currency_id', readonly=True)
    discount_receivable = fields.Monetary(string="应收折让", store=True,
                                          currency_field='company_currency_id', readonly=True)
    balance = fields.Monetary(string="余额", store=True,
                              currency_field='company_currency_id', readonly=True)
    product_id_name = fields.Char(string='客户名称', store=True, copy=False)
    total = fields.Float(string='合计', digits=(10, 2))
    stock_picking = fields.Char(string='送货单号', store=True, copy=False)
    discount = fields.Float(string='折扣', digits=(10, 2))

    def accountant_statement(self):
        if self.startDate > self.endDate:
            raise exceptions.ValidationError('你选择的开始日期不能大于结束日期')
        partner_id = self.partner_id.id
        invoice_list = self.env['account.invoice'].search([('partner_id', '=', partner_id),
                                                           ('company_id', '=', self.company_id.id),
                                                           ('date_invoice', '>=', self.startDate),
                                                           ('date_invoice', '<=', self.endDate)]).ids
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
                'partner_id': partner_id,
                'product_id_name': self.partner_id.name,
                'company_id': self.company_id.id,
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
                'name': self.name,
                'startDate': self.startDate,
                'endDate': self.endDate,
            }
            self.create(vals)
            self._account_invoice_line(invoice_id, state, number, date, user_id, team_id, origin)

    def _account_invoice_line(self, invoice_id, state, number, date, user_id, team_id, origin):
        product_id_list = self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id)]).mapped('product_id')
        for product_id in product_id_list:
            product_id = product_id.id
            uom_id = self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                              ('product_id', '=', product_id)], limit=1).uom_id.name
            quantity = sum(self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                                   ('product_id', '=', product_id)]).mapped('quantity'))
            price_unit_list = self.env['account.invoice.line'].search([('invoice_id', '=', invoice_id),
                                                                      ('product_id', '=', product_id)]).mapped('price_unit')
            price_unit = sum(price_unit_list)/len(price_unit_list)
            product_id_name = self.env['product.product'].search([('id', '=', product_id)]).product_tmpl_id.name
            total = quantity * price_unit
            values = {
                'partner_id': self.partner_id.id,
                'product_id_name': self.partner_id.name,
                'company_id': self.company_id.id,
                'state': state,
                'number': number,
                'date': date,
                'user_id': user_id,
                'team_id': team_id,
                'origin': origin,
                'product_id': product_id_name,
                'uom_id': uom_id,
                'quantity': quantity,
                'price_unit': price_unit,
                'total': total,
                # 'receivable_debit': receivable_debit,
                # 'receivable_credit': receivable_credit,
                # 'balance': balance,
                'name': self.name,
                'startDate': self.startDate,
                'endDate': self.endDate,
            }
            self.create(values)

    def remove_data(self):
        try:
            sql = "DELETE FROM accountant_invoice_statement"
            self.env.cr.execute(sql)
        except Exception:
            pass

    @api.model_create_multi
    def create(self, values):
        lines = super(AccountantInvoiceStatement, self).create(values)
        return lines





















