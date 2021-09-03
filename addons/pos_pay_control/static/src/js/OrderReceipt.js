odoo.define('pos_pay_control.OrderReceipt', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');

    const OrderReceipt2 = (OrderReceipt) =>
        class extends OrderReceipt {
        get cliente() {
            return this.props.order.get_client();
        }
        get puntos() {
            return this.props.order.puntos;
        }
        get ubicacion() {
            return this.env.pos.config.datos_ubicacion.split("/");
        }
        get facturacion(){
            console.log(this._receiptEnv);
            return 0
        }
    }


    Registries.Component.extend(OrderReceipt, OrderReceipt2);
});
