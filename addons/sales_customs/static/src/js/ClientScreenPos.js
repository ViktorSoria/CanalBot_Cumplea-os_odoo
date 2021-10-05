odoo.define('sales_customs.ClientDetailsEdit', function (require) {
"use strict";

    console.log(" ==== Si carga el js ==== 6");
    const { _t } = require('web.core');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');

    const PosPartnerScreen = (ClientDetailsEdit) =>  class extends ClientDetailsEdit {
        captureChange(event) {
            this.changes[event.target.name] = event.target.value;
        }
        saveChanges() {
            let processedChanges = {};
            for (let [key, value] of Object.entries(this.changes)) {
                if (this.intFields.includes(key)) {
                    processedChanges[key] = parseInt(value) || false;
                } else {
                    processedChanges[key] = value;
                }
            }
            if ((!this.props.partner.name && !processedChanges.name) ||
                processedChanges.name === '' ){
                return this.showPopup('ErrorPopup', {
                  title: _t('A Customer Name Is Required'),
                });
            }
            /* Check if phone */
            if ((!this.props.partner.phone && !processedChanges.phone) ||
                processedChanges.phone === ''){
                return this.showPopup('ErrorPopup', {
                    title: _t('Se requiere un teléfono de cliente'),
                });
            }
            processedChanges.id = this.props.partner.id || false;
            this.trigger('save-changes', { processedChanges });
        }


    }
    Registries.Component.extend(ClientDetailsEdit, PosPartnerScreen);
});