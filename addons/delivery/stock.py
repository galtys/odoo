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

from openerp.osv import fields,osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# Redefinition of the new fields in order to update the model stock.picking.out in the orm
# FIXME: this is a temporary workaround because of a framework bug (ref: lp996816). It should be removed as soon as
#        the bug is fixed
class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _cal_weight(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            total_weight = total_weight_net = 0.00

            for move in picking.move_lines:
                total_weight += move.weight
                total_weight_net += move.weight_net

            res[picking.id] = {
                                'weight': total_weight,
                                'weight_net': total_weight_net,
                              }
        return res


    def _get_picking_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    _columns = {
        'carrier_id':fields.many2one("delivery.carrier","Carrier"),
        'volume': fields.float('Volume'),
        'weight': fields.function(_cal_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
        'weight_net': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=32),
        'number_of_packages': fields.integer('Number of Packages'),
        'weight_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True,readonly="1",help="Unit of measurement for Weight",),
        'email_sent':fields.boolean('Email Sent'),
        'pjb_autowiz':fields.boolean('pjb_autowiz'), #has been process by pjb auto delivery wizzard
        }

    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context=None):
        """Prepare the invoice line to add to the shipping costs to the shipping's
           invoice.

            :param browse_record picking: the stock picking being invoiced
            :param browse_record invoice: the stock picking's invoice
            :return: dict containing the values to create the invoice line,
                     or None to create nothing
        """
        print 44*'__'
        print 'invoice shipping '

            
        carrier_obj = self.pool.get('delivery.carrier')
        grid_obj = self.pool.get('delivery.grid')

        account_id = picking.carrier_id.product_id.property_account_income.id
        if not account_id:
            account_id = picking.carrier_id.product_id.categ_id\
                    .property_account_income_categ.id

        taxes = picking.carrier_id.product_id.taxes_id
        partner = picking.partner_id or False
        if partner:
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, partner.property_account_position, account_id)
            taxes_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, taxes)
        else:
            taxes_ids = [x.id for x in taxes]
        lines = [l for l in picking.sale_id.order_line if l.delivery_line]
        if len(lines)==1 and (not picking.sale_id.delivery_invoiced):
            price = lines[0].price_unit
            vals={
                'name': picking.carrier_id.name,
                'invoice_id': invoice.id,
                'uos_id': picking.carrier_id.product_id.uos_id.id,
                'product_id': picking.carrier_id.product_id.id,
                'account_id': account_id,
                'price_unit': price,
                'quantity': 1,
                'invoice_line_tax_id': [(6, 0, taxes_ids)],
            }
            picking.sale_id.write( {'delivery_invoiced':True} )
        else:
            vals=None
        return vals
    def _get_price_unit_invoice2(self, cr, uid, move_line, type, context=None):
        """ Gets price unit for invoice
        @param move_line: Stock move lines
        @param type: Type of invoice
        @return: The price unit for the move line
        """
        if context is None:
            context = {}

        if type in ('in_invoice', 'in_refund'):
            # Take the user company and pricetype
            context['currency_id'] = move_line.company_id.currency_id.id
            amount_unit = move_line.product_id.price_get('standard_price', context=context)[move_line.product_id.id]
            return amount_unit
        else:


            return move_line.product_id.list_price
        
        #return move_line.product_id.list_price
    def _product_pricelist_price(self, cursor, user, move_line, product_id=None, uom_id=None):
        #print ['id id', move_line, 'sssd']

        pricelist_id = move_line.picking_id.sale_id.pricelist_id.id
        if product_id is None:            
            product_id = move_line.product_id.id
        if uom_id is None:
            uom_id = move_line.product_uom.id            
        partner_id = move_line.picking_id.partner_id.id
        date_order = move_line.picking_id.sale_id.date_order
        price_pricelist = self.pool.get('product.pricelist').price_get(cursor, user, [pricelist_id],
                                                                                 product_id, 1.0, partner_id, 
                                                                                 {'uom': uom_id,
                                                                                  'date': date_order,
                                                                                 })[pricelist_id]
        return price_pricelist
    def _get_price_unit_invoice_galtys(self, cursor, user, move_line, type):
        #ret_super=super(stock_picking, self)._get_price_unit_invoice2(cursor, user, move_line, type)
        print 'CALC', move_line, move_line.sale_line_id.id,  move_line.sale_line_id.move_ids
        #print 'calc', [move_line]
        ret_super=self._get_price_unit_invoice2(cursor, user, move_line, type)
        ret=ret_super
        ret_line=0
        ret_uos=0
        ret_pro_rata=0
        if move_line.sale_line_id and move_line.sale_line_id.product_id.id == move_line.product_id.id:
            ret_line= move_line.sale_line_id.price_unit
            ret=ret_line
            uom_id = move_line.product_id.uom_id.id
            uos_id = move_line.product_id.uos_id and move_line.product_id.uos_id.id or False
            price = move_line.sale_line_id.price_unit
            coeff = move_line.product_id.uos_coeff
            if uom_id != uos_id  and coeff != 0:
                price_unit = price / coeff
                ret_uos=price_unit
                ret=ret_uos
        if move_line.sale_line_id:        
            print 'move_price', move_line
            move_price = self._product_pricelist_price(cursor, user, move_line)
            boms = move_line.sale_line_id.product_id.bom_ids
            if boms:
                if len(boms)==1:
                    #prod,ret =  self.pool.get('mrp.bom')._bom_explode(cursor, user, boms[0], 1)
                    #bom_components_map = dict( [ (x['product_id'],x['product_qty']) for x in prod ] )
                    move_ids=move_line.sale_line_id.move_ids
                    total=0
                    for move in move_ids:
                        if move_line.sale_line_id.procurement_id.move_id.id != move.id:                            
                            price=self._product_pricelist_price(cursor, user, move)
                            print 'move product trade price', move.product_id, price
                            total += move.product_qty*price
                    print 'total', total
                    pro_rata=move_line.sale_line_id.product_uom_qty*move_line.sale_line_id.price_unit/total
                    ret_pro_rata = move_price * pro_rata
                    ret=ret_pro_rata
                    
        print 'GET PRICE LINE', [move_line.name, ret_super, ret_line, ret_uos, ret_pro_rata,ret, move_line.sale_line_id.id,  move_line.sale_line_id.price_unit, move_line.sale_line_id.discount ]
        #raise
        return ret

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        picking_obj = self.pool.get('stock.picking')
        invoice_line_obj = self.pool.get('account.invoice.line')
        result = super(stock_picking, self).action_invoice_create(cr, uid,
                ids, journal_id=journal_id, group=group, type=type,
                context=context)
        def inv_sign(inv):
            if inv.type=='out_invoice':
                return 1.0
            elif inv.type=='out_refund':
                return -1.0
            else:
                raise
        for picking in picking_obj.browse(cr, uid, result.keys(), context=context):
            invoice_id = result[picking.id]
            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            taxes=[]
            account_id=[]
            for inv_line in invoice.invoice_line:
                account_id.append( inv_line.account_id.id )
                for t in inv_line.invoice_line_tax_id:
                    if t.id not in taxes:
                        taxes.append(t.id)
            print 'taxes', taxes
            assert len(taxes)==1

            invoice_line = self._prepare_shipping_invoice_line(cr, uid, picking, invoice, context=context)
            if invoice_line:
                invoice_line_obj.create(cr, uid, invoice_line)
                invoice_obj.button_compute(cr, uid, [invoice.id], context=context)
        #for picking in self.browse(cr, uid, ids, context=context):
            current_invoice_untaxed = invoice_obj.browse(cr, uid, invoice_id).amount_untaxed
            print 'current invoice untaxed ', current_invoice_untaxed, [x.amount_untaxed for x in picking.sale_id.invoice_ids]
            
            invoiced_total = sum( [inv_sign(x)*x.amount_untaxed for x in picking.sale_id.invoice_ids] ) #+ current_invoice_untaxed
            diff_adj = picking.sale_id.amount_untaxed - invoiced_total
            still_2bi=False

            vals = {
                'name': picking.name,
                'origin': picking.name,
                'invoice_id': invoice_id,
                'uos_id': False,
                #'product_id': move_line.product_id.id,
                'account_id': account_id[-1],
                #'price_unit': self._get_price_unit_invoice(cr, uid, move_line, invoice_vals['type']),
                #'discount': self._get_discount_invoice(cr, uid, move_line),
                #'quantity': move_line.product_uos_qty or move_line.product_qty,
                'invoice_line_tax_id': [(6, 0, taxes)],
                #'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
                }
            for p in picking.sale_id.picking_ids:
                if p.id!=picking.id:
                    if p.invoice_state == '2binvoiced':
                        still_2bi=True
    
            if (not still_2bi) and abs(diff_adj) > 0.0:
                print 'DIFF ADJ: ', diff_adj
                if abs(diff_adj)>0.001:
                    assert False
                    raise
                vals['price_unit']=diff_adj
                vals['product_id']=False
                vals['name']='Adj to %s' % picking.sale_id.name
                vals['discount']=0
                vals['quantity']=1
                invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
        return result

    def _get_default_uom(self,cr,uid,c):
        uom_categ, uom_categ_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_categ_kgm')
        return self.pool.get('product.uom').search(cr, uid, [('category_id', '=', uom_categ_id),('factor','=',1)])[0]
    _defaults = {
        'weight_uom_id': lambda self,cr,uid,c: self._get_default_uom(cr,uid,c)
    }


# Overloaded stock_picking to manage carriers :
class stock_picking_out(osv.osv):
    _inherit = 'stock.picking.out'

    def _cal_weight(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for picking in self.browse(cr, uid, ids, context=context):
            total_weight = total_weight_net = 0.00

            for move in picking.move_lines:
                total_weight += move.weight
                total_weight_net += move.weight_net

            res[picking.id] = {
                                'weight': total_weight,
                                'weight_net': total_weight_net,
                              }
        return res


    def _get_picking_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()

    _columns = {
        'carrier_id':fields.many2one("delivery.carrier","Carrier"),
        'volume': fields.float('Volume'),
        'weight': fields.function(_cal_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
        'weight_net': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=32),
        'number_of_packages': fields.integer('Number of Packages'),
        'weight_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True,readonly="1",help="Unit of measurement for Weight",),
        'email_sent':fields.boolean('Email Sent'),
        'pjb_autowiz':fields.boolean('pjb_autowiz'), #has been process by pjb auto delivery wizzard
        }

    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context=None):
        """Prepare the invoice line to add to the shipping costs to the shipping's
           invoice.

            :param browse_record picking: the stock picking being invoiced
            :param browse_record invoice: the stock picking's invoice
            :return: dict containing the values to create the invoice line,
                     or None to create nothing
        """
        print 44*'__'
        print 'invoice shipping '

            
        carrier_obj = self.pool.get('delivery.carrier')
        grid_obj = self.pool.get('delivery.grid')

        account_id = picking.carrier_id.product_id.property_account_income.id
        if not account_id:
            account_id = picking.carrier_id.product_id.categ_id\
                    .property_account_income_categ.id

        taxes = picking.carrier_id.product_id.taxes_id
        partner = picking.partner_id or False
        if partner:
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, partner.property_account_position, account_id)
            taxes_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, taxes)
        else:
            taxes_ids = [x.id for x in taxes]
        lines = [l for l in picking.sale_id.order_line if l.delivery_line]
        if len(lines)==1 and (not picking.sale_id.delivery_invoiced):
            price = lines[0].price_unit
            vals={
                'name': picking.carrier_id.name,
                'invoice_id': invoice.id,
                'uos_id': picking.carrier_id.product_id.uos_id.id,
                'product_id': picking.carrier_id.product_id.id,
                'account_id': account_id,
                'price_unit': price,
                'quantity': 1,
                'invoice_line_tax_id': [(6, 0, taxes_ids)],
            }
            picking.sale_id.write( {'delivery_invoiced':True} )
        else:
            vals=None
        return vals
    def _get_price_unit_invoice2(self, cr, uid, move_line, type, context=None):
        """ Gets price unit for invoice
        @param move_line: Stock move lines
        @param type: Type of invoice
        @return: The price unit for the move line
        """
        if context is None:
            context = {}

        if type in ('in_invoice', 'in_refund'):
            # Take the user company and pricetype
            context['currency_id'] = move_line.company_id.currency_id.id
            amount_unit = move_line.product_id.price_get('standard_price', context=context)[move_line.product_id.id]
            return amount_unit
        else:


            return move_line.product_id.list_price
        
        #return move_line.product_id.list_price
    def _product_pricelist_price(self, cursor, user, move_line, product_id=None, uom_id=None):
        #print ['id id', move_line, 'sssd']

        pricelist_id = move_line.picking_id.sale_id.pricelist_id.id
        if product_id is None:            
            product_id = move_line.product_id.id
        if uom_id is None:
            uom_id = move_line.product_uom.id            
        partner_id = move_line.picking_id.partner_id.id
        date_order = move_line.picking_id.sale_id.date_order
        price_pricelist = self.pool.get('product.pricelist').price_get(cursor, user, [pricelist_id],
                                                                                 product_id, 1.0, partner_id, 
                                                                                 {'uom': uom_id,
                                                                                  'date': date_order,
                                                                                 })[pricelist_id]
        return price_pricelist
    def _get_price_unit_invoice_galtys(self, cursor, user, move_line, type):
        #ret_super=super(stock_picking, self)._get_price_unit_invoice2(cursor, user, move_line, type)
        print 'CALC', move_line, move_line.sale_line_id.id,  move_line.sale_line_id.move_ids
        #print 'calc', [move_line]
        ret_super=self._get_price_unit_invoice2(cursor, user, move_line, type)
        ret=ret_super
        ret_line=0
        ret_uos=0
        ret_pro_rata=0
        if move_line.sale_line_id and move_line.sale_line_id.product_id.id == move_line.product_id.id:
            ret_line= move_line.sale_line_id.price_unit
            ret=ret_line
            uom_id = move_line.product_id.uom_id.id
            uos_id = move_line.product_id.uos_id and move_line.product_id.uos_id.id or False
            price = move_line.sale_line_id.price_unit
            coeff = move_line.product_id.uos_coeff
            if uom_id != uos_id  and coeff != 0:
                price_unit = price / coeff
                ret_uos=price_unit
                ret=ret_uos
        if move_line.sale_line_id:        
            print 'move_price', move_line
            move_price = self._product_pricelist_price(cursor, user, move_line)
            boms = move_line.sale_line_id.product_id.bom_ids
            if boms:
                if len(boms)==1:
                    prod,ret =  self.pool.get('mrp.bom')._bom_explode(cursor, user, boms[0], 1)
                    bom_components_map = dict( [ (x['product_id'],x['product_qty']) for x in prod ] )
                    move_ids=move_line.sale_line_id.move_ids
                    total=0
                    for move in move_ids:
                        if move_line.sale_line_id.procurement_id.move_id.id != move.id:                            
                            price=self._product_pricelist_price(cursor, user, move)
                            print 'move product trade price', move.product_id, price
                            total += move.product_qty*price
                    print 'total', total
                    pro_rata=move_line.sale_line_id.product_uom_qty*move_line.sale_line_id.price_unit/total
                    ret_pro_rata = move_price * pro_rata
                    ret=ret_pro_rata
                    
        print 'GET PRICE LINE', [move_line.name, ret_super, ret_line, ret_uos, ret_pro_rata,ret, move_line.sale_line_id.id,  move_line.sale_line_id.price_unit, move_line.sale_line_id.discount ]
        #raise
        return ret

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        picking_obj = self.pool.get('stock.picking')
        invoice_line_obj = self.pool.get('account.invoice.line')
        result = super(stock_picking_out, self).action_invoice_create(cr, uid,
                ids, journal_id=journal_id, group=group, type=type,
                context=context)
        for picking in picking_obj.browse(cr, uid, result.keys(), context=context):
            invoice_id = result[picking.id]
            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            taxes=[]
            account_id=[]
            for inv_line in invoice.invoice_line:
                account_id.append( inv_line.account_id.id )
                for t in inv_line.invoice_line_tax_id:
                    if t.id not in taxes:
                        taxes.append(t.id)
            print 'taxes', taxes
            assert len(taxes)==1

            invoice_line = self._prepare_shipping_invoice_line(cr, uid, picking, invoice, context=context)
            if invoice_line:
                invoice_line_obj.create(cr, uid, invoice_line)
                invoice_obj.button_compute(cr, uid, [invoice.id], context=context)
        #for picking in self.browse(cr, uid, ids, context=context):
            current_invoice_untaxed = invoice_obj.browse(cr, uid, invoice_id).amount_untaxed
            print 'current invoice untaxed ', current_invoice_untaxed, [x.amount_untaxed for x in picking.sale_id.invoice_ids]
            invoiced_total = sum( [x.amount_untaxed for x in picking.sale_id.invoice_ids] ) #+ current_invoice_untaxed
            diff_adj = picking.sale_id.amount_untaxed - invoiced_total
            still_2bi=False

            vals = {
                'name': picking.name,
                'origin': picking.name,
                'invoice_id': invoice_id,
                'uos_id': False,
                #'product_id': move_line.product_id.id,
                'account_id': account_id[-1],
                #'price_unit': self._get_price_unit_invoice(cr, uid, move_line, invoice_vals['type']),
                #'discount': self._get_discount_invoice(cr, uid, move_line),
                #'quantity': move_line.product_uos_qty or move_line.product_qty,
                'invoice_line_tax_id': [(6, 0, taxes)],
                #'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
                }
            for p in picking.sale_id.picking_ids:
                if p.id!=picking.id:
                    if p.invoice_state == '2binvoiced':
                        still_2bi=True

            if (not still_2bi) and abs(diff_adj) > 0.0:
                vals['price_unit']=diff_adj
                vals['product_id']=False
                vals['name']='Adj to %s' % picking.sale_id.name
                vals['discount']=0
                vals['quantity']=1
                invoice_line_id = invoice_line_obj.create(cr, uid, vals, context=context)
        return result

    def _get_default_uom(self,cr,uid,c):
        uom_categ, uom_categ_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_categ_kgm')
        return self.pool.get('product.uom').search(cr, uid, [('category_id', '=', uom_categ_id),('factor','=',1)])[0]
    _defaults = {
        'weight_uom_id': lambda self,cr,uid,c: self._get_default_uom(cr,uid,c)
    }



class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _cal_move_weight(self, cr, uid, ids, name, args, context=None):
        res = {}
        uom_obj = self.pool.get('product.uom')
        for move in self.browse(cr, uid, ids, context=context):
            weight = weight_net = 0.00
            if move.product_id.weight > 0.00:
                converted_qty = move.product_qty

                if move.product_uom.id <> move.product_id.uom_id.id:
                    converted_qty = uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, move.product_id.uom_id.id)

                weight = (converted_qty * move.product_id.weight)

                if move.product_id.weight_net > 0.00:
                    weight_net = (converted_qty * move.product_id.weight_net)

            res[move.id] =  {
                            'weight': weight,
                            'weight_net': weight_net,
                            }
        return res

    _columns = {
        'weight': fields.function(_cal_move_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_move_weight'),
        'weight_net': fields.function(_cal_move_weight, type='float', string='Net weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_move_weight'),
        'weight_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True,readonly="1",help="Unit of Measure (Unit of Measure) is the unit of measurement for Weight",),
        }
    def _get_default_uom(self,cr,uid,c):
        uom_categ, uom_categ_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_categ_kgm')
        return self.pool.get('product.uom').search(cr, uid, [('category_id', '=', uom_categ_id),('factor','=',1)])[0]
    _defaults = {
        'weight_uom_id': lambda self,cr,uid,c: self._get_default_uom(cr,uid,c)
    }
stock_move()

class stock_picking_in(osv.osv):
    _inherit = 'stock.picking.in'

    def _cal_weight(self, cr, uid, ids, name, args, context=None):
        return self.pool.get('stock.picking')._cal_weight(cr, uid, ids, name, args, context=context)

    def _get_picking_line(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking')._get_picking_line(cr, uid, ids, context=context)

    _columns = {
        'weight': fields.function(_cal_weight, type='float', string='Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
        'weight_net': fields.function(_cal_weight, type='float', string='Net Weight', digits_compute= dp.get_precision('Stock Weight'), multi='_cal_weight'),
        }
stock_picking_in()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

