(function($, google) {
    'use strict';

    /*
    Create a new picker
    
    @param root : the root DOM element or jQuery selector to work from
    @param options : a set of options, will be deep copied on top of
                `Picker.prototype.defaults`
    */        
    var Picker = function(root, options) {
        this.$root = $(root);
        this.parseOptions(options);
        this.start();
    };
    /*
    Default options for the drawn shapes (rect / circle)
    */
    var baseShapeOptions = {
        draggable: false,
        editable: false,
        clickable: false,
        strokeWidth: 1,
        strokeColor: '#6f6',
        fillColor: '#6f6'
    };
    /*
    Picker defaults
    */
    Picker.prototype.defaults = {
        /* List of the 4 N/S/E/W inputs (enables NSEW mode) */
        nsewInputs: [],
        /* List of the 3 Center Lat / Center Lon / Radius inputs (enables CR mode) */
        crInputs: [],
        /* Button that will open the picker. Will be created if null. */
        openBtn: null,
        /* Map size */
        width: 600,
        height: 400,
        /* Map options */
        mapOptions: {
            zoom: 1,
            center: new google.maps.LatLng(0,0),
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            streetViewControl: false
        },
        /* NSEW rectangle options */
        rectangleOptions: $.extend({}, baseShapeOptions),
        /* CR circle options */
        circleOptions: $.extend({}, baseShapeOptions)
    };
    /* Parse options */
    Picker.prototype.parseOptions = function(options) {
        this.options = $.extend(true, {}, this.defaults, options );
    };
    /* Connect to the inputs on the main page */
    Picker.prototype.initInputs = function() {
        // Create picker button if not defined
        this.$openBtn = this.options.openBtn;
        if (this.options.openBtn) {
            this.$openBtn = $(this.options.openBtn);
        } else {
            this.$openBtn = $('<button type="button" class="btn btn-default">Pick Coordinates</button>');
            this.$root.append($('<div class="text-center">').append(this.$openBtn));
        }
        // Connect to inputs
        this.$inputN = $(this.options.nsewInputs[0] || $('input[name*=north]', this.$root));
        this.$inputS = $(this.options.nsewInputs[1] || $('input[name*=south]', this.$root));
        this.$inputE = $(this.options.nsewInputs[2] || $('input[name*=east]', this.$root));
        this.$inputW = $(this.options.nsewInputs[3] || $('input[name*=west]', this.$root));

        this.$inputCenterLat = $(this.options.crInputs[0] || $('input[name*=center_lat]', this.$root));
        this.$inputCenterLon = $(this.options.crInputs[1] || $('input[name*=center_lon]', this.$root));
        this.$inputMaxRadius = $(this.options.crInputs[2] || $('input[name*=max_radius]', this.$root));
        this.$inputMinRadius = $(this.options.crInputs[3] || $('input[name*=min_radius]', this.$root));
    };
    /* Set up the picker dialog */
    Picker.prototype.initDialog = function() {
        // Div that the map attaches to
        this.$map = $('<div class="coordinate-picker-map" style="width:'+this.options.width+'px;height:'+this.options.height+'px;"></div>');
        // Overlay sits on top of the map so we can capture mouse events
        this.$mapOverlay = $('<div class="coordinate-picker-overlay"></div>');
        // Drawing controls
        this.$rectBtn = $('<button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-pencil"></span> Draw Box</button>');
        this.$circleBtn = $('<button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-pencil"></span> Draw Circle</button>');
        this.$panBtn = $('<button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-move"></span> Pan/Zoom</button>');
        this.$drawPanControls = $('<div class="coordinate-picker-top-controls">').append(
            "<small>Drawing mode:</small> ",
            $('<div class="btn-group">').append(this.$rectBtn, this.$circleBtn, this.$panBtn));
        // Dialog controls
        this.$okBtn = $('<button type="button" class="btn btn-primary btn-sm">Ok</button>');
        this.$cancelBtn = $('<button type="button" class="btn btn-default btn-sm">Cancel</button>');
        this.$okCancelControls = $('<div class="coordinate-picker-bottom-controls">').append(
            this.$okBtn, ' ', this.$cancelBtn);

        // Add cursor position monitor after drawing controls
        this.$cursorPos = $('<div class="well cursor-pos"></div>');
        this.$drawPanControls.append(
            $('<div class="pull-right">').append(this.$cursorPos));
    };
    /* Set up the map and related pieces */
    Picker.prototype.initMap = function() {
        this.rectShape = null;
        this.circleShape = null;
        this.drawStartPoint = null;
        this.drawStartLatLng = null;
        this.map = null;
        // GMaps overlay for coordinate translation
        this.ov = new google.maps.OverlayView();
        this.ov.onAdd = function () {
        };
        this.ov.draw = function () {
        };
        this.ov.onRemove = function () {
        };
        // Set to null, "rect" or "circle"
        this.drawingMode = null;
    };
    Picker.prototype.setDrawingMode = function(mode) {
        this.drawingMode = mode;
        if (mode) {
            this.$mapOverlay.show();
        } else {
            this.$mapOverlay.hide();
        }
        this.$rectBtn.toggleClass('active', mode === 'rect');
        this.$circleBtn.toggleClass('active', mode === 'circle');
        this.$panBtn.toggleClass('active', !mode);
    };
    Picker.prototype.initConnections = function() {
        var _this = this;
        this.$rectBtn.click(function() { _this.setDrawingMode('rect'); });
        this.$circleBtn.click(function() { _this.setDrawingMode('circle'); });
        this.$panBtn.click(function() { _this.setDrawingMode(null); });
    };
    /* Position is from mouse event evt.pageX, evt.pageY */
    Picker.prototype.getPoint = function(pageX, pageY) {
        var offset = this.$map.offset();
        var posX = Math.max(0, pageX - offset.left);
        var posY = Math.max(0, pageY - offset.top);
        posX = Math.min(posX, this.$map.width());
        posY = Math.min(posY, this.$map.height());
        return new google.maps.Point(posX, posY);
    };
    /* Turn a point into a LatLng */
    Picker.prototype.getLatLng = function(point) {
        var prj = this.ov.getProjection();
        return prj.fromContainerPixelToLatLng(point);
    };
    /* Print a LatLng for the infobubble */
    Picker.prototype.printLatLng = function(latLng) {
        var lat = latLng.lat().toFixed(3);
        var lon = latLng.lng().toFixed(3);
        var latSuffix = (lat >= 0 ? "&deg; N" : "&deg; S");
        var lonSuffix = (lon >= 0 ? "&deg; E" : "&deg; W");
        return "" + Math.abs(lat) + latSuffix + " x " + Math.abs(lon) + lonSuffix;
    };
    /* Update the NSEW rect with the given point as the mouse/bounds position */
    Picker.prototype.updateRect = function(point) {
        // The rect bounds are based on `point` and `drawStartPoint` but we have
        // to define the bounds using NW and SE points
        var left = Math.min(point.x, this.drawStartPoint.x);
        var right = Math.max(point.x, this.drawStartPoint.x);
        var top = Math.min(point.y, this.drawStartPoint.y);
        var bottom = Math.max(point.y, this.drawStartPoint.y);
        // console.log("("+left+","+bottom+")-("+right+","+top+")");
        this.rectShape.setBounds(new google.maps.LatLngBounds(
            this.getLatLng(new google.maps.Point(left, bottom)),
            this.getLatLng(new google.maps.Point(right, top))
        ));
    };
    /* Update the CR circle with the given point as the mouse/bounds position */
    Picker.prototype.updateCircle = function(point) {
        // Radius is the distance from this point to the center at drawStartLatLng
        var latLng = this.getLatLng(point);
        var distance = google.maps.geometry.spherical.computeDistanceBetween(
            this.drawStartLatLng, latLng);
        this.circleShape.setRadius(distance);
    };

    Picker.prototype.startRect = function(n, s, e, w) {
        var sw = new google.maps.LatLng(s, w);
        var ne = new google.maps.LatLng(n, e);
        var rectOptions = {
            map: this.map,
            bounds: new google.maps.LatLngBounds(sw, ne)
        };
        if (this.rectShape) {
            this.rectShape.setOptions(rectOptions);
        } else {
            this.rectShape = new google.maps.Rectangle(
                $.extend({}, this.options.rectangleOptions, rectOptions)
            );
        }
    };

    Picker.prototype.startCircle = function(lat, lon, r) {
        var center = new google.maps.LatLng(lat, lon);
        var circleOptions = $.extend({}, this.options.circleOptions, {
            map: this.map,
            center: center,
            radius: r
        });
        if (this.circleShape) {
            this.circleShape.setOptions(circleOptions);
        } else {
            this.circleShape = new google.maps.Circle(circleOptions);
        }
    };

    Picker.prototype.startDrawing = function(e) {
        if (this.rectShape) {
            this.rectShape.setMap(null);
        }
        if (this.circleShape) {
            this.circleShape.setMap(null);
        }
        this.drawStartPoint = this.getPoint(e.pageX, e.pageY);
        this.drawStartLatLng = this.getLatLng(this.drawStartPoint);
        var startLat = this.drawStartLatLng.lat();
        var startLng = this.drawStartLatLng.lng();
        if (this.drawingMode === 'rect') {
            this.startRect(startLat, startLat, startLng, startLng);
        }
        else if (this.drawingMode === 'circle') {
            this.startCircle(startLat, startLng, 0);
        }
    };

    // Debounce the refresh method
    // 200ms timeout
    var DEBOUNCE = 200;
    Picker.prototype.keepDrawingDebounced = function() {
        if (this.drawingMode === 'rect') {
            this.updateRect(this.lastPoint);
        }
        else if (this.drawingMode === 'circle') {
            this.updateCircle(this.lastPoint);
        }
        this.debounceTimeout = null;
    };
    Picker.prototype.keepDrawing = function(e) {
        this.lastPoint = this.getPoint(e.pageX, e.pageY);
        this.$cursorPos.html(this.printLatLng(this.getLatLng(this.lastPoint)));
        if (!this.debounceTimeout) {
            var _this = this;
            this.debounceTimeout = window.setTimeout(function() {
                _this.keepDrawingDebounced();
            }, DEBOUNCE);
        }
    };
    Picker.prototype.stopDrawing = function(e) {
        this.keepDrawing(e);
        this.drawStartPoint = this.drawStartLatLng = this.lastPoint = null;
    };

    Picker.prototype.initRect = function() {
        var self = this;
        var locN = parseFloat(self.$inputN.val());
        var locS = parseFloat(self.$inputS.val());
        var locE = parseFloat(self.$inputE.val());
        var locW = parseFloat(self.$inputW.val());
        // Skip if no/invalid coordinates
        if (isNaN(locN) || isNaN(locS) || isNaN(locE) || isNaN(locW)) {
            return;
        }
        // Skip if these are global coordinates
        if (locN > 89 && locS < -89 && locE > 179 && locW < -179) {
            return;
        }
        var firstTime = !self.rectShape;
        self.startRect(locN, locS, locE, locW);

        // Zoom into current bounds on initial open
        if (firstTime) {
            google.maps.event.addListenerOnce(self.map, 'idle', function(r) {
                self.map.controls[google.maps.ControlPosition.BOTTOM_RIGHT].push(self.$cursorPos);
                self.map.fitBounds(self.rectShape.getBounds());
                if (self.map.getZoom() > 5) {
                    self.map.setZoom(5);
                }
            });
        }
    };
    Picker.prototype.initCircle = function() {
        var self = this;
        var centerLat = parseFloat(self.$inputCenterLat.val());
        var centerLon = parseFloat(self.$inputCenterLon.val());
        var maxRadius = parseFloat(self.$inputMaxRadius.val());
        var minRadius = parseFloat(self.$inputMinRadius.val());
        // Skip if no/invalid coordinates
        if (isNaN(centerLat) || isNaN(centerLon) || isNaN(maxRadius)) {
            return;
        }

        var firstTime = !self.circleShape;
        self.startCircle(centerLat, centerLon, maxRadius);

        // Zoom into current bounds on initial open
        if (firstTime) {
            google.maps.event.addListenerOnce(self.map, 'idle', function(r) {
                self.map.fitBounds(self.circleShape.getBounds());
                if (self.map.getZoom() > 5) {
                    self.map.setZoom(5);
                }
            });
        }
    };

    Picker.prototype.startMap = function() {
        var self = this;
        // Create map object
        self.map = new google.maps.Map(self.$map[0], self.options.mapOptions);
        // Add the overlay DOM after the OverlayView is added, to ensure it is on top
        self.ov.onAdd = function() {
            self.$map.append(self.$mapOverlay);
        };
        self.ov.setMap(self.map);
        self.$mapOverlay.mousedown(function(e) {
            if (self.drawingMode) {
                self.startDrawing(e);
            }
        });
        self.$map.mousemove(function(e) {
            var point = self.getPoint(e.pageX, e.pageY);
            self.$cursorPos.html(self.printLatLng(self.getLatLng(point)));
            if (self.drawingMode && self.drawStartPoint) {
                self.keepDrawing(e);
            }
        });
        $(document).mouseup(function(e) {
            if (self.drawingMode && self.drawStartPoint) {
                self.stopDrawing(e);
                self.disableDrawingMode();
            }
        });
    };

    /* Set up picker */
    Picker.prototype.start = function() {
        var self = this;
        self.initInputs();
        self.initDialog();
        self.initMap();
        self.initConnections();

        self.startMap();

        var $qtipTarget = self.$root;
        $qtipTarget.qtip({
            content: {
                title: 'Draw a box on the map to define a region',
                text: 'Loading map...'
            },
            position: {
                my: 'center',
                at: 'center',
                viewport: $(document)
            },
            show: {
                target: this.$openBtn,
                event: 'click'
            },
            hide: {
                event: 'unfocus'
            },
            style: {
                classes: 'coordinate-picker qtip-bootstrap'
            },
            events: {
                render: function(event, api) {
                    var tooltip = $(this);
                    api.elements.content.empty().append(self.$drawPanControls, self.$map, self.$okCancelControls);
                    // Temporarily show the tooltip so we don't get rendering bugs in GMaps
                    tooltip.show();
                    self.startMap();
                    // Hide the tooltip again now we're done
                    tooltip.hide();
                },
                show: function(event, api) {
                    // Initialize/update the current selection
                    self.initRect();
                    // If there is no selection, start in drawing mode
                    if (self.rectShape) { self.disableDrawingMode(); }
                    else { self.enableRectMode(); }
                }
            }
        });
        
        self.$cancelBtn.click(function() {
            self.$qtipTarget.qtip('hide');
        });
        self.$okBtn.click(function() {
            self.$qtipTarget.qtip('hide');
            if (self.rectShape) {
                var bounds = self.rectShape.getBounds();
                self.$inputS.val(bounds.getSouthWest().lat().toFixed(3));
                self.$inputW.val(bounds.getSouthWest().lng().toFixed(3));
                self.$inputN.val(bounds.getNorthEast().lat().toFixed(3));
                self.$inputE.val(bounds.getNorthEast().lng().toFixed(3));
            }
            if (self.circleShape) {
                self.$inputCenterLat.val(self.circleShape.getCenter().lat().toFixed(3));
                self.$inputCenterLon.val(self.circleShape.getCenter().lng().toFixed(3));
                var radius = self.circleShape.getRadius();
                // Hacky meters/degrees conversion, get the longitude of moving the distance East from 0,0
                var offset = google.maps.geometry.spherical.computeOffset(
                    new google.maps.LatLng(0, 0), radius, 90);
                var degrees = offset.lng();
                self.$inputMaxRadius.val(degrees.toFixed(3));
            }
        });
    };

    $.fn.coordinate_picker = function(options) {
        var picker = new Picker(this, options);
        $(this).data('coordinate_picker', picker);
        return this;
    };

})(jQuery, google);
