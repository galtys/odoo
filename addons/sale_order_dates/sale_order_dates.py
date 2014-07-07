# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, osv

class sale_order_dates(osv.osv):
    _inherit = 'sale.order'

    def _get_effective_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        dates_list = []
        for order in self.browse(cr, uid, ids, context=context):
            dates_list = []
            for pick in order.picking_ids:
                dates_list.append(pick.date)
            if dates_list:
                res[order.id] = min(dates_list)
            else:
                res[order.id] = False
        return res

    def _get_commitment_date(self, cr, uid, ids, name, arg, context=None):
        res = {}
        dates_list = []
        for order in self.browse(cr, uid, ids, context=context):
            dates_list = []
            for line in order.order_line:
                dt = datetime.strptime(order.date_order, '%Y-%m-%d') + relativedelta(days=line.delay or 0.0)
                dt_s = dt.strftime('%Y-%m-%d')
                dates_list.append(dt_s)
            if dates_list:
                res[order.id] = min(dates_list)
        return res
    _columns = {
        'commitment_date': fields.function(_get_commitment_date, store=True, type='date', string='Commitment Date', help="Committed date for delivery."),
        'requested_date': fields.date('Requested Date', help="Date requested by the customer for the sale."),
        'effective_date': fields.function(_get_effective_date, type='date', store=True, string='Effective Date',help="Date on which picking is created."),
    }

sale_order_dates()

#67: Need to be able to sort by 'requested date' in Delivery Orders
class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    def _requested_date_ids(self, cr, uid, ids, context=None):
        out=[]
        for so in self.pool.get('sale.order').browse(cr, uid, ids):
            for p in so.picking_ids:
                out.append( p.id )
        return out
    def init(self,cr):
        cr.execute("select id from stock_picking where sale_id is not Null")
        p_ids=[x[0] for x in cr.fetchall()]
        for p in self.pool.get('stock.picking').browse(cr, 1, p_ids):
            if p.sale_id.requested_date != p.requested_date:
                p.write({'requested_date':p.sale_id.requested_date})
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Sale Order',
            ondelete='set null', select=True),
        'requested_date': fields.related('sale_id', 'requested_date', string='Reqested Date',type="date",
                                         store={'sale.order':(_requested_date_ids, ['requested_date'],10)} ),
        #'requested_date_db': fields.date('Requested Date', help="Date requested by the customer for the sale."),
    }
stock_picking()

class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    def _requested_date_ids(self, cr, uid, ids, context=None):
        out=[]
        for so in self.pool.get('sale.order').browse(cr, uid, ids):
            for p in so.picking_ids:
                out.append( p.id )
        return out
    _columns = {
        'sale_id': fields.many2one('sale.order', 'Sale Order',
            ondelete='set null', select=True),
        'requested_date': fields.related('sale_id', 'requested_date', string='Reqested Date',type="date",
                                         store={'sale.order':(_requested_date_ids, ['requested_date'],10)} 
                                         ),
        #'requested_date_db': fields.date('Requested Date', help="Date requested by the customer for the sale."),
    }
stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
