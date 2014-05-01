var adblockMatcher = function(ad_db) {
  var self = this;
  this._ad_db = ad_db;

  this._checkUrlPattern = function(url, domain, filter) {
    var url_match = true;
    var url_exception = false;
    if (filter['address-part'] && filter['address-part'].length > 0) {
      url_match = false;
      for (var i = 0; i < filter['address-part'].length; i++) {
        try {
          var reg = new RegExp(filter['address-part'][i]);
          if (reg.test(url)) {
            url_match = true;
            break;
          }
        } catch (e) {
          // console.log(filter);
          return false;
        }

      }
    }
    else if (filter['domain']) {
      url_match = false;
      try {
        var reg = new RegExp(filter['domain']);
        if (reg.test(url))
          url_match = true;
      } catch (e) {
        // console.log(filter);
        return false
      }
    }
    else if (filter['address-exact']) {
      url_match = (url == filter['address-exact']);
    }
    if (filter['address-exception'] && filter['address-exception'].length > 0) {
      url_exception = false;
      for (var i = 0; i < filter['address-exception'].length; i++) {
        try {
          var reg = new RegExp(filter['address-exception'][i]);
          if (reg.test(url)) {
            url_exception = true;
            break;
          }
        } catch (e) {
          // console.log(filter);
          return false
        }
      }
    }
    return url_match && !url_exception;
  }
  
  this._checkUrlFilter = function(url, domain, element, third_party, filter) {
    // Match URL
    var url_match = self._checkUrlPattern(url, domain, filter);

    // Check Options
    var option_or = false;
    var option_or_count = 0;
    var option_and = true;
    var domain_match = true;
    var domain_exception = false;
    for ( var i in filter['options']) {
      switch (i) {
      case "script": {
        option_or_count++;
        if (filter['options'][i] == true || filter['options'][i] == "True")
          option_or = option_or || (element.tagName == "SCRIPT");
        else
          option_or = option_or || (element.tagName != "SCRIPT");
        break;
      }
      case "image": {
        option_or_count++;
        if (filter['options'][i] == true || filter['options'][i] == "True")
          option_or = option_or || (element.tagName == "IMG");
        else
          option_or = option_or || (element.tagName != "IMG");
        break;
      }
      case "stylesheet": {
        option_or_count++;
        if (filter['options'][i] == true || filter['options'][i] == "True")
          option_or = option_or || (element.tagName == "STYLE");
        else
          option_or = option_or || (element.tagName != "STYLE");
        break;
      }
      case "object": {
        option_or_count++;
        if (filter['options'][i] == true || filter['options'][i] == "True")
          option_or = option_or
              || (element.tagName == "OBJECT" || element.tagName == "EMBED");
        else
          option_or = option_or
              || (element.tagName != "OBJECT" && element.tagName != "EMBED");
        break;
      }
      case "subdocument": {
        option_or_count++;
        if (filter['options'][i] == true || filter['options'][i] == "True")
          option_or = option_or
              || (element.tagName == "FRAME" || element.tagName == "IFRAME");
        else
          option_or = option_or
              || (element.tagName != "FRAME" && element.tagName != "IFRAME");
        break;
      }
      case "third-party": {
        if (filter['options'][i] == true || filter['options'][i] == "True")
          option_and = option_and && third_party;
        else
          option_and = option_and && !third_party;
        break;
      }
      case "domains": {
        domain_match = false;
        for ( var j = 0; j < filter['options']["domains"].length; j++) {
          if (domain.indexOf(filter['options']["domains"][j]) >= 0) {
            domain_match = true;
            break;
          }
        }
        break;
      }
      case "domains-exception": {
        domain_exception = false;
        for ( var j = 0; j < filter['options']["domains-exception"].length; j++) {
          if (domain.indexOf(filter['options']["domains-exception"][j]) >= 0) {
            domain_exception = true;
            break;
          }
        }
        break
      }
      default: {
        break;
      }
      }
    }
    // If no or-condition-option at all
    if (option_or_count == 0)
      option_or = true;

    return url_match && option_or && option_and && domain_match && !domain_exception;
  }

  this._checkElementSelector = function(element, selector) {
    if (!element)
      return false;
    
    // Selector
    var selector_match = true;
    if (selector['id']) {
      selector_match = (element.id.indexOf(selector['id']) >= 0)
    } else if (selector['tag']) {
      selector_match = (selector['tag'].toUpperCase() == element.tagName)
    } else if (selector['class']) {
      selector_match = false;
      for (var i = 0; i < element.classList.length; i++) {
        if (element.classList[i] == selector['class']) {
          selector_match = true;
          break;
        }
      }
    }
    if (!selector_match)
      return false;
    
    // Attributes
    var attr_match = true;
    for (var i = 0; i < selector['attributes'].length; i++) {
      attribute = selector['attributes'][i];
      var value_element = element.getAttribute(attribute['key']);
      var value_selector = attribute['value'];
      
      if (value_selector == "") {
        if (value_element == null) {
          attr_match = false;
          break;
        }
      } else if (attribute['first']) {
        if (value_element == null || value_element.indexOf(value_selector) != 0) {
          attr_match = false;
          break;
        }
      } else if (attribute['last']) {
        if (value_element == null || value_element.indexOf(value_selector) < 0 || value_element.indexOf(value_selector) != value_element.length - value_selector.length ) {
          attr_match = false;
          break;
        }
      } else if (attribute['include']) {
        if (value_element == null || value_element.indexOf(value_selector) < 0) {
          attr_match = false;
          break;
        }
      } else {
        if (value_element == null || value_element != value_selector) {
          attr_match = false;
          break;
        }
      }
    }
    return selector_match && attr_match;
  }
  
  this._checkElementFilter = function(element, domain, filter) {
    // Match URL
    var urlMatch = self._checkUrlPattern(domain, domain, filter);
    if (!urlMatch)
      return false;
    
    // Element
    if (filter['element']['selector']) {
      return self._checkElementSelector(element, filter['element']['selector']);
    }
    else if (filter['element']['enclosed-in']) {
      var temp = element;
      var elemMatch = true;
      for (var i = 0; i < filter['element']['enclosed-in'].length - 1; i++) {
        if (!self._checkElementSelector(temp, filter['element']['enclosed-in'][i])) {
          elemMatch = false;
          break;
        }
        var enclosed_element = false;
        for (var j = 0; j < temp.children.length; j++) {
          if (!self._checkElementSelector(temp.children[j], filter['element']['enclosed-in'][i + 1])) {
            enclosed_element = true;
            temp = temp.children[j];
            break;
          }
        }
        if (!enclosed_element) {
          elemMatch = false;
          break;
        }
          
      }
      return elemMatch;
    }
    else if (filter['element']['preceded-by']) {
      var temp = element;
      var elemMatch = true;
      for (var i = 0; i < filter['element']['preceded-by'].length; i++) {
        if (!self._checkElementSelector(temp, filter['element']['preceded-by'][i])) {
          elemMatch = false;
          break;
        } else {
          temp = temp.nextElementSibling;
        }
      }
      return elemMatch;
    }
  }

  this.matchUrl = function(url, domain, element, third_party) {
    var match = false;
    var exception = false;
    
    // Url match
    for (var i = 0; i < self._ad_db['url-matcher'].length; i ++) {
      if (self._checkUrlFilter(url, domain, element, third_party, self._ad_db['url-matcher'][i])) {
        match = true;
        //console.log(url);
        //console.log("matched by");
        //console.log(self._ad_db['url-matcher'][i]);
        break;
      }
    }
    return match;
    
    /*
    if (!match)
      return false;
    // Url exception
    for (var i = 0; i < self._ad_db['url-exception'].length; i ++) {
      if (self._checkUrlFilter(url, domain, element, third_party, self._ad_db['url-exception'][i])) {
        exception = true;
        break;
      }
    }
    return !exception;
    */
  }

  this.matchElement = function(element, domain) {
    var match = false;
    var elemhide = false;
    var exception = false;
    
    // Elemhide
    for (var i = 0; i < self._ad_db['elemhide'].length; i ++) {
      if (self._checkUrlFilter(domain, domain, element, false, self._ad_db['elemhide'][i])) {
        elemhide = true;
        break;
      }
    }
    if (elemhide)
      return false;
    
    // Element match
    for (var i = 0; i < self._ad_db['element-matcher'].length; i ++) {
      if (self._checkElementFilter(element, domain, self._ad_db['element-matcher'][i])) {
        match = true;
        //console.log(element);
        //console.log("matched by");
        //console.log(self._ad_db['element-matcher'][i]);
        break;
      }
    }
    return match;
    /*
    if (!match)
      return false;
    
    // Element exception
    for (var i = 0; i < self._ad_db['element-exception'].length; i ++) {
      if (self._checkElementFilter(element, domain, self._ad_db['element-exception'][i])) {
        exception = true;
        break;
      }
    }
    return !exception;
    */
  }
}