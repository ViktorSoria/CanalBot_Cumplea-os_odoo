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
        valida_lineas(){
            let valido = true;
            let orden = this.env.pos.get_order();
            orden.orderlines.forEach(function(line){
                if(line.quantity <= 0 || line.price <= 0.01){
                    valido = false;
                    return;
                }
            });
            return valido;
        }
        async comprueba_stock(){
            let lines = this.env.pos.get_order().get_orderlines();
            let productos = [];
            for (var i = 0; i < lines.length; i++) {
                productos[i] = [lines[i].product.id,lines[i].quantity];
            }
            let nueva_cantidades = await this.rpc({
                model: 'product.product',
                method: 'validate_stock',
                args: [productos,this.env.pos.config.default_location_src_id[0]],
            });
            if(nueva_cantidades){
                let l;
                for (var i = 0; i < nueva_cantidades.length; i++) {
                    l = lines.find(l => l.product.id===nueva_cantidades[i][0]);
                    l.set_quantity(nueva_cantidades[i][1]);
                    l.product.qty_available = nueva_cantidades[i][1];
                }
                return false;
            }
            else{
                return true;
            }
        }

        async onClick(event){
            var self = this;
            var order_is_correct = true;
            this.env.pos.db.cache.unpaid_orders.forEach(function(order){
                order.data.lines.forEach(function(line){
                    var linea = line[2];
                    if(linea.qty <= 0){
                         self.showPopup('ErrorPopup', {
                            title: "Error de cantidad",
                            body: "No puedes enviar cero productos.",
                        });
                        order_is_correct = false;
                    }
                    if(linea.price_unit <= 0.01){
                        self.showPopup('ErrorPopup', {
                            title: "Error de precio",
                            body: "No puedes enviar productos con precio menor o igual a cero.",
                        });
                        order_is_correct = false;
                    }
                });
            });
            if(order_is_correct == false){
            let valido = this.valida_lineas();
            if(!valido){
                this.showPopup('ErrorPopup', {
                    title: "Error de precio",
                    body: "No puedes enviar productos sin precio o con precio menor o igual a cero.",
                });
                return;
            }}
            let valida_stock = await this.comprueba_stock();
            if(!valida_stock){
                this.showPopup('ErrorPopup', {
                    title: "Error de existencias",
                    body: "El stock de algunos productos fue actualizado, no cuentas con la cantidad suficiente, el carrito ha sido actualizado.",
                });
                return;
            }
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
