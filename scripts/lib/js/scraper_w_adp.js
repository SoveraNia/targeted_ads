// ====================================================
// UTILITY FUNCTIONS
// ====================================================

var dbgmsg = false;
var extract_iframe = false;

/**
 * Converts a Javascript object array that contains HTML element to a JSON string
 * 
 * @param array
 * @returns {String}
 */
function array2JSON(array) {
  var result = '[';
  var FIRST = true
  for (var i = 0; i < array.length; i++) {
    if (!FIRST)
      result += ',';
    else
      FIRST = false;
    result += '{';
    var first = true;
    for (var j in array[i]) {
      if (!first)
        result += ',';
      else
        first = false;
      if (array[i][j])
        if (array[i][j].constructor == Object || array[i][j].constructor == Array)
          result += '"' + j + '":' + JSON.stringify(array[i][j]) + '';
        else
          result += '"' + j + '":"' + array[i][j].toString().replace(/"/g, '\\"') + '"';
      else
        result += '"' + j + '":"UNDEFINED"';
    }
    result += '}'
  }
  result += ']';
  return result;
}

// mainly used to get the domain of a url, similar function as
// extractDomainFromURL
function parseUri(str) {  
  var o = parseUri.options, m = o.parser[o.strictMode ? "strict" : "loose"]
      .exec(str), uri = {}, i = 14;

  while (i--)
    uri[o.key[i]] = m[i] || "";

  uri[o.q.name] = {};
  uri[o.key[6]] = "http://" + uri[o.key[6]];
  uri[o.key[12]].replace(o.q.parser, function($0, $1, $2) {
    if ($1)
      uri[o.q.name][$1] = $2;
  });

  return uri;
};
parseUri.options = {
  strictMode : false,
  key : [ "source", "protocol", "authority", "userInfo", "user", "password",
      "host", "port", "relative", "path", "directory", "file", "query",
      "anchor" ],
  q : {
    name : "queryKey",
    parser : /(?:^|&)([^&=]*)=?([^&]*)/g
  },
  parser : {
    strict : /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
    loose : /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
  }
};

/**
 * Given a DOM element, extract the url that would be requested by loading the element
 * 
 * @param element
 * @returns
 */
function getElementURL(element) {
  var url;
  switch (element.localName.toUpperCase()) {
  case 'OBJECT': {
    url = element.data;
    if (!url) {
      var params = element.querySelectorAll(["param[name=\"movie\"]", "param[name=\"Movie\"]"]);
      if (params[0]) {
        url = params[0].value;
        break;
      }
      params = element.querySelectorAll(["param[name=\"src\"]", "param[name=\"Src\"]"]);
      if (params[0]) {
        url = params[0].value;
        break;
      }
    }
    if (!url)
      url = element.src || element.href;
    break;
  }
  default:
    url = element.src || element.href;
    break;
  }
  return url;
}

/**
 * Transform relative url to absolute url
 * 
 * @param url
 * @returns
 */
function relativeToAbsoluteURL(url) {
  if (!url || url.match(/^http/i))
    return url;
  if (url[0] == '/')
    return document.location.protocol + '//' + document.location.host + url;
  var base = document.baseURI.match(/.+\//);
  if (!base)
    return document.baseURI + '/' + url;
  return base[0] + url;
}

/**
 * HTTP GET
 * 
 * @param url
 * @returns
 */
function syncGet(url) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', url, false);
  xhr.send(null);
  return xhr.responseText;
}

/**
 * Given a DOM element, extract all its attributes that may contain ad url
 * 
 * @param element
 * @returns {Array}
 */
function getElementAdUrls(element) {
  var urls = [];
  var url;
  switch (element.localName.toUpperCase()) {
  case 'OBJECT': {
    if (element.data)
      urls.push(element.data);
    if (element.src || element.href)
      urls.push(element.src || element.href);
    var params = element.querySelectorAll([ "param[name=\"movie\"]", "param[name=\"Movie\"]" ]);
    if (params[0])
      urls.push(params[0].value);
    params = element.querySelectorAll([ "param[name=\"src\"]", "param[name=\"Src\"]" ]);
    if (params[0])
      urls.push(params[0].value);
    params = element.querySelectorAll([ "param[name=\"flashvars\"]", "param[name=\"FlashVars\"]" ]);
    if (params[0]) {
      // Split flashvars
      var values = params[0].value.split('&');
      for (var i = 0; i < values.length; i++) {
        value = values[i];
        try {
          value = decodeURIComponent(value);
          urls.push(value);
        } catch (e) {
          urls.push(value);
        }
      }
    }
    break;
  }
  case 'EMBED': {
    if (element.getAttribute('flashvars')) {
      var values = element.getAttribute('flashvars').split('&');
      for (var i = 0; i < values.length; i++) {
        value = values[i];
        try {
          value = decodeURIComponent(value);
          urls.push(value);
        } catch (e) {
          urls.push(value);
        }
      }
    }
    if (element.src || element.href) {
      urls.push(element.src || element.href);
    }
    break;
  }
  default:
    if (element.src || element.href) {
      urls.push(element.src || element.href);
    }
    break;
  }
  return urls;
}

/**
 * Given a document, extract all possible ads within. Storing the urls of the
 * ads in ad_urls
 * 
 * @param doc
 * @param result_obj_list
 * @param level
 */
function getDocumentAdSrc(doc, level, result_obj_list, incomplete_iframes) {
  if (!doc)
    return;

  var nodes = doc.querySelectorAll('a > img, embed, object');
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].tagName == 'IMG') {
      var href = nodes[i].parentNode.href;
      if (href && isUrlAd(href) && isElementAd(nodes[i])) {
        result_obj_list.push({"url": href, "element": nodes[i].parentNode, "ad_urls": [href]})
      }
    } else if (nodes[i].tagName = 'EMBED') {
      var flashvars = nodes[i].getAttribute('flashvars');
      if (flashvars && isUrlAd(flashvars) && isElementAd(nodes[i])) {
        result_obj_list.push({"url": flashvars, "element": nodes[i], "ad_urls": flashvars.split('&')})
      }
    } else if (nodes[i].tagName = 'OBJECT') {
      var flashvars = nodes[i].getAttribute('flashvars');
      if (flashvars && isUrlAd(flashvars) && isElementAd(nodes[i])) {
        result_obj_list.push({"url": flashvars, "element": nodes[i], "ad_urls": flashvars.split('&')});
        continue;
      }
      var params = nodes[i].querySelectorAll(["param[name=\"flashvars\"]", "param[name=\"FlashVars\"]"]);
      if (params[0]) {
        flashvars = params[0].value;
        if (flashvars && isUrlAd(flashvars) && isElementAd(nodes[i])) {
          result_obj_list.push({"url": flashvars, "element": nodes[i], "ad_urls": flashvars.split('&')});
        }
      }
    }
  }
  var iframes = doc.querySelectorAll('iframe');
  for (var i = 0; i < iframes.length; i++) {
    if (iframes[i].contentDocument.readyState == 'complete') {
      getDocumentAdSrc(iframes[i].contentDocument, level + 1, result_obj_list, incomplete_iframes);
    } else {
      incomplete_iframes.push(iframes[i]);
    }
  }
  
  /*
  // Get ad urls
  // non-iframe ads
  var elements = doc.querySelectorAll('object, embed, a > img');
  for ( var i = 0; i < elements.length; i++) {
    element = elements[i];
    var url = getElementURL(element);
    if (url)
      url = relativeToAbsoluteURL(url);
    // console.log('<Main>['+i+']:'+element.tagName);
    getAdSrc(element, ad_urls);
  }

  // iframe ads
  var elements = doc.querySelectorAll('iframe');
  for ( var i = 0; i < elements.length; i++) {
    element = elements[i];
    var url = getElementURL(element);
    if (url)
      url = relativeToAbsoluteURL(url);
    
    if (!isElementAd(element) && !isUrlAd(url, element)) {
      if (element.contentDocument.readyState == 'complete') {
        getDocumentAdSrc(element.contentDocument, level + 1, ad_urls);
      } else {
        incomplete_iframes.push(element.contentDocument);
      }
      continue;
    }
    ad_urls.push({
      "element" : element,
      "url" : url
    });
  }
  */
}

/**
 * Given an DOM element, determine whether it represents an ad.
 * 
 * @param element
 */
function isElementAd(element) {
  // Without ADP, this is to check whether the element is visible or large enough
  var style = window.getComputedStyle(element);
  var height = parseInt(style.height);
  var width = parseInt(style.width);
  if (height >= 50 || width >= 50)
    return true;
  else
    return false;
  
  /* ADP approach
  if (!element)
    return false;
  
  if (!adMatcher)
    return true;
  
  return adMatcher.matchElement(element, domain);
  */
}

/**
 * Given an URL and its context, determine whether it represents an ad.
 * 
 * @param url
 * @param location
 */
function isUrlAd(url, element) {
  if (!url)
    return false;
  
  for (var j = 0; j < ad_providers.length; j++) {
    if (url.indexOf(ad_providers[j]) >= 0) {
      return true;
    }
  }
  return false;
  
  /* ADP approach
  if (!adMatcher)
    return true;
  
  // First Party
  if (url.indexOf(domain) >= 0) {
    return adMatcher.matchUrl(url, domain, element, false);
  } else {
    return adMatcher.matchUrl(url, domain, element, true);
  }
  */
}

/**
 * Extract the landing page url if the ad is clicked. Store the landing page url
 * in the ad_urls list.
 * 
 * @param ad_urls
 * @returns
 */
function computeAdLandingPages(ads) {
  var ret = []
  for ( var i = 0; i < ads.length; i++) {
    ads[i]['possible_landing_urls'] = []
    for (var j = 0; j < ads[i].ad_urls.length; j ++) {
      ads[i]['possible_landing_urls'] = ads[i]['possible_landing_urls'].concat(extractLandingPageFromUrlAlt(ads[i].ad_urls[j]));
      var landing = extractLandingPageFromUrl(ads[i].ad_urls[j]);
      if (landing && landing != "") {
        ads[i]['landing_url'] = landing;
        break;
      }
    }
    
    if (ads[i]['landing_url']) {
      ads[i]['landing_domain'] = parseUri(ads[i]['landing_url']).host;
      //ads[i]['landing_url_category'] = getLandingPageCategory(ads[i]['landing_domain']);
      ads[i]['landing_url_category'] = getLandingPageCategory(ads[i]['landing_url'].split(/[&\?]+/)[0]);
      ret.push(ads[i]);
      continue;
    }
    
    /*
    ads[i]['landing_url'] = extractLandingPageFromElement(ads[i].element);
    
    if (ads[i]['landing_url']) {
      ads[i]['landing_domain'] = parseUri(ads[i]['landing_url']).host;
      //ads[i]['landing_url_category'] = getLandingPageCategory(ads[i]['landing_domain']);
      ads[i]['landing_url_category'] = getLandingPageCategory(ads[i]['landing_url'].split(/[&\?]+/)[0]);
      ret.push(ads[i]);
      continue;
    }
    */
  }
  return ret;
}

function matchException(url) {
  for ( var l = 0; l < landing_pattern.exceptions.length; l++) {
    if (url.indexOf(landing_pattern.exceptions[l]) >= 0) {
      if (dbgMsg)
        console.log("<MSG><DEBUG>\tException detected: " + landing_pattern.exceptions[l]);
      return true;
    }
  }
  return false;
}

function matchLandingUrl(url, pattern) {
  var original_url = url;
  // Enumerate patterns
  for ( var k = 0; k < pattern.url_match.length; k++) {
    var reg = new RegExp(pattern.url_match[k], 'i');
    // console.log(reg);
    if (!original_url.match(reg))
      continue;
    var splited_urls = original_url.split(original_url.match(reg)[0]);
    if (splited_urls.length >= 2) {
      for ( var jk = 1; jk < splited_urls.length; jk++) {
        var index = splited_urls[jk].lastIndexOf('http');
        if (index < 0) {
          continue;
        } else if (index > 5) {
          splited_urls[jk] = splited_urls[jk].substring(index);
        }
        try {
          var landing_url = decodeURIComponent(splited_urls[jk].replace(
              /^\/url\//, '').replace(re_unescape, '$1'))
        } catch (e) {
          var landing_url = splited_urls[jk].replace(/^\/url\//, '').replace(
              re_unescape, '$1')
        }
        // Extract landing domain from url
        var landing_host = parseUri(landing_url).host;
        if (!landing_host)
          continue;
        // Exception detection
        var iterate_flag = true;
        if (landing_host.length < 10 || matchException(landing_host))
          iterate_flag = false;
        if (iterate_flag)
          return landing_url;
      }
    }
  }
}

function matchLandingId(url, pattern) {
  for ( var i = 0; i < pattern.id_match.length; i++) {
    var regPattern = new RegExp(pattern.id_match[i].pattern, 'i');
    console.log(regPattern);
    if (url.match(regPattern)) {
      var matches = url.match(regPattern).slice(1);
      var connector = '&';
      if (pattern.id_match[i].connector)
        connector = pattern.id_match[i].connector;
      var landing_url = pattern.id_match[i].prefix + matches.join(connector);
      var landing_host = parseUri(landing_url).host;
      if (!landing_host)
        continue;
        
      // Exception detection
      var iterate_flag = true;
      if (landing_host.length < 10)
        iterate_flag = false;
      if (iterate_flag)
        return landing_url;
      return landing_url;
    }
  }
  return null
}

/**
 * Given a url, determine whether it contains patterns that suggests the landing page
 * of an ad
 * 
 * @param url
 * @returns
 */
function extractLandingPageFromUrl(url) {
  if (dbgMsg)
    console.log("<MSG><DEBUG>\tExtracting landing page from:" + url);
  try {
    var _url = decodeURIComponent(url);
  } catch (err) {
    console.log('URI Error.');
    var _url = url;
  }
  
  // Split parameters first
  // URI parameters is already splitted by '&' in getElementAdUrls
  // Here we are only splitting JSON parameters
  var parameters = _url.split(';');
  for (var i = 0; i < parameters.length; i++) {
    if (dbgMsg)
      console.log("<MSG><DEBUG>\tParameter: " + parameters[i]);
    
    // Try decode URI component
    var original_url = parameters[i];
    try {
      original_url = decodeURIComponent(parameters[i]);
    } catch (e) {
      ;
    }
    
    // Match against patterns
    for (var j = 0; j < landing_pattern.patterns.length; j++) {
      var id = landing_pattern.patterns[j].identifier;
      if (id == "GLOBAL" || _url.indexOf(id) >= 0) {
        var landing_url = matchLandingUrl(original_url, landing_pattern.patterns[j]);
        if (!landing_url)
          landing_url = matchLandingId(original_url, landing_pattern.patterns[j]);
        if (landing_url)
          return landing_url;
      }
    }
  }
  return null;
}

/**
 * Alternate version of extractLandingPageFromUrl
 * 
 * @param url
 * @returns
 */
function extractLandingPageFromUrlAlt(url) {
  // Decode URI components until there's no "http%"
  var _url = url
  try {
    while (_url.indexOf('http%') >= 0) {
      _url = decodeURIComponent(_url);
    }
  } catch (err) {
    console.log('URI Error.');
  }
  
  // Extract inline urls
  var urlPattern = /(http|https):\/\/[\w-\\.\/]+/g;
  var inline_urls = _url.match(urlPattern);
  
  // Match against ad providers
  var ret = []
  if (inline_urls) {
    for (var i = 0; i < inline_urls.length; i++) {
      var match = false;
      for ( var l = 0; l < ad_providers.length; l++) {
        if (inline_urls[i].indexOf(ad_providers[l]) >= 0) {
          match = true;
          break;
        }
      }
      if (!match) {
        ret.push(inline_urls[i]);
      }
    }
  }
  return ret;
}

/**
 * Given a DOM element, extract the landing page URL if the element is clicked
 * 
 * @param element
 */
/*
function extractLandingPageFromElement(element) {
  if (dbgMsg) {
    console.log("<MSG><DEBUG>\tExtracting landing page from:" );
    console.log(element);
  }
  if (element.tagName == "IFRAME") 
    var children = element.contentDocument.querySelectorAll(['a > img', 'object', 'embed', 'iframe']);
  else
    var children = element.querySelectorAll(['a > img', 'object', 'embed', 'iframe']);
  for (var i = 0; i < children.length; i++) {
    var urls = getElementAdUrls(children[i]);
    var result = null;
    for (var j = 0; j < urls.length; j ++) {
      var temp = extractLandingPageFromUrl(urls[j]);
      if (temp && temp != "") {
        result = temp;
        break;
      }
    }
    
    if (result)
      return result;
    if (children[i].tagName == "IFRAME") {
      result = extractLandingPageFromElement(children[i].contentDocument);
      return result;
    }
  }
  return "";
}
*/

/**
 * Given a url of an ad's landing page, determine the category of the url using
 * third-party API
 * 
 * @param url
 */
function getLandingPageCategory(url) {
  // AWIS
  // var accessKeyId = "AKIAJE4Z7LOVBPZWDP5A";
  // var secretAccessKey = "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";
  var phpCallUrl = "http://localhost/ad_detect/get_url_category.php";
  var callUrl = phpCallUrl + '?site=' + encodeURIComponent(url);
  // callUrl += '&accessKeyId=' + encodeURIComponent(accessKeyId) + '&secretAccessKey=' + encodeURIComponent(secretAccessKey);
  console.log("<MSG><DEBUG>\tCall Url\t" + callUrl);
  var xhr = new XMLHttpRequest();
  xhr.open('GET', callUrl, false);
  xhr.send(null);
  try {
    var result = JSON.parse(xhr.responseText);
    console.log(result);
    return result['Response']['UrlInfoResult']['Alexa']['Related']['Categories']['CategoryData'];
  } catch (e) {
    // Alchemy as backup plan
    var alchemy_api_key = "beeb8469c6f7d1a0c7344dcee236d3e8ca71d53c";
    var alchemy_api_url = "http://access.alchemyapi.com/calls/url/URLGetCategory";
    var call_url = alchemy_api_url + "?apikey=" + alchemy_api_key;
    call_url += "&url=" + encodeURIComponent(url);
    call_url += "&outputMode=json"
    
    var xhr = new XMLHttpRequest();
    xhr.open('GET', call_url, false);
    xhr.send(null);
    try {
      var result = JSON.parse(xhr.responseText);
      if (result.status == "OK") {
        return { source: "Alchemy", category: result.category };
      } else {
        return {};
      }
    } catch (e) {
      return {};
    }
  } 
}

// ====================================================
// MAIN & GLOBAL VARIABLES
// ====================================================

// Page Information
var address = document.URL;
var host = parseUri(address).host;
var domain;
if (host.match(/.*?\..*\./))
  domain = host.replace(host.match(/.*?\./)[0], "");
else
  domain = host.replace(host.match(/.*\/\//)[0], "");

// Debug Options
var dbgMsg = true;
var base_domain = "http://localhost/ad_detect/";
var re_unescape = /^[~!@#\$%\^&\*\(\)-_+=\{\}\[\]\|\\\/:;"'<>,\.\?`\s]+([\S\s]+)$/;
var re_simple_domain = /^(http:\/\/)([\w-]+\.)+[\w-]+/;

// Landing pattern database
var xhr = new XMLHttpRequest();
xhr.open('GET', base_domain + "/resources/landing_patterns.json", false);
xhr.send(null);
var landing_pattern = JSON.parse(xhr.responseText);

// Ad providers database
var xhr = new XMLHttpRequest();
xhr.open('GET', base_domain + "/resources/ad_providers.json", false);
xhr.send(null);
var ad_providers = JSON.parse(xhr.responseText);

var __result_obj_list;
var __result_ad_list;

/*
// Adblock rule database
var xhr = new XMLHttpRequest();
xhr.open('GET', base_domain + "resources/easylist_doubleclick.json", false);
xhr.send(null);
var ad_db = JSON.parse(xhr.responseText);

// Load adblock matcher
var script = document.createElement("script");
script.type = "text/javascript";
script.src = base_domain + "lib/matcher.js";
document.body.appendChild(script);

var adMatcher = null;
var interval = window.setInterval(function () {
  if (adblockMatcher) {
    adMatcher = new adblockMatcher(ad_db);
    window.clearInterval(interval);
    __main__();
  }
}, 100)
*/

function __main__() {
  // Main
  var main_time = Date.now();
  console.log('<MSG><URL>\t' + address);
  console.log('<MSG><HOST>\t' + host);

  var result_obj_list = [];
  var incomplete_iframe_list = [];
  
  getDocumentAdSrc(document, 0, result_obj_list, incomplete_iframe_list);
  var ad_extract_time = Date.now();
  console.log("<MSG><TIMING>\tAd extraction finished in: " + (ad_extract_time - main_time) + "ms");
  
  var landingPages = computeAdLandingPages(result_obj_list);
  var landing_compute_time = Date.now();
  console.log("<MSG><TIMING>\tLanding page computation finished in: " + (landing_compute_time - ad_extract_time) + "ms");
  
  console.log("<MSG><TIMING>\tAnalysis finished in: " + (landing_compute_time - main_time) + "ms");
  
  __result_obj_list = result_obj_list;
  __result_ad_list = landingPages;
  
  console.log("<MSG><RESULT>\tObject Detected:\t" + array2JSON(__result_obj_list));
  console.log("<MSG><RESULT>\tAd Detected:\t" + array2JSON(__result_ad_list));
  console.log("__quit__");
}
__main__();