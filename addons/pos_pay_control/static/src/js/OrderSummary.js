odoo.define('pos_pay_control.OrderSummary', function (require) {
    'use strict';
    const OrderSummary = require('point_of_sale.OrderSummary');
    const Registries = require('point_of_sale.Registries');

    const OrderSummary2 = (OrderSummary) =>
        class extends OrderSummary {
        get puntos() {
            let puntos = this.env.pos.get_order().get_total_with_tax()*0.04; 
            return this.env.pos.format_currency_no_symbol(puntos);
        }
    }


    Registries.Component.extend(OrderSummary, OrderSummary2);
});