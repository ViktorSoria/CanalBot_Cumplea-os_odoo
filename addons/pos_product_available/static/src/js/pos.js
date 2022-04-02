odoo.define("pos_product_available.PosModel", function (require) {
    "use strict";

    var exports = require("point_of_sale.models");
    const ProductItem = require("point_of_sale.ProductItem");
    const CategoryButton = require("point_of_sale.CategoryButton");
    const Chrome = require('point_of_sale.Chrome');
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require('web.custom_hooks');
    const {Gui} = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    var field_utils = require("web.field_utils");

    exports.load_fields("product.product", ["qty_available", "type",'display_name']);
    var models = exports.PosModel.prototype.models;

    models.find(e=>e.model=="product.product").context = function(self){ return { global:true, display_default_code: true, location:self.config.default_location_src_id[0]}; };
    models.find(e=>e.model=="product.pricelist.item").context = function(self){ return { global:true};};

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
                var stock = await this.rpc({
                    model: 'product.product',
                    method: 'available_qty',
                    args: [this.props.product.id],
                });
                Gui.showPopup("StockProductPopup", {'stock': stock});
            }
            get imageUrl() {
                const product = this.props.product;
                // return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
                return 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAAsTAAALEwEAmpwYAAAXcElEQVR4nO3de3gdZZ0H8O9vzjlpA0mLZSnKRZ4CFSHYNOfMSUIoSsAbInJ5NMpN0VXwgq4rKi7iouttXei6wiKwuC48Cmhku8ICykUCuzUmOTMnROgKy9LiculytWxD0+acmd/+kVO20lvOnJl5Z3K+n+fhv8z7fhv6fjtnzsw7ABERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERFR+ojpALRjruu+X1VvAJAxnaVBnoicWSgUfmo6CG2PBZBAc2jxb8USSCgWQMLMwcW/FUsggVgACTKHF/9WLIGEYQEkRBMs/q1YAgnCAkiAJlr8W7EEEoIFYFgTLv6tWAIJwAIwqIkX/1YsAcNYAIZw8b+CJWAQC8AALv7tsAQMYQHEjIt/p1gCBrAAYsTFv1ssgZixAGLCxT9rLIEYsQBiwMVfN5ZATFgAEePiD4wlEAMWQIS4+BvGEogYCyAiXPyhYQlEiAUQAS7+0LEEIsICCBkXf2RYAhFgAYSIiz9yLIGQsQBCwsUfG5ZAiFgAIeDijx1LICQsgAZx8RvDEggBC6ABXPzGsQQaNKcKwHGcPTKZzOJKpbKniET9Z+sRkWvAxW+ap6rnARiNchJV1Vwu97Lnec/atr0pyrnilNoCKJfL+/m+fyyAXgDLAbwRwD5GQ1GzeA7AwwAeADBiWdZ9+Xz+acOZAklVAYyOji7JZDJnATgNM4ueKCkeALDK87wf9/T0rDMdZrZSUQCu6x6nqhcAOAEpyUxNSwH8QkRWFgqFe02H2Z1EL6ZyuWyr6mWq+hbTWYjqJSL3i8jn8/m8YzrLziSyAIaGhua3tbV9W0Q+A8AynYeoAb6qXj45OfkX/f39m02HebXEFYDruoeq6ioAbzKdhShED4rIaYVC4b9MB9lWogqgXC4f5fv+vwLY23QWogi8YFnWSfl8/jemg2yVmAKoLf67ALSZzkIUoUnLst6elBJIRAGMj48v9TxvBMAi01mIYvBiJpPp7erqetR0EOMX2IaHh1s9z1sFLn5qHos8z1s1PDzcajqI8QLI5XLfAnCk6RxEMTuy9nffKKMfAVzXXaaqZfB+empOnojkC4XCb00FMHoGoKrfBhc/Na9MbQ0YY+wMoPav/4Sp+YmSQkQ6TZ0FGDsDUNWPm5qbKElMrgUjZwBDQ0PZ9vb2Z8Ar/0QA8OLGjRv37e/vr8Y9sZEzgPb29mPAxU+01aLamoidqY8AxxmalyipjKwJIwWgqkeZmJcoqUytCSMFICLLTMxLlFSm1kTsBTAyMrIA3LuP6NX2qa2NWMVeAJZlHRj3nERpYGJtxF4A2WyWz/oT7YCJtRF7AXiex+f9iXbAxNrIxj0hgJyBOWnGCwCeUtXnRGSjqm4BABGZB2DrtZkDAexlMGMzi31txF4AMbyxh2b8HsD9AEZEZFxVf2fb9kuzOXB8fHyvSqVyhIjkRaQXwLEA9o8wK8HM2jBxBkDRGQfwU1X9ebFYfCToIF1dXRsADNf++3sAcBznTQBOAfABAEeEkJUSgAWQfpsAXAfgatu2H4xqktrYDwL4eqlU6haRTwI4HUBLVHNS9FgA6fWSqv5dpVK5vK+v78U4Jy4Wi2MAxsrl8kWq+nlV/QSA+XFmoHAY3xKM6lYFcLnneYcUi8Wvxr34t5XP558uFAqfq1arSwHcYCoHBcczgHQZA/DRKE/1g+jt7X0SwFljY2PXWpZ1LYClpjPR7PAMIB2qqnrx2rVr+5K2+LfV3d19//T0dCeA75vOQrPDM4DkWw9goFgsrjYdZDb6+vqmAHyqVCrdKyLXgS96STSeASRbOZvNFm3bTsXi31axWPzn2iOuvzedhXaOBZBcd7e2tr5l+fLlT5kOElSxWHwIwFGY+fqQEogFkEy3LVy48KSOjo5J00EaZdv2+unp6WMxc5MSJQwLIGFU9VcLFy5879KlS7eYzhKWvr6+Fz3PexuANaaz0B9jASTLA1u2bDl1Li3+rXp6el7wff8EAE+bzkL/jwWQHM/6vv+eFStWbDQdJCrd3d1PiMh7AGw2nYVm8GvAZPABfKC7u/sJ00GioKrW+Pj4Ct/3T1bVE8DbhhODBZAM37Jte8h0iLCVSqUuEfmQ67rvB/Ba03loeywA8yY2btz4NdMhwjI0NDS/ra3tjNrTggXTeWjXWABm+ap6rolXQoXNcZyFqnq+iHwGwGLTeWh2WAAGich1tm2Pmc7RiImJiT2np6c/C+ACEXmN6TxUHxaAOVMi8hXTIYJSVXEc58OVSuUbIvI603koGBaAOVfl8/lUfideLpc7Xde9RkR6TGehxrAAzJi2LGul6RD1chwnp6pf9X3/i+DfnTmB/xPNuDlt//qXy+UjfN+/QUSWm85C4eGdgAaIyNWmM9TDdd1zfN8vAeDin2N4BhC/dYVC4d9Nh5gNx3FyInKFqp5nOgtFgwUQv0HTAWZjeHh4kYisUtW3xDjtRlV9CMDDIrJOVZ8C8Hwmk9lQrVanstmsep5nqWqrZVmvEZF9fN/fH8AhlmUdpqodAPaIMW/qsQBi5vv+raYz7I7jOK8HcKeqvjHiqZ4Rkbt837/P9/3V3d3dj4qIBh1MVS3XdTsArMDM24zeBoD3JuwCCyBeLz3++OOjpkPsSqlUOgzAPQAOiGiK9QBuEpGf5fP50UYW/KuJiI+Z3YceBHDV4OBgZsmSJceIyACA9wNYFNZccwULIEYiMjwwMOCZzrEzruserqpDAPaNYPg7ReTKxx577I64fge1ee4DcN+jjz765xs2bDhVRM4HcHQc86cBCyBGqjpiOsPOuK57qKr+CuEufh8z7yr8Vm1/QGNqm6z8BMBPXNftVdWLAZxoMlMSsABipKoPmM6wI+VyeT/f9+8BEOYtvXeo6oWmF/6OFAqFEQDvLpfLR6nqZaraZzqTKSyAGPm+/7DpDK+2Zs2atqmpqTsAHBTSkI+LyKcLhcJtIY0XmXw+/xsAR5dKpbNFZCWAfUxnihtvBIqP39bW9rjpENtSVWtqauomAJ1hDAfgilwud2QaFv+2isXijzzPOxzATaazxI1nAPF5vqOjY9p0iG25rvtVAO8OYahnReSDhULhzhDGMqKnp+cFAGe4rnu7ql6NJnmjEc8A4vO86QDbKpVKJwC4OIShRizL6krz4t9WoVC4AUARQOI+rkWBBRCfxOz2OzY29loRuR6ANDjUjQsXLjw2bQ827Y5t2w8D6AVwt+ksUWMBxCcx235lMpkfosELXqp6qW3bZ87FdxgAgG3bLwE4UVV/bDpLlHgNoMmUSqWP1LbmDkxEvmrbdqQbmbque66qfqaOQ56ybfsdYWawbbuiqh9yXXcKwMfCHDspWAAxUdV5pjNMTEwsrlQqlzU4zDcKhULkuxir6mIAHXUcEslFOxHxVfU8x3GyIvLhKOYwiR8BYiIi7aYzVCqVS9HYwzFX2bad2n0MgxIRXbdu3cdEJPEPctWLBRAfozeZOI7TA+DsoMeLyC/Wrl376RAjpcrAwICnqqcDcE1nCRMLID6LHMcx+az6pQh+1f9RVT09yQ8yxcG27U3VavUUAM+azhIWFkC8DjExaalUeheAYwIevllE3lu7Kt70ent7n1TVMzFz52PqsQBiJCJHGJr3kqDHquoXCoXCb8PMk3bFYvEeEbnUdI4wsABipKpdcc9ZKpXeCqA74OH32rZ9ZZh55or58+d/BcB/mM7RKBZAvEw8dnpBwOM2Azg3zB175pKOjo5py7I+ipR/FGABxKt7eHi4Na7JRkdH3yAiQW+OudS27cdCDTTH1B4nvt50jkawAOI1L5fL9cc1WSaTOQ/BrvyvB/DXIceZqy4C8LLpEEGxAGImIqfGMc/Q0FAWwb/3/7pt25vCzDNX2ba9HsDlpnMExQKI32mO4+SinmTBggXvRLCbj55sbW39x7DzzGWe561ESs8CWADxW6SqJ8cwz0DA476btI1Lkq62mcgPTOcIggVgxsejHHxoaCirqicFOPRlAPzXP5grkMJvBFgABojI8a7rLotq/La2thUA9qr3OBH5Ke/4C6b2jUnqNhBhARiiql+OauwGvvq7LswcTSh1XwmyAMx5X6lUiurOwOMCHPNkPp9fHXqSJtLa2norgCnTOerBAjBHanvRh6p2o1E+QJif866/xnR0dEwCuMt0jnqwAMzqL5VKHwhzwHnz5tkIttPT7WHmaFYicofpDPVgARgmIt8bHR3dO8QhCwGOqajqv4WYoWlVq9VUXQhkAZi3OJPJXBvWYL7vB/l2weWdf+Ho6elZB+Ap0zlmiwWQDKc6jhPKdlsB9xwYDWNumqGqqfl9sgCSY2W5XH5zCOMcGuCY8RDmpRoRSeRboHeE24InR873/VWjo6N9PT09/xlkgNqbfuu+nuD7fl0bWziOk6tWq/vWO089VHWBSF0PMmZGRkYOiCoPAMybN2+yq6trw+5+TkTWqKbjCxUWQLLsnclk7nIc5822bf93vQdv2rRp/zoXDQAgl8s9Ws/PW5bVmc1mS3VPFK0DstnsE1FO4Pv+NZjFbdwi8lhaCoAfAZLnIAD3Oo7z+noPtCxrcYD5ZvWvGs1eNputu7xNYQEk0yEAVpfL5bou6Pm+H+SlH/8T4BjahWXLlv0BQCqeqGQBJNeBvu//2nGct8/2AMuyFtQ7iYj8od5jaFZeNB1gNlgAybYXgDtc171IVWfz4b7u/QZVdbL+WDQLqfi9sgCSL6Oq33Qc5+7dXRdQ1UyA8VNxqppCqfi9sgBSQkSOB/BQqVQ6f3BwcIcLXdNy6ZkSgwWQLu0icsXBBx9cdl13u2f+RWRzgDGNv7Z8jkrF75UFkE7LVPWXjuOsdhznxK3XB0TkfwOMZfy15XNUKn6vLIB0OxrAba7rPuw4zgUAguw2vCjkTDQjFb9X3gk4N7wBwGUBLwG8NuQsTW9iYmJxpVJJxdriGQC1lsvlIO8PoJ3wPK/uuzhNib2lVFWD3K9O0alWq0sBPDfbn9+0adMj8+bNi/QVZ5Zlna2qH6njkGdUNdTdlV7N87ynZ/lzhwb5Oy4i1boPalDsBWBZ1hZ+W5UsmUymA8DwbH9+xYoVGwHcF1kgAI7jrKjzkM3FYvG+KLLUS0Q6ghzn+37sd2XG/hHA87wgV6opQqpa9yaitEuBfp/ZbDb2nYRiL4BcLjfrU02KTa/pAHNMd4BjppcvXx77U4SxF8DU1NSTSOErlOa4ZePj43W/SYi2NzY21gHgTwIc+rCI+GHn2Z3YC6Cvr28KQKQbN1DdLN/3g7xMhF4lk8m8LchxquqGnWU2jHwNmKY905pFwJeJ0vZODHickbcyGSkA3/d/bWJe2qWThoaGUnHzSlKNjo7urarHBjlWRO4JOc6smDoDMPKHpV3au62tbdabj9D2MpnM+xDsq/WJIHtAhsFIAdi2XQbwuIm5aedE5MOmM6TcOQGP+0mYIeph8lbgHxmcm3bsZMdxXmc6RBrV3vTcE+BQL5vNGlsLxgogm81eA6Bian7aoRyAT5oOkUYi8tmAh65avny5sVeJGSuA2h/6OlPz0059avXq1al4lj0palu1nR7kWBH5Tshx6mL6acBLkJLNE5vIa+bPn/9npkOkiap+GcH2YrirUCgY+f5/K6MFYNv2ehH5kskMtENfCPmV5XNWqVQ6TETqeWrxFaoa2luhgzJ9BoB8Pv99ALeZzkF/ZEEmk/mG6RBpICIrEeyrv/WTk5M/DztPvYwXgIhoJpM5G0BdL6ikyJ07NjZWNB0iyRzHOQXB7/y7qr+/P/bn/1/NeAEAQFdX14ZqtfoOAGtNZ6FXWJZl/WDNmjUtpoMkkeM4CwFcGfDwTZ7nfT/MPEElogAAoLe390nLso4BMGE6C71i2dTU1NdMh0ioKwHsF+RAEbmmp6fnhZDzBJKYAgCAfD7/dC6XOxrATaaz0Cu+WCqV3mo6RJKUSqUPAjgz4OGbPM/7mzDzNCJRBQAAnZ2dL9u2fYaInIU69qmjyFgicuPIyMgBpoMkQblc7hSRq4IeLyLf7e7uTswbmRNXAFsVCoUbWlpaDgOwEsCU6TxNbp9sNnvrxMTEnqaDmDQxMbHY9/1bAOwRcIhnK5VKYv71BxJcAMDMe9Zt2/58tVpdAuCvAKw3namJdVUqlcFmfWR4zZo1bdPT07cDOCjoGKp6UW9vb6L2xEx0AWzV29v7jG3bl6xdu/ZAEXkngB8AMHb/dBN7V3t7+/Wqmoq/N2EZGhqaPzU1dYuI2EHHEJFh27Z/GGauMKSqzQcGBjwAd9b+w/j4+NJqtdorIssBHAZgCYDFAPZESsrNkEZeXHmG4zj+4ODgObX/H1GpAthSx8/X87OzNjw83NrS0nILgEa2TNsC4KMikri9MPmGjibkOM6VaPCpP1VdNTk5eWZ/f3+QNxKnwvj4+F6e590K4JhGxlHVC4vFYqI++2/FAmhCa9asadm0adOvGzmlrVltWdZp+Xx+zn1bMzo6uiSTydwG4IhGxhGR+/P5/HEmdvydDZ4mN6GOjo5p3/cHAGxocKgVvu+XapthzBnlcvn4TCYzhgYXP4DnROSMpC5+gAXQtHp6etap6jkhDHWQiPymVCqdH8JYRg0ODmYcx/ma7/t3Idje/tvyVPWMfD4/q/cJmsKPAE3OcZyVAD4X0nB3+r7/se7u7tS998F13cNV9ToEe6vPjlxg2/bfhjRWZFgATW5oaCjb3t5+O4CwdgSeBHDJxo0bL0/C0267U7vKfxGALwII68Gna23bPjeksSLFjwBNrr+/vzo9PX0KwnvbbxuAle3t7Q/VHpdNJFW1HMf5UEtLyyMALkZ4i/+2tWvXfiKksSLHMwACAExMTOxZqVTuBHB0yEO7IvLNfD5/SxIuhjmOk1PV00XkIszcOxIaEbl/y5YtJ9Ref5cKLAB6xcjIyIJsNns3wvscvK3HAFwF4Hrbtp+PYPxdGhkZOSCXy/2pqp6LgI/x7sbq1tbWEzo6OlK1xyULgP5I7eaXewFE9dVeFcAvAdzsed5tUT4X7zjO61T1PSIyAOBYRPSRV1V/1dLScnJnZ+fLUYwfJRYAbWd4eHhRLpcbFJHjI57KB1ACcK+qjmQyGaeRr83K5fJBnucVReQoAMcDWIbo/47fvHDhwrOWLl0aya3IUWMB0A4NDg5mlixZclkDL7wI6gUReURVHxeRJ1X1ORF5CcCU7/tVADnLslp9399LRBar6gEisgQzn+cXxpz1skKhcGESrm0ExQKgXSqVSh8UkWsAzDedJUE2i8gnCoXCdaaDNIoFQLs1NjZWtCzrXwDsbzpLAqwVkQHTL/QIC+8DoN3q7u4u+b5vA7jddBbDbqxWq11zZfEDPAOgOjmO8z4A3wPQTG8Rfk5Ezi8UCoOmg4SNZwBUF9u2fwbgcABXA0jcBhchU1X9p+np6TfOxcUP8AyAGlAul4/yff8fABxpOksERkXks4VCYcR0kCixAKghta8LB0TkQgCdpvOE4Heq+pfFYvFm00HiwAKg0JRKpRMAfElE3mw6SwDjIvKdfD7/szR/r18vFgCFrvbR4EIA7waQMZ1nFyoAblHVK4vF4n2mw5jAAqDITExMLJ6enj7Vsqz3quqxSMgu1KrqALixpaXlhs7OzmdN5zGJBUCxGB0d3duyrJNrZfBWALkYp98sIqsB3F6tVm/p6elZF+PcicYCoNitXr26vbW19WhV7VPVooh0Adg3xCmeEJFxAKO+7w9PTk6OzOXtyxvBAqBEGB0d3VtEDstkMger6oEisp+qLlLVRQD2EJF5mPkIURWRzar6MmZ2NX5ORJ7yff8JzNym+4ht2y+Z/LMQERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERUdr9H6oZ2+ARvN4/AAAAAElFTkSuQmCC';
            }
        }

    class GetStock extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('onClick', this.existencias_completo);
        }
        async existencias_completo(){
            console.log("Trae existencias",Date());
            let location = this.env.pos.config.default_location_src_id[0];
            let products;
             products = await this.rpc({
                model: 'stock.quant',
                method: 'search_read',
                fields: ["product_id","available_quantity"],
                domain:[['location_id','=',location]],
             });
            let p;
            let list = this.env.pos.db.product_by_id;
            for(const prod in list){
                list[prod].qty_available = 0;
            }
            products.forEach(item => {
                p = this.env.pos.db.product_by_id[item.product_id[0]];
                if(p){
                    p.qty_available = item.available_quantity;
                }
            });
            this.showScreen('PaymentScreen');
            this.showScreen('ProductScreen');
            console.log("regreso existencias",Date());
        }
    }

    GetStock.template = 'GetStock';

    Registries.Component.add(GetStock);

    const ProductScreen2 = (ProductScreen) =>
        class extends ProductScreen {

            constructor() {
                super(...arguments);
                this.inicial();
                this.update_data();
            }
            inicial() {
                const self = this;
                async function loop(tiempo) {
                    if(tiempo===0){
                        setTimeout(()=>{loop(100000);}, 100000);
                    }
                    else{
                        try {
                            await self.existencias_completo();
                        } catch (error) {
                            console.log(error);
                        }
                        setTimeout(()=>{loop(tiempo);}, tiempo);
                    }
                }
                loop(0);
            }
            async existencias_completo(){
                let location = this.env.pos.config.default_location_src_id[0];
                let products;
                 products = await this.rpc({
                    model: 'stock.quant',
                    method: 'search_read',
                    fields: ["product_id","available_quantity"],
                    domain:[['location_id','=',location]],
                 });
                let p;
                let list = this.env.pos.db.product_by_id;
                for(const prod in list){
                    list[prod].qty_available = 0;
                }
                products.forEach(item => {
                    p = this.env.pos.db.product_by_id[item.product_id[0]];
                    if(p){
                        p.qty_available = item.available_quantity;
                    }
                });
                this.showScreen('PaymentScreen');
                this.showScreen('ProductScreen');
            }

            update_data() {
                const self = this;
                async function loop(tiempo,anterior) {
                    if(tiempo===0){
                        setTimeout(()=>{loop(40000,1000*60*3);}, 1000*60*3);
                    }
                    else{
                        try {
                            await self.autoSync(anterior);
                        } catch (error) {
                            console.log(error);
                        }
                        setTimeout(()=>{loop(tiempo,tiempo);}, tiempo);
                    }
                }
                loop(0,0);
            }

            async load_new_items(mod,Id) {
                var self = this;
                var index = 20;
                let obj;
                return new Promise(function (resolve, reject) {
                    var fields = _.find(self.env.pos.models, function(model){ return model.model === mod; }).fields;
                    var domain = [['id','=', Id]];
                    self.rpc({
                        model: mod,
                        method: 'search_read',
                        args: [domain, fields],
                    }, {
                        timeout: 3000,
                        shadow: true,
                    })
                    .then(function (items) {
                        if (mod === "res.partner") index = 5;
                        else if(mod === "product.product") index = 20;
                        else if(mod === "product.pricelist.item") index = 16;

                        obj = self.env.pos.models[index].loaded(self.env.pos,items);
                        if(obj) {
                            resolve();
                        }else {
                            reject();
                        }
                    }, function (type, err) { reject(); });
                });
            }

            update_info(rec) {
                var self = this;
                let DB = self.env.pos.db;
                let actualizar;

                return new Promise( (resolve,reject) =>{
                    let datos = JSON.parse(rec.datos);
                    if(rec["modelo"] === "product.product"){
                        actualizar = DB.product_by_id[rec.rec_id];
                    } else if (rec["modelo"] === "res.partner"){
                        actualizar = DB.get_partner_by_id(rec.rec_id);
                    } else if (rec["modelo"] === "product.pricelist.item"){
                        let lst = this.env.pos.pricelists;
                        let items;
                        for(let i=0; i<lst.length; i++){
                            if(datos.pricelist_id && lst[i].id === datos.pricelist_id[0]) {
                                items = lst[i].items;
                                actualizar = _.filter(items,function (item){
                                   return (item.id === rec.rec_id);
                                });
                                if(actualizar) actualizar = actualizar[0];
                            }
                        }
                    }

                    if(actualizar){
                        for(let p in datos){
                            actualizar[p] = datos[p];
                        }
                    } else {
                        console.log("Es nuevo solicitando info");
                        self.load_new_items(rec["modelo"],rec.rec_id).then( () => {
                            resolve("Objeto creado");
                        }).catch( () => {
                            reject();
                        });
                    }
                });
            }

            async autoSync(tiempo){
                let dt = await this.rpc({
                    model: 'data.pos.metadatos',
                    method: 'update_data_pos',
                    args: [tiempo/1000]
                });
                dt.forEach( (registro,index) => {
                   this.update_info(registro).then( res => {

                   }).catch((e) => {
                        console.log("No se pudo actualizar ",e);
                   });
                });

                this.showScreen('PaymentScreen');
                this.showScreen('ProductScreen');
            }
        }

    const CategoryButton2 = (CategoryButton) =>
        class extends CategoryButton {
            get imageUrl() {
                const category = this.props.category
                // return `/web/image?model=pos.category&field=image_128&id=${category.id}&write_date=${category.write_date}&unique=1`;
                return 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAAsTAAALEwEAmpwYAAAXcElEQVR4nO3de3gdZZ0H8O9vzjlpA0mLZSnKRZ4CFSHYNOfMSUIoSsAbInJ5NMpN0VXwgq4rKi7iouttXei6wiKwuC48Cmhku8ICykUCuzUmOTMnROgKy9LiculytWxD0+acmd/+kVO20lvOnJl5Z3K+n+fhv8z7fhv6fjtnzsw7ABERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERFR+ojpALRjruu+X1VvAJAxnaVBnoicWSgUfmo6CG2PBZBAc2jxb8USSCgWQMLMwcW/FUsggVgACTKHF/9WLIGEYQEkRBMs/q1YAgnCAkiAJlr8W7EEEoIFYFgTLv6tWAIJwAIwqIkX/1YsAcNYAIZw8b+CJWAQC8AALv7tsAQMYQHEjIt/p1gCBrAAYsTFv1ssgZixAGLCxT9rLIEYsQBiwMVfN5ZATFgAEePiD4wlEAMWQIS4+BvGEogYCyAiXPyhYQlEiAUQAS7+0LEEIsICCBkXf2RYAhFgAYSIiz9yLIGQsQBCwsUfG5ZAiFgAIeDijx1LICQsgAZx8RvDEggBC6ABXPzGsQQaNKcKwHGcPTKZzOJKpbKniET9Z+sRkWvAxW+ap6rnARiNchJV1Vwu97Lnec/atr0pyrnilNoCKJfL+/m+fyyAXgDLAbwRwD5GQ1GzeA7AwwAeADBiWdZ9+Xz+acOZAklVAYyOji7JZDJnATgNM4ueKCkeALDK87wf9/T0rDMdZrZSUQCu6x6nqhcAOAEpyUxNSwH8QkRWFgqFe02H2Z1EL6ZyuWyr6mWq+hbTWYjqJSL3i8jn8/m8YzrLziSyAIaGhua3tbV9W0Q+A8AynYeoAb6qXj45OfkX/f39m02HebXEFYDruoeq6ioAbzKdhShED4rIaYVC4b9MB9lWogqgXC4f5fv+vwLY23QWogi8YFnWSfl8/jemg2yVmAKoLf67ALSZzkIUoUnLst6elBJIRAGMj48v9TxvBMAi01mIYvBiJpPp7erqetR0EOMX2IaHh1s9z1sFLn5qHos8z1s1PDzc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V1V/1dLScnJnZ+fLUYwfJRYAbWd4eHhRLpcbFJHjI57KB1ACcK+qjmQyGaeRr83K5fJBnucVReQoAMcDWIbo/47fvHDhwrOWLl0aya3IUWMB0A4NDg5mlixZclkDL7wI6gUReURVHxeRJ1X1ORF5CcCU7/tVADnLslp9399LRBar6gEisgQzn+cXxpz1skKhcGESrm0ExQKgXSqVSh8UkWsAzDedJUE2i8gnCoXCdaaDNIoFQLs1NjZWtCzrXwDsbzpLAqwVkQHTL/QIC+8DoN3q7u4u+b5vA7jddBbDbqxWq11zZfEDPAOgOjmO8z4A3wPQTG8Rfk5Ezi8UCoOmg4SNZwBUF9u2fwbgcABXA0jcBhchU1X9p+np6TfOxcUP8AyAGlAul4/yff8fABxpOksERkXks4VCYcR0kCixAKghta8LB0TkQgCdpvOE4Heq+pfFYvFm00HiwAKg0JRKpRMAfElE3mw6SwDjIvKdfD7/szR/r18vFgCFrvbR4EIA7waQMZ1nFyoAblHVK4vF4n2mw5jAAqDITExMLJ6enj7Vsqz3quqxSMgu1KrqALixpaXlhs7OzmdN5zGJBUCxGB0d3duyrJNrZfBWALkYp98sIqsB3F6tVm/p6elZF+PcicYCoNitXr26vbW19WhV7VPVooh0Adg3xCmeEJFxAKO+7w9PTk6OzOXtyxvBAqBEGB0d3VtEDstkMger6oEisp+qLlLVRQD2EJF5mPkIURWRzar6MmZ2NX5ORJ7yff8JzNym+4ht2y+Z/LMQERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERUdr9H6oZ2+ARvN4/AAAAAElFTkSuQmCC';
            }
        }
    const Chrome2 = (Chrome) =>
        class extends Chrome {
            _preloadImages() {
            var ima = 'data:image/png;base64, iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAAsTAAALEwEAmpwYAAAXcElEQVR4nO3de3gdZZ0H8O9vzjlpA0mLZSnKRZ4CFSHYNOfMSUIoSsAbInJ5NMpN0VXwgq4rKi7iouttXei6wiKwuC48Cmhku8ICykUCuzUmOTMnROgKy9LiculytWxD0+acmd/+kVO20lvOnJl5Z3K+n+fhv8z7fhv6fjtnzsw7ABERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERFR+ojpALRjruu+X1VvAJAxnaVBnoicWSgUfmo6CG2PBZBAc2jxb8USSCgWQMLMwcW/FUsggVgACTKHF/9WLIGEYQEkRBMs/q1YAgnCAkiAJlr8W7EEEoIFYFgTLv6tWAIJwAIwqIkX/1YsAcNYAIZw8b+CJWAQC8AALv7tsAQMYQHEjIt/p1gCBrAAYsTFv1ssgZixAGLCxT9rLIEYsQBiwMVfN5ZATFgAEePiD4wlEAMWQIS4+BvGEogYCyAiXPyhYQlEiAUQAS7+0LEEIsICCBkXf2RYAhFgAYSIiz9yLIGQsQBCwsUfG5ZAiFgAIeDijx1LICQsgAZx8RvDEggBC6ABXPzGsQQaNKcKwHGcPTKZzOJKpbKniET9Z+sRkWvAxW+ap6rnARiNchJV1Vwu97Lnec/atr0pyrnilNoCKJfL+/m+fyyAXgDLAbwRwD5GQ1GzeA7AwwAeADBiWdZ9+Xz+acOZAklVAYyOji7JZDJnATgNM4ueKCkeALDK87wf9/T0rDMdZrZSUQCu6x6nqhcAOAEpyUxNSwH8QkRWFgqFe02H2Z1EL6ZyuWyr6mWq+hbTWYjqJSL3i8jn8/m8YzrLziSyAIaGhua3tbV9W0Q+A8AynYeoAb6qXj45OfkX/f39m02HebXEFYDruoeq6ioAbzKdhShED4rIaYVC4b9MB9lWogqgXC4f5fv+vwLY23QWogi8YFnWSfl8/jemg2yVmAKoLf67ALSZzkIUoUnLst6elBJIRAGMj48v9TxvBMAi01mIYvBiJpPp7erqetR0EOMX2IaHh1s9z1sFLn5qHos8z1s1PDzc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V1V/1dLScnJnZ+fLUYwfJRYAbWd4eHhRLpcbFJHjI57KB1ACcK+qjmQyGaeRr83K5fJBnucVReQoAMcDWIbo/47fvHDhwrOWLl0aya3IUWMB0A4NDg5mlixZclkDL7wI6gUReURVHxeRJ1X1ORF5CcCU7/tVADnLslp9399LRBar6gEisgQzn+cXxpz1skKhcGESrm0ExQKgXSqVSh8UkWsAzDedJUE2i8gnCoXCdaaDNIoFQLs1NjZWtCzrXwDsbzpLAqwVkQHTL/QIC+8DoN3q7u4u+b5vA7jddBbDbqxWq11zZfEDPAOgOjmO8z4A3wPQTG8Rfk5Ezi8UCoOmg4SNZwBUF9u2fwbgcABXA0jcBhchU1X9p+np6TfOxcUP8AyAGlAul4/yff8fABxpOksERkXks4VCYcR0kCixAKghta8LB0TkQgCdpvOE4Heq+pfFYvFm00HiwAKg0JRKpRMAfElE3mw6SwDjIvKdfD7/szR/r18vFgCFrvbR4EIA7waQMZ1nFyoAblHVK4vF4n2mw5jAAqDITExMLJ6enj7Vsqz3quqxSMgu1KrqALixpaXlhs7OzmdN5zGJBUCxGB0d3duyrJNrZfBWALkYp98sIqsB3F6tVm/p6elZF+PcicYCoNitXr26vbW19WhV7VPVooh0Adg3xCmeEJFxAKO+7w9PTk6OzOXtyxvBAqBEGB0d3VtEDstkMger6oEisp+qLlLVRQD2EJF5mPkIURWRzar6MmZ2NX5ORJ7yff8JzNym+4ht2y+Z/LMQERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERERUdr9H6oZ2+ARvN4/AAAAAElFTkSuQmCC';
            for (let product of this.env.pos.db.get_product_by_category(0)) {
                const image = new Image();
                // image.src = `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
                image.src = ima;
            }
            for (let category of Object.values(this.env.pos.db.category_by_id)) {
                if (category.id == 0) continue;
                const image = new Image();
                // image.src = `/web/image?model=pos.category&field=image_128&id=${category.id}&write_date=${category.write_date}&unique=1`;
                image.src = ima;
            }
            const staticImages = ['backspace.png', 'bc-arrow-big.png'];
            for (let imageName of staticImages) {
                const image = new Image();
                image.src = `/point_of_sale/static/src/img/${imageName}`;
            }
        }
        }

    Registries.Component.extend(Chrome, Chrome2);

    Registries.Component.extend(ProductItem, ProductItem2);
    Registries.Component.extend(ProductScreen, ProductScreen2);
    Registries.Component.extend(CategoryButton, CategoryButton2);

    return ProductItem;
});
