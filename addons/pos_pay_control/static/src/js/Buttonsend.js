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
        async getPayload() {
            return {value:this.state.inputValue,order:this.env.pos.get_order().name};
        }
        async confirmAndPrint(event){
            let pay = await this.getPayload();
            pay.print = true;
            this.props.resolve({ confirmed: true, payload: pay});
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