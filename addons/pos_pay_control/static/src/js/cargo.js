odoo.define("pos_pay_control.cargo", function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen')
    const {useListener} = require('web.custom_hooks');
    var exports = require("point_of_sale.models");
    var models = exports.PosModel.prototype.models;

    exports.load_fields("pos.payment.method", ["cargo", "es_puntos"]);
    exports.load_fields("res.partner", ["acomula_puntos", 'puntos']);


    models.find(e => e.model == "product.product").domain = function (self) {
        var domain = ['&', '&', ['sale_ok', '=', true], ['available_in_pos', '=', true], '|', ['company_id', '=', self.config.company_id[0]], ['company_id', '=', false]];
        if (self.config.limit_categories && self.config.iface_available_categ_ids.length) {
            domain.unshift('&');
            domain.push(['pos_categ_id', 'in', self.config.iface_available_categ_ids]);
        }
        if (self.config.iface_tipproduct) {
            domain.unshift(['id', '=', self.config.tip_product_id[0]]);
            domain.unshift('|');
        }
        if (self.config.producto_cargo) {
            domain.unshift(['id', '=', self.config.producto_cargo[0]]);
            domain.unshift('|');
        }
        return domain;
    }

    const PaymentScreenControl = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor(props) {
                super(...arguments);
                useListener('pay_electronic', this.pay_electronic);
            }

            async validateOrder(isForceValidate) {
                let order = this.currentOrder;
                let lines = order.get_paymentlines();
                let method = lines.find(l => l.payment_method.es_puntos)
                if (method) {
                    if (method.amount > this.puntos) {
                        this.showPopup("ErrorPopup", {
                            title: "Pago Incorrecto",
                            body: "NO puede usar mas puntos para pagar de los que tiene el cliente seleccionado",
                        });
                        return;
                    }
                }
                if(order.is_to_invoice() && (!order.get_client() || !order.get_client().vat)){
                    this.showPopup("ErrorPopup", {
                            title: "Falta RFC",
                            body: "Agregue cliente con RFC valido antes de finalizar el pedido",
                        });
                        return;
                }
                if (await this.verify_price_list()) {
                    super.validateOrder(...arguments);
                    let acomulados = 0;
                    let usado = 0;
                    lines.forEach( l=>{
                       if(l.payment_method.es_puntos){
                           usado += l.amount
                       }else{
                           acomulados += l.amount
                       }
                    });
                    let cliente = this.env.pos.get_client();
                    if(cliente){
                        let puntos = acomulados * 0.04 - usado;
                        cliente.puntos = cliente.puntos + puntos;
                        order.puntos = acomulados * 0.04;
                    }
                }
            }

            pay_electronic(event) {
                let method = this.env.pos.payment_methods.find(e => e.es_puntos);
                let lines = this.currentOrder.get_paymentlines();
                if (lines.find(l => l.payment_method.id === method.id)) {
                    return;
                }
                this.addNewPaymentLine({detail: method});
                this.currentOrder.selected_paymentline.set_amount(this.puntos);
            }

            get puntos() {
                let cliente = this.env.pos.get_client();
                if (cliente && cliente.acomula_puntos) {
                    return this.env.pos.format_currency_no_symbol(cliente.puntos);
                } else {
                    return false
                }
            }

            deletePaymentLine(event) {
                super.deletePaymentLine(...arguments);
                let order = this.currentOrder;
                let product = this.env.pos.config.producto_cargo[0];
                let line = order.get_orderlines().find(line => line.product.id === product);
                if (line) {
                    order.remove_orderline(line);
                }
            }

            addNewPaymentLine({detail: paymentMethod}) {
                let cargo = parseFloat(paymentMethod.cargo);
                if (cargo > 0) {
                    let product = this.env.pos.db.get_product_by_id(this.env.pos.config.producto_cargo[0])
                    let total = this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied();
                    this.currentOrder.add_product(product, {
                        quantity: 1,
                        price: total * cargo / 100,
                        lst_price: total * cargo / 100,
                        extras: {price_manually_set: true},
                    });
                }
                return super.addNewPaymentLine(...arguments);
            }

            async verify_price_list() {
                let selectedPricelist = this.currentOrder.pricelist;
                if (selectedPricelist.autorizacion) {
                    const {confirmed, payload} = await this.showPopup(
                        'NumberPopup',
                        {
                            title: "Ingrese Autorización",
                            startingValue: 0,
                            isPassword: true,
                        }
                    );
                    if (confirmed) {
                        let aut = await this.rpc({
                            model: 'res.users',
                            method: 'autorize',
                            args: [null, payload],
                        });
                        if (aut) {
                            return true;
                        } else {
                            this.showPopup('ErrorPopup', {
                                title: 'Permiso Denegado',
                                body: 'El código de autorización no es valido',
                            });
                        }
                    } else {
                        return false;
                    }

                } else {
                    return true;
                }
            }
            async _finalizeValidation() {
                if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                    this.env.pos.proxy.printer.open_cashbox();
                }

                this.currentOrder.initialize_validation_date();
                this.currentOrder.finalized = true;

                let syncedOrderBackendIds = [];

                try {
                    if (this.currentOrder.is_to_invoice()) {
                        this.currentOrder.to_invoice = $("#method").val();
                        syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                            this.currentOrder
                        );
                        if(syncedOrderBackendIds){
                            this.currentOrder.cfdi_vals = await this._get_cfdi_vals(syncedOrderBackendIds);
                        }
                    } else {
                        syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                    }
                } catch (error) {
                    this.error = true;
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        await this._handlePushOrderError(error);
                    }
                }
                if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                    const result = await this._postPushOrderResolve(
                        this.currentOrder,
                        syncedOrderBackendIds
                    );
                    if (!result) {
                        await this.showPopup('ErrorPopup', {
                            title: 'Error: no internet connection.',
                            body: error,
                        });
                    }
                }

                this.showScreen(this.nextScreen);

                // If we succeeded in syncing the current order, and
                // there are still other orders that are left unsynced,
                // we ask the user if he is willing to wait and sync them.
                if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Remaining unsynced orders'),
                        body: this.env._t(
                            'There are unsynced orders. Do you want to sync these orders?'
                        ),
                    });
                    if (confirmed) {
                        // NOTE: Not yet sure if this should be awaited or not.
                        // If awaited, some operations like changing screen
                        // might not work.
                        this.env.pos.push_orders();
                    }
                }
            }

            async _get_cfdi_vals(id){
                let vals = await this.rpc({
                            model: 'pos.order',
                            method: 'get_cfdi_vals',
                            args: [id],
                        });
                if(vals){
                    return JSON.parse(vals);
                }
                else{
                    return false
                }
            }
        }

    Registries.Component.extend(PaymentScreen, PaymentScreenControl);
})
;
