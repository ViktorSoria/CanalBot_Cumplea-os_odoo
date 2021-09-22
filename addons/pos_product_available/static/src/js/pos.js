odoo.define("pos_product_available.PosModel", function (require) {
    "use strict";

    var exports = require("point_of_sale.models");
    const ProductItem = require("point_of_sale.ProductItem");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require('web.custom_hooks');
    const {Gui} = require('point_of_sale.Gui');
    const Registries = require('point_of_sale.Registries');
    var field_utils = require("web.field_utils");

    exports.load_fields("product.product", ["qty_available", "type",'display_name']);
    var models = exports.PosModel.prototype.models;
    models.find(e=>e.model=="product.product").context = function(self){ return { display_default_code: true, location:self.config.default_location_src_id[0]}; };
    const ProductItem2 = (ProductItem) =>
        class extends ProductItem {
            constructor() {
                super(...arguments);
                useListener('click-available', this._clickProductAvailable);
            }
            format_float_value(val) {
                var value = parseFloat(val);
                value = field_utils.format.float(value, {digits: [69, 3]});
                return String(parseFloat(value));
            }

            get product_type() {
                return this.props.product.type;
            }

            get rounded_qty() {
                return this.format_float_value(this.props.product.qty_available);
            }

            get price() {
                const formattedUnitPrice = this.env.pos.format_currency(
                    this.props.product.get_price(this.pricelist, 1),
                    'Product Price'
                );
                return formattedUnitPrice;
            }

            async _clickProductAvailable(event) {
                console.log(this.props.product);
                var stock = await this.rpc({
                    model: 'product.product',
                    method: 'available_qty',
                    args: [this.props.product.id],
                });
                Gui.showPopup("StockProductPopup", {'stock': stock});
            }
        }
        const ProductScreen2 = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                this.inicial();
            }
            inicial() {
                const self = this;
                async function loop(limit,offset) {
                    if(limit===0){
                        setTimeout(()=>{loop(5000,0);}, 60000);
                    }else{
                        let newof = offset;
                        let tam = _.size(self.env.pos.db.product_by_id);
                        let tiempo = 5000;
                        if(newof>tam){newof=0;}
                        try {
                            await self.recompute_quantity(limit,newof);
                            newof += 5000;
                        } catch (error) {
                            console.log(error);
                            tiempo = 60000;
                        }
                        setTimeout(()=>{loop(5000,newof);}, tiempo);
                    }
                }
                loop(0,0);
            }
            async recompute_quantity(limit,offset){
                let location = this.env.pos.config.default_location_src_id[0];
                let products = await this.rpc({
                    model: 'product.product',
                    method: 'search_read',
                    fields: ["qty_available"],
                    context: {location:location},
                    domain:[['type','=','product'],['available_in_pos','=',true]],
                    limit: limit,
                    offset: offset,
                    orderBy: _.map(['id'], function (name) { return {name: name}; }),
                });
                let p;
                products.forEach(item => {
                    p = this.env.pos.db.product_by_id[item.id];
                    if(p){
                        p.qty_available = item.qty_available;
                    }
                });
                this.render();
            }

        }



    Registries.Component.extend(ProductItem, ProductItem2);
    Registries.Component.extend(ProductScreen, ProductScreen2);

    return ProductItem;
});
