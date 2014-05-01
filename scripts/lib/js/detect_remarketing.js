function detectGoogleRemarketing(doc) {
  var google_remarketing_flag_1 = false;
  var google_remarketing_flag_2 = false;
  var google_remarketing_flag_3 = false;
  var google_conversion_id = '';
  var google_conversion_label = '';
  var adroll_retargeting_flag = false;
  var adroll_adv_id = '';
  var adroll_pix_id = '';
  var scripts = doc.getElementsByTagName('script');
  for ( var j = 0; j < scripts.length; j++) {
    var script = scripts[j];
    var script_src = script.getAttribute('src');
    if (script_src && script_src.indexOf('googleadservices.com/pagead/conversion.js') >= 0) {
      google_remarketing_flag_1 = true;
    }
    var content = script.innerHTML;
    if (content.indexOf('google_remarketing_only = true') >= 0) {
      google_remarketing_flag_2 = true;
    }
    if (content.indexOf('google_conversion_id') >= 0) {
      var index1 = content.indexOf('google_conversion_id');
      var index2 = content.indexOf(';', index1);
      google_conversion_id = content.substring(index1, index2);
      index1 = content.indexOf('google_conversion_label', index2);
      if (index1 >= 0) {
        index2 = content.indexOf(';', index1);
        google_conversion_label = content.substring(index1, index2);
      }
      // console.log('XXX\t'+index1+'\t'+index2+'\n'+google_conversion_id+'\n'+google_conversion_label);
    }
    if (content.indexOf('adroll_adv_id') >= 0) {
      adroll_retargeting_flag = true;
      var index1 = content.indexOf('adroll_adv_id');
      var index2 = content.indexOf(';', index1);
      adroll_adv_id = content.substring(index1, index2);
      index1 = content.indexOf('adroll_pix_id', index2);
      if (index1 >= 0) {
        index2 = content.indexOf(';', index1);
        adroll_pix_id = content.substring(index1, index2);
      }
      // console.log('<MSG><RTG>\t' + adroll_adv_id + '<-+->' + adroll_pix_id);
      // console.log('XXX\t'+index1+'\t'+index2+'\n'+adroll_adv_id+'\n'+adroll_pix_id);
    }
    if (google_remarketing_flag_1 && google_remarketing_flag_2
        && adroll_retargeting_flag) {
      break;
    }
  }
  if (google_remarketing_flag_1 && google_remarketing_flag_2) {
    return true;
    //console.log('<MSG><RTG>\t' + google_conversion_id + '<-+->' + google_conversion_label);
  }

  // console.log('YYYY\t'+google_remarketing_flag_1+google_remarketing_flag_2+google_remarketing_flag_3);
  var imgs = doc.getElementsByTagName('img');
  for ( var j = 0; j < imgs.length; j++) {
    var img = imgs[j];
    var src = img.src;
    // console.log('YYYY\t'+src);
    if (src.indexOf('googleadservices.com/pagead/conversion') >= 0
        || src.indexOf('doubleclick.net/pagead/conversion') >= 0
        || src.indexOf('doubleclick.net/pagead/viewthroughconversion') >= 0) {
      if (src.indexOf('value=') >= 0) {
        google_remarketing_flag_3 = true;
      }
      if (google_remarketing_flag_1 && !google_remarketing_flag_2
          && !google_remarketing_flag_3) {
        return true
        //console.log('<MSG><RTG>\t' + google_conversion_id + '<-+->' + google_conversion_label);
      }
      break;
    }
  }
  
  // Handle iframes
  var iframes = doc.querySelectorAll('iframe');
  for (var j = 0; j < iframes.length; j ++) {
    result = detectGoogleRemarketing(iframes[j].contentDocument);
    if (result == true)
      return true;
  }
  
  return false;
}
ret = detectGoogleRemarketing(document);
if (ret == true)
  console.log("<MSG><RESULT>\tRemarketing script detected");
else
  console.log("<MSG><RESULT>\tRemarketing script not detected");
console.log('__quit__detect_remarketing.js')
