odoo.define('pos_product_available.Buttonsend', function (require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useState, useRef } = owl.hooks;
    class Buttonsend extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: '',name: ''});
            this.inputRef = useRef('session');
        }
        selection(event){
            this.state.name = event.target.getAttribute('sname');
            this.state.inputValue = event.target.getAttribute('session-id');
        }
        getPayload() {
            return {value:this.state.inputValue,order:this.env.pos.get_order().name};
        }
        async confirmAndPrint(event){
            this.printReceiptC();
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            this.trigger('close-popup');
        }

        async printReceiptC(){
            console.log("IMPRIMIENDO EL TICKET... ");
            console.log(this.env);
            if (this.env.pos.proxy.printer) {
                const printResult = await this.env.pos.proxy.printer.print_receipt(this.orderReceipt.el.outerHTML);
                if (printResult.successful) {
                    return true;
                } else {
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: printResult.message.title,
                        body: 'Do you want to print using the web printer?',
                    });
                    if (confirmed) {
                        // We want to call the _printWeb when the popup is fully gone
                        // from the screen which happens after the next animation frame.
                        await nextFrame();
                        return await this._printWeb();
                    }
                    return false;
                }
            } else {
                return await this._printWeb();
            }
        }

        async _printWeb() {
            try {
                const isPrinted = document.execCommand('print', false, null);
                if (!isPrinted) window.print();
                return true;
            } catch (err) {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Printing is not supported on some browsers'),
                    body: this.env._t(
                        'Printing is not supported on some browsers due to no default printing protocol ' +
                            'is available. It is possible to print your tickets by making use of an IoT Box.'
                    ),
                });
                return false;
            }
        }

        async confirm() {
            console.log("___ ASYNC CONFIRM ");
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            this.trigger('close-popup');
        }
    }

    //Create products popup
    Buttonsend.template = 'Buttonsend';
    Buttonsend.defaultProps = {
        confirmText: 'Enviar',
        printConfirmText: 'Imprimir y Enviar',
        cancelText: 'Cancelar',
        title: 'Equipos Disponibles',
        body: '',
    };
    Registries.Component.add(Buttonsend);
    return Buttonsend;
});