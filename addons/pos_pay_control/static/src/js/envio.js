odoo.define("pos_pay_control.SendOrder", function (require) {
    "use strict";
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class SendOrder extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('onClick', this.onClick);
        }

        async onClick(event){
            var sessions = await this.rpc({
                model: 'pos.session',
                method: 'search_read',
                domain: [['state','=','opened'],['config_id','!=',this.env.pos.config_id]],
                fields: ['config_id','name']
            });
            const {confirmed, payload: payload} = await this.showPopup("Buttonsend", {'sessions':sessions});
            if(confirmed){
                let order = this.env.pos.db.get_unpaid_orders().find(e=> e.name == payload.order);
                let data = JSON.stringify({
                    'unpaid_orders': [order],
                    'session_id':    payload.value,
                    'date':          (new Date()).toUTCString(),
                    'version':       this.env.pos.version.server_version_info,
                },null,2);
                await this.rpc({
                            model: 'pos.session',
                            method: 'envia',
                            args: [parseInt(payload.value),data],
                        }).then(aut => {
                            if(aut){
                                this.env.pos.get_order().destroy({'reason':'abandon'});
                                this.showPopup("ConfirmPopup",{
                                    title: "Orden Enviada",
                                    body: "El pedido fue enviado con exito",
                                })
                            }else{
                                this.showPopup("ErrorPopup",{
                                    title: "Envio Fallido",
                                    body: "La orden no pudo ser enviada, comunicate con un Administrador",
                                })
                            }
                });
            }
        }
    }

    SendOrder.template = 'SendOrder';

    Registries.Component.add(SendOrder);

    return SendOrder;
});
