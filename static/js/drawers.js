/**

   Created and copyrighted by Massimo Di Pierro <massimo.dipierro@gmail.com> 
   (MIT license)        
   
   Example:
   
   <script src="drawers.js?left_url=http://web2py.com&left_label=Tags&right_url=http://example.com"></script>
**/

jQuery(function(){
	var script_source = jQuery('script[src*="drawers.js"]').attr('src');
	var params = function(name,default_value) {
	    var match = RegExp('[?&]' + name + '=([^&]*)').exec(script_source);
	    return match && decodeURIComponent(match[1].replace(/\+/g, ' '))||default_value;
	}
	var left_url = params('left_url');
	var left_label = params('left_label','');
	var right_url = params('right_url');
	var right_label = params('right_label','');
	var make_drawer = function(left,label,src) {
	    var right = (left=='left')?'right':'left';
	    var tbar = '<div id="w2drawer'+left+'"><span>'+label+'</span><iframe src="'+src+'"/></iframe></div>';
	    jQuery('body').append(tbar);
	    var st = jQuery('#w2drawer'+left);
	    var sign = (right=='right')?'':'-';
	    st.css({'opacity':'.7','background':'#FFF','border':'solid 1px #666','border-width':'1px 0 0 1px','height':'20px','width':'40px','position':'fixed','bottom':'0','padding':'2px 5px','overflow':'hidden','-moz-box-shadow':''+sign+'3px -3px 3px rgba(0,0,0,0.5)','-webkit-box-shadow':''+sign+'3px -3px 3px rgba(0,0,0,0.5)','box-shadow':''+sign+'3px -3px 3px rgba(0,0,0,0.5)','z-index':3000});
	    st.css((''+left),'0').css('-webkit-border-top-'+right+'-radius','12px').css('-moz-border-radius-top'+right,'12px').css('border-top-'+right+'-radius','12px')
	    st.find('span').css({'width':'100%','text-align':right,'float':right,'margin':'2px 3px','text-shadow':'1px 1px 1px #FFF','color':'#444','font-size':'12px','line-height':'1em'});
	    st.find('iframe').css({'border':0,'margin':0,'width':'100%','height':'100%','background-repeat': 'no-repeat','background-position': '50% 50%'}).attr('scrolling','auto');
	    st.find('iframe').hide();
	    // hover
	    st.click(function(){
		    jQuery(this).animate({height:'50%', width:'80%', opacity: 0.95}, 300);
		    st.find('iframe').show();
		});
	    //leave
	    st.mouseleave(function(){ 
		    st.animate({height:'20px', width: '40px', opacity: .7}, 300); 
		    st.find('iframe').hide();
		});
	}
	left_url&&make_drawer('left',left_label,left_url);
	right_url&&make_drawer('right',right_label,right_url);
    });
