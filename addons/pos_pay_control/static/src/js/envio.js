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
                domain: [['state','=','opened'],['config_id','!=',this.env.pos.config_id],['config_id.default_location_src_id','=',this.env.pos.config.default_location_src_id[0]]],
                fields: ['config_id','name']
            });
            const {confirmed, payload: payload} = await this.showPopup("Buttonsend", {'sessions':sessions});
            if(confirmed){
                let order = this.env.pos.db.get_unpaid_orders().find(e=> e.name == payload.order);
                if(!payload.value){
                    this.showPopup("ErrorPopup",{
                                    title: "Envio Fallido",
                                    body: "La orden no pudo ser enviada, seleccione una caja destino.",
                                })
                    return
                }
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
                                let order = this.env.pos.get_order();
                                //nueva orden
                                let new_order = this.env.pos.add_new_order();
                                this.env.pos.set_order(new_order);
                                if(payload.print){
                                    this.showScreen('PrintEnvScreen', { order: order });
                                }else{
                                    this.showScreen('ProductScreen');
                                    this.showPopup("ConfirmPopup",{
                                    title: "Orden Enviada",
                                    body: "El pedido fue enviado con exito",
                                    });
                                }
                                order.destroy({'reason':'abandon'});
                            }else{
                                this.showPopup("ErrorPopup",{
                                    title: "Envio Fallido",
                                    body: "La orden no pudo ser enviada, comunicate con un Administrador",
                                });
                            }
                });
            }
        }
    }

    SendOrder.template = 'SendOrder';

    Registries.Component.add(SendOrder);

    return SendOrder;
});
