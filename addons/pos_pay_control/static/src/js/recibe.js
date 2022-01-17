odoo.define("pos_pay_control.ResOrder", function (require) {
    "use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const Chrome = require('point_of_sale.Chrome');
    const {useListener} = require('web.custom_hooks');

    class ResOrder extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('onClick', this.onClick);
            this._start();
        }
        _start() {
            const self = this;
            async function loop() {
                if (self.env && self.env.pos && self.env.pos.pos_session) {
                    try {
                        self.ReceiveOrders();
                    } catch (error) {
                        console.log(error);
                    }
                }
                setTimeout(loop, 10000);
            }
            loop();
        }
        async ReceiveOrders() {
            var orders = await this.rpc({
                model: 'pos.session',
                method: 'recibe',
                args: [this.env.pos.pos_session.id]
            });
            if (orders && orders.length>0) {
                orders.forEach(order => {
                    this.env.pos.import_orders(order);
                });
                let eti = $("div[badge]");
                eti[0].setAttribute('badge', this.env.pos.get_order_list().length);
                this.playSound('/pos_pay_control/static/src/sound/rin.wav');
                return orders
            }
            return orders
        }
        async SeeOrders(){
            return await this.rpc({
                model: 'pos.session',
                method: 'ver',
                args: [this.env.pos.pos_session.id]
            });
        }
        async onClick(event) {
            let orders = await this.SeeOrders();
            await this.showPopup("Buttonreceive", {'orders':orders});
        }

    }

    ResOrder.template = 'ResOrder';

    Registries.Component.add(ResOrder);

    const Chrome2 = (Chrome) =>
        class extends Chrome {
            _onPlaySound({detail: name}) {
                let src;
                if (name === 'error') {
                    src = "/point_of_sale/static/src/sounds/error.wav";
                } else if (name === 'bell') {
                    src = "/point_of_sale/static/src/sounds/bell.wav";
                } else {
                    src = name;
                }
                this.state.sound.src = src;
            }
        }

    Registries.Component.extend(Chrome, Chrome2);

    return ResOrder;
});
