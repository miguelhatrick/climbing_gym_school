# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, models, fields, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ResProductChangeQuantity(models.TransientModel):
    _name = "stock.change.product.qty_custom"
    _inherit = "stock.change.product.qty"

    def change_product_qty(self):
        """ Changes the Product Quantity by making a Physical Inventory. """
        Inventory = self.env['stock.inventory']
        for wizard in self:
            product = wizard.product_id.with_context(location=wizard.location_id.id)
            line_data = wizard._action_start_line()

            if wizard.product_id.id:
                inventory_filter = 'product'
            else:
                inventory_filter = 'none'
            inventory = Inventory.create({
                'name': _('INV: %s') % tools.ustr(wizard.product_id.display_name),
                'filter': inventory_filter,
                'product_id': wizard.product_id.id,
                'location_id': wizard.location_id.id,
                'line_ids': [(0, 0, line_data)],

                # TODO: I HAD TO ADD THIS CLASS AND THIS PARAMETER TO MAKE IT WORK WHEN CONFIRMING A SO
                'partner_id': None
            })
            inventory.action_validate()
        return {'type': 'ir.actions.act_window_close'}
