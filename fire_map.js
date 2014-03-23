





function init() {
            
            
            
            map = new OpenLayers.Map('map', {
                        projection: "EPSG:3857"
            });

            var arrayOSM = ["http://otile1.mqcdn.com/tiles/1.0.0/map/${z}/${x}/${y}.jpg", "http://otile2.mqcdn.com/tiles/1.0.0/map/${z}/${x}/${y}.jpg", "http://otile3.mqcdn.com/tiles/1.0.0/map/${z}/${x}/${y}.jpg", "http://otile4.mqcdn.com/tiles/1.0.0/map/${z}/${x}/${y}.jpg"];
            
            
            

            var baseOSM = new OpenLayers.Layer.OSM("MapQuest-OSM Tiles", arrayOSM);
           
	    
                        
            
            /**for styling wildfire/incidents layer**/ 
            var context = {
                        selectGraphic: function(feature) {
                                    if (feature.attributes.status == "active") {
                                                return "fire.png"
                                    }
                                    else {
                                                return "fire-inactive.png"
                                    }
                        }
                        
            }
            
            var template = {
                        externalGraphic: "${selectGraphic}",
                        graphicWidth: 20,
                        graphicHeight: 30
            }
            
            
            var wildfireStyle = new OpenLayers.Style(template, {context:context});
            
            
            var incidents = new OpenLayers.Layer.Vector("Wildfires", {
                        projection: "EPSG:4326",
                        strategies: [new OpenLayers.Strategy.Fixed()],
                        protocol: new OpenLayers.Protocol.HTTP({
                                    url: "wildfires.geojson",
                                    format: new OpenLayers.Format.GeoJSON()
                        }),
                        styleMap: new OpenLayers.StyleMap(wildfireStyle)

            });
            
            
                       
		/**for styling modis layers**/

            
            var style = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style["default"]);
                        style.graphicName = "square";
                        style.fillColor = "${colorFunction}";
                        style.fillOpacity = "0.4";
                        style.pointRadius = "${sizeFunction}";
                        style.strokeColor = "#fa0000";
                        style.strokeWidth = "0.4";
                        style.strokeOpacity = "0.8";
                        
            
            
            var defaultStyle = new OpenLayers.Style(style, {
                        context: {
                                    sizeFunction: function(feature){
                                                
                                                if (map.getScale() > 800000) {
                                                            return 5
                                                } else {
                                                            return 1000/feature.layer.map.getResolution();
	        /**size function is to keep icon equal to scaled 1km, approx 'detection' size of modis birds**/ 
                                                
                                                }
                                    },
                                    
	       /**color for different layers/times**/
                                    colorFunction: function(feature){
                                                
                                                if (feature.attributes.group == 24) {
                                                            return '#FA0000'
                                                } else if (feature.attributes.group == 48){
                                                            return '#F78222'
                                                            
                                                } else {
                                                            return '#FDFB99'
                                                }
                                                
                                                
                                    }
                        }
            })
            

            var modis24 = new OpenLayers.Layer.Vector("MODIS Detections -- 24 Hours", {
                        projection: "EPSG:3857",
                        strategies: [new OpenLayers.Strategy.Fixed()],
                        protocol: new OpenLayers.Protocol.HTTP({
                                    url: "modis24.geojson",
                                    format: new OpenLayers.Format.GeoJSON()
                        }),
                        styleMap: new OpenLayers.StyleMap(defaultStyle)


            });
            
            var modis48 = new OpenLayers.Layer.Vector("MODIS Detections -- 48 Hours", {
                        projection: "EPSG:3857",
                        strategies: [new OpenLayers.Strategy.Fixed()],
                        protocol: new OpenLayers.Protocol.HTTP({
                                    url: "modis48.geojson",
                                    format: new OpenLayers.Format.GeoJSON()
                        }),
                        styleMap: new OpenLayers.StyleMap(defaultStyle)
                        

            });
            
            var modis7 = new OpenLayers.Layer.Vector("MODIS Detections -- 7 Days", {
                        projection: "EPSG:3857",
                        strategies: [new OpenLayers.Strategy.Fixed()],
                        protocol: new OpenLayers.Protocol.HTTP({
                                    url: "modis7.geojson",
                                    format: new OpenLayers.Format.GeoJSON()
                        }),
                        styleMap: new OpenLayers.StyleMap(defaultStyle)
                        

            });
            
            
           var perimeters = new OpenLayers.Layer.WMS("Perimeters", "http://wildfire.cr.usgs.gov/arcgis/services/geomac_dyn/MapServer/WMSServer",
                        {
                                    layers: "24",
                                    transparent: true,
                                    format: "image/png"
                        },
                        {
                                    isBaseLayer:false
                        }
            
            )
                        
            


            map.addLayers([baseOSM, perimeters, incidents, modis24, modis48, modis7]);

            map.setCenter(
            new OpenLayers.LonLat(-121.4689, 38.5556).transform(new OpenLayers.Projection("EPSG:4326"), map.getProjectionObject()), 8);
            
	    function buildPopupHTML(feature) {
                        console.log(feature.feature.attributes.name)
                        html = "<h4 class='popup'>" + feature.feature.attributes.name + " Fire</h4><div class='popupContent'>"
                        
                        if (feature.feature.attributes.acres) {
                                    html += "<h5>Size</h5><span>" + feature.feature.attributes.acres + " acres</span><br>"
                        }
                        if (feature.feature.attributes.containment) {
                                    html += "<h5>Containment</h5><span>" + feature.feature.attributes.containment + "</span><br>"
                        }
                        if (feature.feature.attributes.location) {
                                    html += "<h5>Location</h5><span>" + feature.feature.attributes.location + "</span><br>"
                        }
                        if (feature.feature.attributes.last_update) {
                                    html += "<h5>Last Update</h5><span>" + feature.feature.attributes.last_update + "</span><br>"
                        }
                        if (feature.feature.attributes.link) {
                                    html += "<a target='_blank' href='" + feature.feature.attributes.link + "'><h5 style='text-align:center;'>More Information</h5>"
                        }
                        
                        html += "</div>"
                        return html
                        
            }
            
            
            function addFirePopup(feature){
                        selectedFeature = feature;
                        popup = new OpenLayers.Popup.Anchored(null,
                                                              feature.feature.geometry.getBounds().getCenterLonLat(),
                                                              null,
                                                              buildPopupHTML(feature)
                                                             , null, true, removePopup);
                        feature.feature.popup = popup;
                        map.addPopup(popup)
                        popup.updateSize()
            }
            
            function removePopup() {
                        map.removePopup(popup);
                        popup.destroy();
                        popup = null;
            }

            
            
            
            selectCntrl = new OpenLayers.Control.SelectFeature(incidents);
            map.addControl(selectCntrl);
            selectCntrl.activate();

            incidents.events.on({"featureselected": addFirePopup, "featureunselected": removePopup});
            


}
