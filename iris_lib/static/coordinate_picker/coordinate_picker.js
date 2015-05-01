(function($, google, InfoBubble) {
  'use strict'

  var Picker = function(root, options) {
    this.$root = $(root);
    this.parseOptions(options);
    this.start();
  };

  Picker.prototype.defaults = {
    nsewInputs: [],
    openBtn: null,
    width: 600,
    height: 400,
    mapOptions: {
      zoom: 1,
      center: new google.maps.LatLng(0,0),
      mapTypeId: google.maps.MapTypeId.ROADMAP,
      streetViewControl: false
    },
    rectangleOptions: {
      draggable: false,
      editable: false,
      clickable: false
    },
    circleOptions: {
      draggable: false,
      editable: false,
      clickable: false
    },
    infoBubbleOptions: {
      padding: 0,
      borderWidth: 0,
      shadowStyle: 0,
      borderRadius: 0,
      backgroundColor: 'none',
      disableAutoPan: true,
      disableAnimation: true,
      hideCloseButton: true,
      arrowStyle: 3,
      arrowSize: 0,
      backgroundClassName: 'info-bubble'
    }
  };

  Picker.prototype.parseOptions = function(options) {
    this.options = $.extend(true, {}, this.defaults, options );
  };

  Picker.prototype.start = function() {
    var _this = this;
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

    // Div that the map attaches to
    var $map = $('<div class="coordinate-picker-map" style="width:'+this.options.width+'px;height:'+this.options.height+'px;"></div>');
    // Overlay sits on top of the map so we can capture mouse events
    var $mapOverlay = $('<div class="coordinate-picker-overlay"></div>');
    // Drawing congtrols
    var $rectBtn = $('<button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-pencil"></span> Draw Box</button>');
    var $circleBtn = $('<button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-pencil"></span> Draw Circle</button>');
    var $panBtn = $('<button type="button" class="btn btn-default btn-xs"><span class="glyphicon glyphicon-move"></span> Pan/Zoom</button>');
    var $drawPanControls = $('<div class="coordinate-picker-top-controls">').append(
      "<small>Drawing mode:</small> ",
      $('<div class="btn-group">').append($rectBtn, $circleBtn, $panBtn));
    // Dialog controls
    var $okBtn = $('<button type="button" class="btn btn-primary btn-sm">Ok</button>');
    var $cancelBtn = $('<button type="button" class="btn btn-default btn-sm">Cancel</button>');
    var $okCancelControls = $('<div class="coordinate-picker-bottom-controls">').append($okBtn, ' ', $cancelBtn);



    var $qtipTarget = this.$root;
    var rectShape = null;
    var circleShape = null;
    var infoBubbles = [
      new InfoBubble(this.options.infoBubbleOptions),
      new InfoBubble(this.options.infoBubbleOptions)]
    var drawStartPoint = null;
    var drawStartLatLng = null;
    var map = null;
    // GMaps overlay for coordinate translation
    var ov = new google.maps.OverlayView();
    ov.onAdd = function () {
    };
    ov.draw = function () {
    };
    ov.onRemove = function () {
    };
    // Set to null, "rect" or "circle"
    var drawingMode = null;
    function setDrawingMode(mode) {
      drawingMode = mode;
      if (drawingMode) {
        $mapOverlay.show();
      } else {
        $mapOverlay.hide();
      }
      $rectBtn.toggleClass('active', drawingMode === 'rect');
      $circleBtn.toggleClass('active', drawingMode === 'circle');
      $panBtn.toggleClass('active', !drawingMode);
    }
    function enableRectMode() {
      setDrawingMode('rect');
    }
    function enableCircleMode() {
      setDrawingMode('circle');
    }
    function disableDrawingMode() {
      setDrawingMode(null);
    }
    $rectBtn.click(enableRectMode);
    $circleBtn.click(enableCircleMode);
    $panBtn.click(disableDrawingMode);

    /* Position is from mouse event evt.pageX, evt.pageY */
    function getPoint(pageX, pageY) {
      var offset = $map.offset();
      var posX = Math.max(0, pageX - offset.left);
      var posY = Math.max(0, pageY - offset.top);
      posX = Math.min(posX, $map.width());
      posY = Math.min(posY, $map.height());
      return new google.maps.Point(posX, posY);
    }
    /* Turn a point into a LatLng */
    function getLatLng(point) {
      var prj = ov.getProjection();
      return prj.fromContainerPixelToLatLng(point);
    }
    /* Print a LatLng for the infobubble */
    function printLatLng(latLng) {
      var lat = latLng.lat().toFixed(3);
      var lon = latLng.lng().toFixed(3);
      var latSuffix = (lat >= 0 ? "&deg; N" : "&deg; S");
      var lonSuffix = (lon >= 0 ? "&deg; E" : "&deg; W");
      return "" + Math.abs(lat) + latSuffix + " x " + Math.abs(lon) + lonSuffix;
    }

    function updateRect(point) {
      var left = Math.min(point.x, drawStartPoint.x);
      var right = Math.max(point.x, drawStartPoint.x);
      var top = Math.min(point.y, drawStartPoint.y);
      var bottom = Math.max(point.y, drawStartPoint.y);
      // console.log("("+left+","+bottom+")-("+right+","+top+")");
      rectShape.setBounds(new google.maps.LatLngBounds(
        getLatLng(new google.maps.Point(left, bottom)),
        getLatLng(new google.maps.Point(right, top))
      ));
      var latLng = getLatLng(point);
      infoBubbles[1].setContent(printLatLng(latLng));
      infoBubbles[1].setPosition(latLng);
    }

    function updateCircle(point) {
      var latLng = getLatLng(point);
      var distance = google.maps.geometry.spherical.computeDistanceBetween(
        drawStartLatLng, latLng);
      circleShape.setRadius(distance);
      infoBubbles[1].setContent(printLatLng(latLng));
      infoBubbles[1].setPosition(latLng);
    }

    function startRect(n, s, e, w) {
      var ne = new google.maps.LatLng(n, e);
      var sw = new google.maps.LatLng(s, w);
      var rectOptions = {
        map: map,
        bounds: new google.maps.LatLngBounds(ne, sw)
      };
      if (rectShape) {
        rectShape.setOptions(rectOptions);
      } else {
        rectShape = new google.maps.Rectangle(
          $.extend({}, _this.options.rectangleOptions, rectOptions)
        );
      }
      infoBubbles[0].setContent(printLatLng(ne));
      infoBubbles[0].setPosition(ne);
      infoBubbles[0].setMap(map);
      infoBubbles[0].open();
      infoBubbles[1].setContent(printLatLng(sw));
      infoBubbles[1].setPosition(sw);
      infoBubbles[1].setMap(map);
      infoBubbles[1].open();
    }

    function startCircle(lat, lon, r) {
      var center = new google.maps.LatLng(lat, lon);
      var circleOptions = $.extend({}, _this.options.circleOptions, {
        map: map,
        center: center,
        radius: r
      });
      if (circleShape) {
        circleShape.setOptions(circleOptions);
      } else {
        circleShape = new google.maps.Circle(circleOptions);
      }
      infoBubbles[0].setContent(printLatLng(center));
      infoBubbles[0].setPosition(center);
      infoBubbles[0].setMap(map);
      infoBubbles[0].open();
      infoBubbles[1].setContent(printLatLng(center));
      infoBubbles[1].setPosition(center);
      infoBubbles[1].setMap(map);
      infoBubbles[1].open();
    }

    function startDrawing(e) {
      if (rectShape) {
        rectShape.setMap(null);
      }
      if (circleShape) {
        circleShape.setMap(null);
      }
      drawStartPoint = getPoint(e.pageX, e.pageY);
      drawStartLatLng = getLatLng(drawStartPoint);
      if (drawingMode === 'rect') {
        startRect(drawStartLatLng.lat(), drawStartLatLng.lat(), drawStartLatLng.lng(), drawStartLatLng.lng());
      }
      else if (drawingMode === 'circle') {
        startCircle(drawStartLatLng.lat(), drawStartLatLng.lng(), 0);
      }
    }
    // Debounce the refresh method
    // 200ms timeout
    var DEBOUNCE = 200;
    var debounceTimeout = null;
    // last position received
    var lastPoint = null
    function keepDrawing(e) {
      lastPoint = getPoint(e.pageX, e.pageY);
      if (!debounceTimeout) {
        debounceTimeout = window.setTimeout(keepDrawingDebounced, DEBOUNCE);
      }
    }
    function keepDrawingDebounced() {
      if (drawingMode === 'rect') {
        updateRect(lastPoint);
      }
      else if (drawingMode === 'circle') {
        updateCircle(lastPoint);
      }
      debounceTimeout = null;
    }
    function stopDrawing(e) {
      keepDrawing(e);
      drawStartPoint = drawStartLatLng = lastPoint = null;
    }

    function initMap() {
      // Create map object
      map = new google.maps.Map($map[0], _this.options.mapOptions);
      // Add the overlay DOM after the OverlayView is added, to ensure it is on top
      ov.onAdd = function() {
        $map.append($mapOverlay);
      }
      ov.setMap(map);
      $mapOverlay.mousedown(function(e) {
        if (drawingMode) {
          startDrawing(e);
        }
      });
      $(document).mousemove(function(e) {
        if (drawingMode && drawStartPoint) {
          keepDrawing(e);
        }
      });
      $(document).mouseup(function(e) {
        if (drawingMode && drawStartPoint) {
          stopDrawing(e);
          disableDrawingMode();
        }
      });
      _this.map = map;
    }
    function initRect() {
      var locN = parseFloat(_this.$inputN.val());
      var locS = parseFloat(_this.$inputS.val());
      var locE = parseFloat(_this.$inputE.val());
      var locW = parseFloat(_this.$inputW.val());
      // Skip if no/invalid coordinates
      if (isNaN(locN) || isNaN(locS) || isNaN(locE) || isNaN(locW)) {
        return;
      }
      // Skip if these are global coordinates
      if (locN > 89 && locS < -89 && locE > 179 && locW < -179) {
        return;
      }
      var firstTime = !rectShape;
      startRect(locN, locS, locE, locW);

      // Zoom into current bounds on initial open
      if (firstTime) {
        google.maps.event.addListenerOnce(map, 'idle', function(r) {
          map.fitBounds(rectShape.getBounds());
          if (map.getZoom() > 5) {
            map.setZoom(5);
          }
        });
      }
    }
    function initCircle() {
      var centerLat = parseFloat(_this.$inputCenterLat.val());
      var centerLon = parseFloat(_this.$inputCenterLon.val());
      var maxRadius = parseFloat(_this.$inputMaxRadius.val());
      var minRadius = parseFloat(_this.$inputMinRadius.val());
      // Skip if no/invalid coordinates
      if (isNaN(centerLat) || isNaN(centerLon) || isNaN(maxRadius)) {
        return;
      }

      var firstTime = !circleShape;
      startCircle(centerLat, centerLon, maxRadius);

      // Zoom into current bounds on initial open
      if (firstTime) {
        google.maps.event.addListenerOnce(map, 'idle', function(r) {
          map.fitBounds(circleShape.getBounds());
          if (map.getZoom() > 5) {
            map.setZoom(5);
          }
        });
      }
    }

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
          api.elements.content.empty().append($drawPanControls, $map, $okCancelControls);
          // Temporarily show the tooltip so we don't get rendering bugs in GMaps
          tooltip.show();
          initMap();
          // Hide the tooltip again now we're done
          tooltip.hide();
        },
        show: function(event, api) {
          // Initialize/update the current selection
          initRect();
          // If there is no selection, start in drawing mode
          if (rectShape) { disableDrawingMode(); }
          else { enableRectMode(); }
        }
      }
    });
    $cancelBtn.click(function() {
      $qtipTarget.qtip('hide');
    });
    $okBtn.click(function() {
      $qtipTarget.qtip('hide');
      if (rectShape) {
        var bounds = rectShape.getBounds();
        _this.$inputS.val(bounds.getSouthWest().lat().toFixed(3));
        _this.$inputW.val(bounds.getSouthWest().lng().toFixed(3));
        _this.$inputN.val(bounds.getNorthEast().lat().toFixed(3));
        _this.$inputE.val(bounds.getNorthEast().lng().toFixed(3));
      }
      if (circleShape) {
        _this.$input
      }
    });
  };

  $.fn.coordinate_picker = function(options) {
    var picker = new Picker(this, options);
    $(this).data('coordinate_picker', picker);
    return this;
  };

})(jQuery, google, InfoBubble);
