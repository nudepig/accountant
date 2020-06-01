# -*- coding: utf-8 -*-
from odoo import http
import json

# class Accountant(http.Controller):
# #     @http.route('/accountant/accountant/', auth='public')
# #     def index(self, **kw):
# #         return "Hello, world"
#
# #     @http.route('/accountant/accountant/objects/', auth='public')
# #     def list(self, **kw):
# #         return http.request.render('accountant.listing', {
# #             'root': '/accountant/accountant',
# #             'objects': http.request.env['accountant.accountant'].search([]),
# #         })
#
# #     @http.route('/accountant/accountant/objects/<model("accountant.accountant"):obj>/', auth='public')
# #     def object(self, obj, **kw):
# #         return http.request.render('accountant.object', {
# #             'object': obj
# #         })


# class Accountant(http.Controller):
#     @http.route('/accountant/accountant/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"
#
#     @http.route('/accountant/accountant/objects/', auth='public')
#     def list(self, **kw):
#         res = http.request.env['accountant.course'].sudo().search_read([])
#         print(res)
#
#         return http.request.render('accountant.listing', {
#             'root': '/accountant/accountant/',
#             'objects': http.request.env['accountant.course'].sudo().search([]),
#         })
#
#     @http.route('/accountant/accountant/objects/<model("accountant.course"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('accountant.object', {
#             'object': obj
#         })


class Accountant(http.Controller):
    @http.route('/accountant/accountant/', auth='public')
    def index(self, **kw):
        return "Hello, world"

    @http.route('/accountant/accountant/objects/', auth='public')
    def list(self, **kw):
        res = http.request.env['account.move.line'].sudo().search_read([])
        for rec in res:
            print(rec.get('debit'))
            print(rec.get('credit'))
            print(rec.get('account_id'))

        return http.request.render('accountant.listing', {
            'root': '/accountant/accountant/',
            'objects': http.request.env['account.move.line'].sudo().search([]),
        })

    @http.route('/accountant/accountant/objects/<model("account.move.line"):obj>/', auth='public')
    def object(self, obj, **kw):
        return http.request.render('accountant.object', {
            'object': obj
        })
