odoo.define("pos_pay_control.ResOrder", function (require) {
    "use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class ResOrder extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('onClick', this.onClick);
        }

        async onClick(event){
            var orders = await this.rpc({
                model: 'pos.session',
                method: 'recibe',
                args: [this.env.pos.pos_session.id]
            });
            orders.forEach(order=>{
                this.env.pos.import_orders(order);
            });
        }
    }

    ResOrder.template = 'ResOrder';

    Registries.Component.add(ResOrder);

    return ResOrder;
});
