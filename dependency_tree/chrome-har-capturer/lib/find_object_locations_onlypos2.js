// Call this by injecting: document.body.appendChild(document.createElement("script")).src = "http://twitsper.cs.ucr.edu/loadtimer/site_test/find_object_locations.js";
var main_url = document.documentURI;
var mainContainer = document.body;
//var main_url = window.mikes_main_url;

var id = '2013_09_04_50UrlsForDaimeng';
var main_url_createdate = Math.floor(new Date().getTime() / 1000);

var resource_records = [];

function save_data(main_url_createdate, id, main_url, object_url, x1, y1, x2, y2, is_css_bg, visible, display, repeat_type, dom_object_type) {
  if (!(object_url == undefined || object_url == ""))
  {
    var record = {"main_url_createdate": main_url_createdate,
                    "id": id, "main_url": main_url,
                    "object_url": object_url, "x1": x1,
                    "y1": y1, "x2": x2, "y2": y2,
                    "is_css_bg": is_css_bg, "visible": visible,
                    "display": display, "repeat_type": repeat_type,
                    "dom_object_type": dom_object_type};

    //var record = [main_url_createdate, id, main_url, object_url, x1, y1, x2, y2, is_css_bg, visible, display, repeat_type, dom_object_type];
    resource_records.push(record);
  }
}

function find_objects(doc, extra_left, extra_top) {
  var types = ["IMG","EMBED","IFRAME"];
  //var types = ["IMG","EMBED","IFRAME","OBJECT"];
  //var types = ["IMG","SCRIPT","EMBED","IFRAME","OBJECT"];
  //var types = ["*"];
  var type_num = 0;
  for (var type_num=0; type_num < types.length; type_num++) {
    var all = doc.getElementsByTagName(types[type_num]);
    for (var i=0, max=all.length; i < max; i++) {
      var obj = all[i];
      if (obj.offsetWidth == undefined || obj.offsetHeight == undefined) {
        continue;
      }

      var visible = document.deepCss(obj,'visibility');
      var display = document.deepCss(obj,'display');
      if (visible.toLowerCase() == 'hidden') {
       visible = 0; 
      }
      else {
        visible = 1;
      }
      if (display.toLowerCase() == 'none') {
        display = 0; 
      }
      else {
        display = 1;
      }


      var left_top = findPos(obj);
      var x1 = left_top[0] + extra_left;
      var y1 = left_top[1] + extra_top;
      var width = parseInt(obj.offsetWidth);
      var height = parseInt(obj.offsetHeight);
      var x2 = parseInt(x1) + width;
      var y2 = parseInt(y1) + height;
      var dom_object_type = obj.nodeName;
      var object_url = obj.src;

      if (obj.nodeName == "IFRAME") {
        try {
          var loc = obj.contentDocument.location.href;
          var iframe_doc = obj.contentDocument;
          var iframe_left = obj.offsetLeft;
          var iframe_top = obj.offsetTop;
          
          save_data(main_url_createdate, id, main_url, object_url, x1, y1, x2, y2, 0, visible, display, "null", dom_object_type);
          find_objects(iframe_doc, x1, y1);
          continue;
        }
        catch(e) { // cross-domain iframe, just settle for html dimentions
          save_data(main_url_createdate, id, main_url, object_url, x1, y1, x2, y2, 0, visible, display, "null", dom_object_type);
          continue;
        }
      }
      else { //normal object
          save_data(main_url_createdate, id, main_url, object_url, x1, y1, x2, y2, 0, visible, display, "null", dom_object_type);
      }
    }
  }
}

function findPos(obj) {
  var curleft = curtop = 0;
  if (obj.offsetParent) {
    do {
      curleft += obj.offsetLeft;
      curtop += obj.offsetTop;
    } while (obj = obj.offsetParent);
  }
  return [curleft,curtop];
}

Array.prototype.contains = function(obj) {
  var i = this.length;
  while (i--) {
    if (this[i] == obj) {
      return true;
    }
  }
  return false;
}

function getallBgimages() {
  var types = ["*"];
  var type_num = 0;
  for (var type_num=0; type_num < types.length; type_num++) {
    var type = types[type_num];

    A = document.getElementsByTagName(type);
    A = [].slice.call(A, 0, A.length);
    while(A.length) {
      var obj = A.shift();
      url = document.deepCss(obj,'background-image');
      if(url) url=/url\(['"]?([^")]+)/.exec(url) || [];

      object_url = url[1];
      if(object_url) {
        var repeat_type = document.deepCss(obj,'background-repeat');
        var visible_value = document.deepCss(obj,'visibility');
        var display_value = document.deepCss(obj,'display');
        if (visible_value.toLowerCase() == 'hidden') {
         visible_value = 0; 
        }
        else {
          visible_value = 1;
        }
        if (display_value.toLowerCase() == 'none') {
          display_value = 0; 
        }
        else {
          display_value = 1;
        }

        // Find background-position (used to determine sprites)
        var position_str = document.deepCss(obj,'background-position');
        position_str = position_str.split(" ");
        var x_str = position_str[0];
        var y_str = position_str[1];
        x_str = x_str.toLowerCase();
        y_str = y_str.toLowerCase();
         
        var percent = "%";
        if (y_str.slice(y_str.length-1, y_str.length) == percent){
          y_str = y_str.slice(0, y_str.length-1);
        }
        if (x_str.slice(x_str.length-1, x_str.length) == percent){
          x_str = x_str.slice(0, x_str.length-1);
        }

        var pixel = "px";
        if (x_str.slice(x_str.length-2, x_str.length) == pixel){
              x_str = x_str.slice(0,x_str.length-2);
        }
        if (y_str.slice(y_str.length-2, y_str.length) == pixel){
              y_str = y_str.slice(0,y_str.length-2);
        }
         
        var left_top = findPos(obj);
        var x1 = left_top[0];
        var y1 = left_top[1];
        var width = 0;
        var height = 0;
        if (obj.offsetWidth != undefined) {width = parseInt(obj.offsetWidth);}
        if (obj.offsetHeight != undefined) {height = parseInt(obj.offsetHeight);}
        var x2 = parseInt(x1) + width;
        var y2 = parseInt(y1) + height;
        var dom_object_type = obj.nodeName;
        var visible = "null";
        var display = "null";

        save_data(main_url_createdate, id, main_url, object_url, x1, y1, x2, y2, 1, visible, display, repeat_type, dom_object_type);
      }
    }
  }
}

document.deepCss= function(who, css){
  if (!who || !who.style) return '';
  var sty= css.replace(/\-([a-z])/g, function(a, b){
    return b.toUpperCase();
  });
  if(who.currentStyle){
    return who.style[sty] || who.currentStyle[sty] || '';
  }
  var dv= document.defaultView || window;
  return who.style[sty] || 
         dv.getComputedStyle(who,"").getPropertyValue(css) || '';
}

find_objects(document, 0, 0);
getallBgimages();
//document.mikes_location_info = resource_records.toJSON();
document.mikes_location_info = JSON.stringify(resource_records);
