odoo.define('pos_product_available.Buttonreceive', function (require) {
    'use strict';
    console.log(" ==== Si carga el js de jeho ====");
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useState, useRef } = owl.hooks;
    class Buttonreceive extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: '',name: ''});
            this.inputRef = useRef('session');
        }
        selection(event){
            this.state.name = event.target.getAttribute('sname');
            this.state.inputValue = event.target.getAttribute('orderid');
        }
        async GetOrder() {
            var orders = await this.rpc({
                model: 'pos.session',
                method: 'recibe',
                args: [this.env.pos.pos_session.id, this.state.inputValue]
            });
            if (orders && orders.length>0) {
                orders.forEach(order => {
                    this.env.pos.import_orders(order);
                });
                let eti = $("div[badge]");
                eti[0].setAttribute('badge', this.env.pos.get_order_list().length);
                this.playSound('/pos_pay_control/static/src/sound/rin.wav');
            }
            this.trigger('close-popup');
            return orders
        }
    }

    //Create products popup
    Buttonreceive.template = 'Buttonreceive';
    Buttonreceive.defaultProps = {
        confirmText: 'Recibir',
        cancelText: 'Cancelar',
        title: 'Pedidos Disponibles',
        body: '',
    };
    Registries.Component.add(Buttonreceive);
    return Buttonreceive;
});