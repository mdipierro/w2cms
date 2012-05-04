/**
   Developed by Massimo Di Pierro
   Released under the MIT license

   Usage:
   <script src="autolinks.js"></script>

   it automatically converts the url to links but when possible it embeds the object being linked.
   In particular it can embed images, videos, audio files, documents (it uses the google code player),
   as well as pages to a oembed service.   
   
   Google Doc Support
   ==================
   Microsoft Word (.DOC, .DOCX)
   Microsoft Excel (.XLS and .XLSX)
   Microsoft PowerPoint 2007 / 2010 (.PPTX)
   Apple Pages (.PAGES)
   Adobe PDF (.PDF)
   Adobe Illustrator (.AI)
   Adobe Photoshop (.PSD)
   Autodesk AutoCad (.DXF)
   Scalable Vector Graphics (.SVG)
   PostScript (.EPS, .PS)
   TrueType (.TTF)
   XML Paper Specification (.XPS)
   
   Oembed Support
   ==============
   flickr.com
   youtube.com
   hulu.com
   vimeo.com
   slideshare.net
   qik.com
   polleverywhere.com
   wordpress.com
   revision3.com
   viddler.com
**/

var autolinks = function() {
    var EMBED_MAPS = 
    [
     ['http://www.flickr.com/services/oembed/',/http:\/\/\S*?flickr.com\/\S*/],
     ['http://www.youtube.com/oembed',/http:\/\/\S*.youtu(\.be|be\.com)\/watch\S*/],
     ['http://www.hulu.com/api/oembed.json',/http:\/\/www.hulu.com\/watch\/\S*/],
     ['http://vimeo.com/api/oembed.json',/http:\/\/vimeo.com\/\S*/],
     ['http://www.slideshare.net/api/oembed/2',/http:\/\/www.slideshare.net\/[^\/]+\/\S*/],
     ['http://qik.com/api/oembed.json',/http:\/\/qik.com\/\S*/],
     ['http://www.polleverywhere.com/services/oembed/',/http:\/\/www.polleverywhere.com\/\w+\/\S+/],
     ['http://public-api.wordpress.com/oembed/',/http:\/\/\S+.wordpress.com\/\S+/],
     ['http://revision3.com/api/oembed/',/http:\/\/*.revision3.com\/\S+/],
     ['http://lab.viddler.com/services/oembed/',/http:\/\/\S+.viddler.com\/\S+/]
     ];
    
    var uuid = function() {
	var S4 = function() {
	    return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
	};
	return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
    };
    var image = function(url) {
	return '<img src="'+url+'" style="max-width:100%"/>';
    };
    var audio = function(url) {
	return '<audio controls="controls" style="max-width:100%"><source src="'+url+'" /></audio>';
    };
    var video = function(url) {
	return '<video controls="controls" style="max-width:100%"><source src="'+url+'" /></video>';
    };
    var doc = function(url) {
	return '<iframe src="http://docs.google.com/viewer?url='+encodeURIComponent(url)+
	'&embedded=true" style="max-width:100%"></iframe>';
    };
    var w2p =  function(url) {
	code = uuid();
	return '<div id="'+code+'"></div><script>\nweb2py_component("'+url+'","'+code+'");\n</script>';
    };
    
    var EXTENSION_MAPS = {
	'png': image,
	'gif': image,
	'jpg': image,
	'jpeg': image,
	'wav': audio,
	'ogg': audio,
	'mp3': audio,
	'mov': video,
	'mpe': video,
	'mp4': video,
	'mpg': video,
	'mpg2': video,
	'mpeg': video,
	'mpeg4': video,
	'movie': video,
	'load': w2p,
	'pdf': doc,
	'doc': doc,
	'docx': doc,
	'ppt': doc,
	'pptx': doc,
	'xls': doc,
	'xlsx': doc,
	'pages': doc,
	'ai': doc,
	'psd': doc,
	'xdf': doc,
	'svg': doc,
	'ttf': doc,
	'xps': doc,
    };
    
    var oembed = function(url) {
	for(var k in EMBED_MAPS) {
	    if(url.match(EMBED_MAPS[k][1])) {
		var oembed = EMBED_MAPS[k][0]+'?format=json&url='+encodeURIComponent(url);
		alert(oembed);
		jQuery.getJSON(oembed,function(json){
		// FIX THIS GOT STUCK ABOUT CROSS DOMAIN LIMITATIONS
			alert(json);
		    });
	    }
	}
    };    

    var extension = function(url) {
	return url.split('?')[0].toLowerCase().split('.').pop();
    };
    
    var expand_one = function(url) {
	// embed images, video, audio files
	var ext = extension(url);
	if(ext in EXTENSION_MAPS)
	    return EXTENSION_MAPS[ext](url);
	// then try ombed but first check in cache
	// var r = oembed(url);
	// if oembed service
	return '<a href="'+url+'s" class="autolink">'+url+'</a>';
    };
    
    jQuery('*','body').andSelf().not('a,img,embed,object,pre,code,audio,video').contents()
    .filter(function(){return this.nodeType === 3;})
    .replaceWith(function(){
	    var obj = jQuery(this);
	    var text = obj.text()
		if(text) {
		    text = text.replace(/http:\/\/\S*/g,
					function(match){
					    return expand_one(match);
					});
		};
	    return text;
	});
};

jQuery(function(){autolinks()});