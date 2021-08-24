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
    }

    //Create products popup
    Buttonsend.template = 'Buttonsend';
    Buttonsend.defaultProps = {
        confirmText: 'Enviar',
        cancelText: 'Cancelar',
        title: 'Equipos Disponibles',
        body: '',
    };
    Registries.Component.add(Buttonsend);
    return Buttonsend;
});