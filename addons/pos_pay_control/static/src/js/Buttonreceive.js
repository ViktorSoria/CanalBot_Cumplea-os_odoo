odoo.define('pos_product_available.Buttonreceive', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const OrderFetcher = require('point_of_sale.OrderFetcher');
    const { useState, useRef } = owl.hooks;
    class Buttonreceive extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: '',name: '', pagado: false});
            this.inputRef = useRef('session');
        }
        selection(event){
            this.state.name = event.target.getAttribute('sname');
            this.state.inputValue = event.target.getAttribute('orderid');
            this.state.pagado = event.target.getAttribute('orderp');
        }
        exist_order(name){
            let orders = OrderFetcher.get();
            let new_order = false;
            orders.forEach(o => {
                if(name === o.name){
                    new_order = o;
                }
            });
            return new_order;
        }
        async GetOrder() {
            if(this.state.pagado==='1'){
                let name = this.state.name;
                this.showScreen('OrderManagementScreen');
                setTimeout(() => {
                    let order = this.exist_order(name);
                    if(order){
                        let targ = 'div.name:contains('+name+')';
                        $(targ).click();
                    }
                }, 500);
                this.trigger('close-popup');
                return
            }
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