# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#   @author Guewen Baconnier
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from report import report_sxw

def report_bom(ns, obj_pool, cr, uid, bom_id):
    product_obj = obj_pool.get('product.product')

    mrp_bom_obj = obj_pool.get('mrp.bom')
    root_bom = mrp_bom_obj.browse(cr, uid, bom_id)

    for bom in sorted(root_bom.bom_lines, key=lambda a: a.product_id.categ_id.id):
        print [bom.product_id.categ_id.name, bom.product_id.name]


def explore_procurement(pool, cr, uid, proc_id, level, out):
    for proc in pool.get('procurement.order').browse(cr, uid, [proc_id]):
        out=out+[(level,proc)]
        if proc.production_id:
            prod=proc.production_id
            for move in prod.move_lines:
                cr.execute("select id from stock_move where move_dest_id=%s", (move.id,))
                move_dest_ids = [x[0] for x in cr.fetchall()]
                if len(move_dest_ids)==1:
                    cr.execute("select id from procurement_order where move_id=%s", (move_dest_ids[0],))
                    proc_ids = [x[0] for x in cr.fetchall()]
                    for proc in pool.get('procurement.order').browse(cr, uid, proc_ids):
                        if proc.production_id:
                            out=explore_procurement(pool, cr, uid, proc.id, level+1, out)
                        else:
                            out=out+[(level,proc)]
    return out
    
    
def report_sale_order(obj_pool, cr, uid, order_id):
    sale_order_obj = obj_pool.get('sale.order')
    sale_order_line_obj = obj_pool.get('sale.order.line')
    product_obj = obj_pool.get('product.product')
    mrp_bom_obj = obj_pool.get('mrp.bom')
    inventory_obj = obj_pool.get('stock.inventory')
    inventory_line_obj = obj_pool.get('stock.inventory.line')
    stock_location_obj = obj_pool.get('stock.location')
    production_order_obj = obj_pool.get('mrp.production')
    ns={}
    for line in sale_order_obj.browse(cr, uid, order_id).order_line:
        v=ns.setdefault(line.id, {} )
        #print line.name, line.product_id
        if not line.procurement_id:
            continue
        cr.execute('select name from mrp_production where move_prod_id=%s'%line.procurement_id.move_id.id)
        ret=cr.fetchall()
        v['prod_order_name']='N/A'
        v['bom_assigned']='No'
        v['line_procurements'] = explore_procurement(obj_pool, cr, uid, line.procurement_id.id, 0, [])
        if ret:
            prod_order_id = ret[0]
            prod_order = production_order_obj.browse(cr, uid, prod_order_id)
            v['prod_order_name'] = ''#prod_order.name
            if prod_order.bom_id:
                bom_ids = [prod_order.bom_id.id]
                v['bom_assigned']='Yes'
            else:
                bom_ids = mrp_bom_obj.search(cr, uid, [('product_id','=',line.product_id.id)])
        else:
            bom_ids = mrp_bom_obj.search(cr, uid, [('product_id','=',line.product_id.id)])
        #print 'BOMs: ', bom_ids
        bom_id = bom_ids
        v['line']=line
        v['bom_ids']=bom_ids
        bom_id = bom_ids[0]
        root_bom = mrp_bom_obj.browse(cr, uid, bom_id)
        v['root_bom']=root_bom
        bom_lines = [bom for bom in sorted(root_bom.bom_lines, key=lambda a: a.product_id.categ_id.id)]
        v['bom_lines'] = bom_lines
        suppliers = {}
        for bom_l in bom_lines:
            xxx = [x.name.name for x in bom_l.product_id.seller_ids]
            #print [(x.id, x.name.name) for x in xxx]
            suppliers[bom_l.id]=xxx
            #print suppliers
            
        v['bom_sellers'] = suppliers
        #for bom in sorted(root_bom.bom_lines, key=lambda a: a.product_id.categ_id.id):
         #   print [bom.product_id.categ_id.name, bom.product_id.name]

        #report_bom(ns,obj_pool, cr, uid, bom_ids[0])

        #print 
        #print
        #for move in line.move_ids:
        #    print "   ", move.name, move.origin, move.state, move.id
        #    for proc in move.procurements:
        #        print "      ", proc.name, proc.state, proc.move_id.name, proc.move_id.id
    return ns



class sale_report_webkit(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(sale_report_webkit, self).__init__(cr, uid, name, context=context)
        order_id = self.localcontext['active_id']
        ns = report_sale_order(self.pool, cr, uid, order_id)
        self.localcontext.update({
            'time': time,
            'ValidTo': self._valid_to,
            'cr':cr,
            'uid': uid,
            'ns': ns,
            })
    def _valid_to(self, prod, cr, uid):
        pl_obj=self.pool.get('product.pricelist.version')
        pl_item=self.pool.get('product.pricelist.item')
        p_ids = pl_item.search(cr, uid, [('product_id','=',prod.id)])
        print 'report parser', p_ids, prod.id, prod.id==61
        if p_ids:
            
            return "".join([x.price_version_id.date_end for x in  pl_item.browse(cr, uid, p_ids)])
        else:
            return ''
   
report_sxw.report_sxw('report.sale.order.availability_report',
                      'sale.order',
                       parser=sale_report_webkit)

report_sxw.report_sxw('report.sale.order.costing_report',
                      'sale.order',
                       parser=sale_report_webkit)

report_sxw.report_sxw('report.sale.order.vendor_report',
                      'sale.order',
                       parser=sale_report_webkit)
