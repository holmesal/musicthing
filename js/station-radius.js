setcoords = function(position){
     lat = position.coords.latitude;
     lon = position.coords.longitude;
     
     log(lat + "," + lon)
     
     loadcities("location")
}

geolocate = function(){
	
	log(1234)

	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(setcoords)
	} else {
		error('Geo Location is not supported');
		setup_location_ui(false)
		make_initial_request(false)
	}

}

binsearch = function(array,target){
	
	trans = []
	$(array).each(function(idx,elem){
/*
		log(elem)
		log(target)
*/
		if (elem > target){trans[idx]=1}else{trans[idx]=0}
		
	})
/* 	log(trans) */
	
	low = 0; 
	high = trans.length;
	while (low != high) {
	    mid = Math.floor((low + high) / 2); // Or a fancy way to avoid int overflow
/*
	    log("low "+low)
	    log("high "+high)
	    log("mid "+mid)
*/
	    if (trans[mid] < 1) {
	        
	        low = mid + 1.
	    }
	    else {
	        
	        high = mid;
	    }
	}
/* 	log(low-high) */
	return low
}

log = function(input){console.log(input)}

plotcities = function(){
	log("plotting cities...")
	$(cities.reverse()).each(function(idx,elem){	//reversing once here
		if (idx%2 == 0){
			side = "left"
		} else{
			side = "right"
		}
		
		html_string = '<div class="city-row city-'+side+'"><div class="circle circle-'+side+'"></div><span class="city-text">'+elem.name+'</span></div>'
		
		$("#city-container").append(html_string)
	})
	
	$("#city-container").append('<div class="buffer"></div>')
	
	
	//get the centers of each circle
	log("getting centers...")
	ycenters = []
	$(".circle").each(function(){
		ycenter = $("#city-container").height() - ($(this).position().top + $(this).height())
		ycenters.push(ycenter)
	})
	ycenters.push(0)
	ycenters.reverse()
	
	dstarts = [0]
	//get the starting values
	$(cities.reverse()).each(function(idx,elem){	//reversing again here, back to normal (small d to large d)
		dstart = elem.distance
		dstarts.push(dstart)
	})
	
/* 	log(dstarts) */
	
	//get the pixel-to-miles conversion
	log("getting miles per pixel factor...")
	mpxs = []
	for (var i=0;i<dstarts.length-1;i++){
		dpx = ycenters[i+1] - ycenters[i]
		dmi = dstarts[i+1] - dstarts[i]
		
		mpx = dmi/dpx
		mpxs.push(mpx)
	}
	
	 
	
}

dragged = function(event,ui){
/* 	console.log(event) */
	yc = $(".radiusblock").height() - ui.position.top - $("#draggable").height()/2
/* 	console.log(yc) */
	$(".pixels").text(yc)
	$("#overlay").height(yc)
	//want to make the whole thing draggable (not just the 100px height element). however, draggable gets stuck (constrained inside parent element, can't drag down)
/* 	$("#draggable").height(yc) */
	
	//which slot?
/*
	log(yc)
	log(ycenters)
*/
	idx_slot = binsearch(ycenters,yc) - 1
/* 	log(idx_slot) */
	
	//get current height in pixels
	fpx = yc-ycenters[idx_slot]
/*
	log(fpx)
	log(mpx[idx_slot])
*/
	mi = fpx * mpxs[idx_slot] + dstarts[idx_slot]
	
	if (idx_slot == ycenters.length-1){
		$(".miles").text(Math.floor(dstarts[dstarts.length-1]))
	} else{
		$(".miles").text(Math.floor(mi))
	}
	
}

recalc_cities = function(event,ui){
	//recalculate the cities
/*
	log(event)
	log(ui)
	log(ycenters)
	log(ui.position.top)
*/
}

initdragger = function(){
	$( "#draggable" ).draggable({
		drag: function(event,ui){
			dragged(event,ui)
		},
		stop: function(event,ui){
			recalc_cities(event,ui)
		},
		containment: "parent"
	});
	
	//fix
	var divTop = $("#top").height();

	$(window).bind('resize', function(e) {
		e.preventDefault()
		e.stopPropagation()
		console.log($(window).height())
		console.log($(document).height())
	});
}

register_autocomplete = function(){
	
	//prevent enter
	$(window).keydown(function(event){
		if(event.keyCode == 13) {
			event.preventDefault();
			return false;
		}
	});
	
	//register
	var input = document.getElementById('location_string');
	var options = {
	  types: ['(cities)']
	};
	
	autocomplete = new google.maps.places.Autocomplete(input, options);
	
	//register the listeners for the place_changed event
	google.maps.event.addListener(autocomplete, 'place_changed', function() {
	
	  	var place = autocomplete.getPlace();
	  	
	  	//empty so there are no ghosts. boo!
/* 	  	$("#location_string").val("") */
	  	$("#locality").val("")
	  	$("#administrative_area_level_1").val("")
	  	$("#country").val("")
	  	$("#lat").val("")
	  	$("#lon").val("")
	  	
	  	console.log(place.address_components)
	  	
	  	//set the location string
/* 	  	$("#location_string").val($("#autocomplete").val()) */
	  	
	  	$.each(place.address_components,function(idx,comp){
		  	
		  	//check if type, and do stuff
		  	$.each(comp.types,function(idx_comp,type_comp){
			  	if (type_comp == "locality"){
				  	$("#locality").val(comp.long_name)
			  	} else if (type_comp == "administrative_area_level_1"){
				  	$("#administrative_area_level_1").val(comp.long_name)
			  	} else if (type_comp == "country"){
				  	$("#country").val(comp.long_name)
			  	}
			  	
		  	})
		  	
		  	if ($("#locality").val() == ""){
			  	$.each(comp.types,function(idx_comp,type_comp){
				  	if (type_comp == "administrative_area_level_3"){
					  	$("#locality").val(comp.long_name)
				  	}
			  	})
		  	}
		  	
		  	if ($("#locality").val() == ""){
			  	$.each(comp.types,function(idx_comp,type_comp){
				  	if (type_comp == "administrative_area_level_2"){
					  	$("#locality").val(comp.long_name)
				  	}
			  	})
		  	}
		  	
	  	})
	  	
	  	//change the button
  		$("#saveCity").text('Use '+$("#location_string").val())
	  	
	  	//grab the lat and lon
		$("#lat").val(place.geometry.location.Ya)
		$("#lon").val(place.geometry.location.Za)
	});

}

loadcities = function(mode){
	
	if (mode == "location"){
		log("loading cities via ajax...")
		data = {
			lat	:	lat,
			lon :	lon
		}
		
		log(data)
		$.getJSON('/music/get_radial_cities',data,function(d){
			spinner.stop()
			log(d.response)
			cities = d.response
			plotcities()
		})
	}
	
	
	
/* 	$.get('/music/get_radial_cities',) */
	
/*
	log("omg spoof")
	
	cities = [
		{
			"name"		:	"Boston",
			"distance"	:	1,
			"key"		:	1
		},
		{
			"name"		:	"Cambridge",
			"distance"	:	4,
			"key"		:	2
		},
		{
			"name"		:	"Waltham",
			"distance"	:	10,
			"key"		:	3
		},
		{
			"name"		:	"Revere",
			"distance"	:	14,
			"key"		:	4
		},
		{
			"name"		:	"Somerville",
			"distance"	:	15,
			"key"		:	5
		},
		{
			"name"		:	"Salem",
			"distance"	:	40,
			"key"		:	6
		},
		{
			"name"		:	"Rockport",
			"distance"	:	50,
			"key"		:	6
		},
		{
			"name"		:	"New York City",
			"distance"	:	300,
			"key"		:	6
		},
		{
			"name"		:	"Bellingham",
			"distance"	:	4000,
			"key"		:	6
		},
		{
			"name"		:	"San Francisco",
			"distance"	:	7000,
			"key"		:	6
		}
	]
*/
	
	
	
}

startspinner = function(){
	var opts = {
	  lines: 17, // The number of lines to draw
	  length: 2, // The length of each line
	  width: 2, // The line thickness
	  radius: 40, // The radius of the inner circle
	  corners: 1, // Corner roundness (0..1)
	  rotate: 0, // The rotation offset
	  color: '#000', // #rgb or #rrggbb
	  speed: 1.4, // Rounds per second
	  trail: 100, // Afterglow percentage
	  shadow: false, // Whether to render a shadow
	  hwaccel: true, // Whether to use hardware acceleration
	  className: 'spinner', // The CSS class to assign to the spinner
	  zIndex: 2e9, // The z-index (defaults to 2000000000)
	  top: 'auto', // Top position relative to parent in px
	  left: 'auto' // Left position relative to parent in px
	};
	var target = document.getElementById('city-container');
	spinner = new Spinner(opts).spin(target);
	}

$(document).ready(function() {
	
	//start spinner
	startspinner()
	
	//geolocate
	geolocate()
	
	//register the collapse
	$(".chooselocation").collapse('hide')
	//register the trigger
	$("#btnchoose").click(function(){
		$(".chooselocation").collapse('show')
		$("#btnchoose, #btnchoose-text,#btnSave").hide()
	})
	
	//register the autocomplete
	register_autocomplete()
	
	//register the choose city button
	$("#saveCity").click(function(){
		$(".chooselocation").collapse('hide')
		$("#btnchoose, #btnchoose-text,#btnSave").show()
		$("#btnchoose").text($("#location_string").val())
		
		//go load new cities
		loadcities()
	})
	
	//initialize the draggable
	initdragger()
	
});