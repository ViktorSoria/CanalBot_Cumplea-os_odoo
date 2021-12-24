odoo.define("website_customs.stock_product_popup", function (require) {
    "use strict";
    var Dialog = require("web.Dialog");
    var publicWidget = require("web.public.widget");
    var ajax = require('web.ajax');
    var core = require('web.core');
    var session = require('web.session');
    var QWeb = core.qweb;
    var xml_load = ajax.loadXML(
        '/website_customs/static/src/xml/web.xml',
        QWeb
    );

    publicWidget.registry.DynamicProductPopup = publicWidget.Widget.extend({
        selector: "#stock_available",
        events: {
            "click": "_onClick",
        },
        _onClick: async function (ev) {
            if(!session.user_id){
                this.do_warn('Inicie sesión', "Inicie sesión para consultar las existrencias", false);
                return;
            }
            var self = this;
            ev.preventDefault();
            let data = await $.get(ev.currentTarget.href);
            let el = $("<div><div/>");
            el.html(data);
            let modalContent = $("#product_detail", el);
            let websitesale = new publicWidget.registry.WebsiteSale(self);
            websitesale.setElement(modalContent);

            modalContent.find("form").remove();
            modalContent.find("#product_details p").remove();
            modalContent.find(".carousel-control-prev").remove();
            modalContent.find(".carousel-control-next").remove();
            modalContent.find(".carousel-indicators").remove();
            let combination = {};
            combination.stock = await self._rpc({
                model: 'product.product',
                method: 'available_qty',
                args: [parseInt($(".product_id").val()),false,true],
            });
            let $message = $(QWeb.render(
                'website_customs.stock_product_available',
                combination
            ));
            modalContent.find("#product_attributes_simple").html($message);
            let dialog = new Dialog(self, {
                size: "extra-large",
                backdrop: true,
                dialogClass: "p-3",
                $content: modalContent,
                technical: false,
                renderHeader: false,
                renderFooter: false,
            });
            dialog.open();
        },
    });
});

