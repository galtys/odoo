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

import time
from openerp.osv import fields,osv
from openerp.tools.translate import _

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'delivery_line':fields.boolean("Delivery Line"),
        }
    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
                'delivery_line':False,
        })
        return super(sale_order_line, self).copy(cr, uid, id, default, context=context)

sale_order_line()

# Overloaded sale_order to manage carriers :
class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'carrier_id':fields.many2one("delivery.carrier", "Delivery Method", help="Complete this field if you plan to invoice the shipping based on picking."),
        'delivery_invoiced':fields.boolean("Delivery Invoiced"),
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        result = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        if part:
            dtype = self.pool.get('res.partner').browse(cr, uid, part, context=context).property_delivery_carrier.id
            result['value']['carrier_id'] = dtype
        return result

    def _prepare_order_picking(self, cr, uid, order, context=None):
        result = super(sale_order, self)._prepare_order_picking(cr, uid, order, context=context)
        print "prepare order picking carrier", result
        result.update(carrier_id=order.carrier_id.id)
        result.update(delivery_partner_id=order.carrier_id.partner_id.id)
        result.update( {'delivery_notes':order.delivery_notes} )
        return result


    def delivery_set(self, cr, uid, ids, context=None):
        order_obj = self.pool.get('sale.order')
        line_obj = self.pool.get('sale.order.line')
        grid_obj = self.pool.get('delivery.grid')
        carrier_obj = self.pool.get('delivery.carrier')
        acc_fp_obj = self.pool.get('account.fiscal.position')
        cr.execute("select res_id,name from ir_model_data where model='delivery.carrier'")
        carrier_map=dict( [x for x in cr.fetchall()] )

        for order in self.browse(cr, uid, ids, context=context):
            grid_id = carrier_obj.grid_get(cr, uid, [order.carrier_id.id], order.partner_shipping_id.id)
            if not grid_id:
                raise osv.except_osv(_('No Grid Available!'), _('No grid matching for this carrier!'))

            if not order.state in ('draft'):
                raise osv.except_osv(_('Order not in Draft State!'), _('The order state have to be draft to add delivery lines.'))

            grid = grid_obj.browse(cr, uid, grid_id, context=context)

            taxes = grid.carrier_id.product_id.taxes_id
            fpos = order.fiscal_position or False
            taxes_ids = acc_fp_obj.map_tax(cr, uid, fpos, taxes)
            #create the sale order line
            #product = ir_model_data.get_object(cr, uid, 'product', 'product_product_consultant')
            delivery_lines = [l for l in order.order_line if l.delivery_line]
            grid_price = grid_obj.get_price(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context)           
            carrier_ref=carrier_map.get(order.carrier_id.id)
            if carrier_ref in ["standard72"]:
                if order.amount_total > 1000.00:
                    grid_price=0
            elif carrier_ref in ["express48","express24","saturday"]:
                if order.amount_total < 1000.00:
                    grid_price+=40
                elif order.amount_total > 1000.00:
                    grid_price=40
            elif carrier_ref in ["special"]:
                if order.amount_total < 1000.00:
                    grid_price+=70
                elif order.amount_total > 3000.00:
                    grid_price=0
                elif order.amount_total > 2000.00:
                    grid_price=125
                elif order.amount_total > 1000.00:
                    grid_price=95
                
            elif carrier_ref in ["bespoke"]:
                if order.amount_total > 1000.0:
                    grid_price=0
            elif carrier_ref in ["home_delivery"]:
                if order.amount_total > 750.00:
                    grid_price=0
            elif carrier_ref in ["collection"]:
                grid_price=0
            elif carrier_ref in ["parcelforce_carrier"]:
                pass
            elif carrier_ref in ["trade_delivery"]:
                grid_price=65
                if order.amount_untaxed > 1500.00:
                    grid_price=0                
            elif carrier_ref in ["trade_home_delivery"]:
                grid_price=120
                if order.amount_untaxed > 1500.00:
                    grid_price=55
            elif carrier_ref in ["contract_delivery"]:
                grid_price=65
                if order.amount_untaxed > 1600.00:
                    grid_price=0
            if order.carrier_id.name in ["XDP Collection"]:
                grid_price=0
            vals = {
                    'order_id': order.id,
                    'name': grid.carrier_id.name,
                    'product_uom_qty': 1,
                    'product_uom': grid.carrier_id.product_id.uom_id.id,
                    'product_id': grid.carrier_id.product_id.id,
                    'price_unit': grid_price,
                    'tax_id': [(6,0,taxes_ids)],
                    'type': 'make_to_stock',
                    'delivery_line':True,
                }
            print vals
            if len(delivery_lines)==0:
                line_obj.create(cr, uid, vals)
            elif len(delivery_lines)==1:
                vals.pop('order_id')
                delivery_lines[0].write( vals)
            else:
                pass
        #remove the value of the carrier_id field on the sale order
        #return self.write(cr, uid, ids, {'carrier_id': False}, context=context)
        #return {'type': 'ir.actions.act_window_close'} action reload?

sale_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class stock_picking(osv.osv):
    _inherit = 'stock.picking'
    def _delivery_date(self,cr, uid, ids, *a, **kw):
        res={}
        for d in self.browse(cr, uid, ids):
            if d.delivery_date:
                res[d.id]="%s/%s/%s"%tuple([x for x in reversed(d.delivery_date.split('-'))])
            else:
                res[d.id]=''
        return res
    _columns = {
        'pjb_carrier_id': fields.related('sale_id', 'carrier_id', string='Delivery',type="many2one",relation='delivery.carrier'),   
        'delivery_partner_id':fields.many2one("res.partner", "Delivery Partner"),
        'delivery_date': fields.date('Delivery Date',help="Delivery date given by carrier"),
        'delivery_date_f':fields.function(_delivery_date, type="char", string="Delivery Date Formatted"),
    }
stock_picking()


class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'
    def _delivery_date(self,cr, uid, ids, *a, **kw):
        res={}
        for d in self.browse(cr, uid, ids):
            if d.delivery_date:
                res[d.id]="%s/%s/%s"%tuple([x for x in reversed(d.delivery_date.split('-'))])
            else:
                res[d.id]=''
        return res
    _columns = {
        'pjb_carrier_id': fields.related('sale_id', 'carrier_id', string='Delivery',type="many2one",relation='delivery.carrier'),
        'delivery_partner_id':fields.many2one("res.partner", "Delivery Partner"),
        'delivery_date': fields.date('Delivery Date',help="Delivery date given by carrier"),
        'delivery_date_f':fields.function(_delivery_date, type="char", string="Delivery Date Formatted"),
    }
stock_picking_out()
