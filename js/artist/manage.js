$(document).ready(function(){


	/* 	72047558 */
	mixpanel.track("band manage page loaded")
	
	//register signup
	mixpanel.track_links("#choosenew","manage choose new button clicked");
	mixpanel.track_links("#scupload","manage soundcloud upload button clicked");
	
	console.log("{{artist.track_id}}")
	
	if ("{{artist.track_id}}" == "None"){
		window.location = '/artist/choosetrack'
	};
	
	
	//get track stuff from soundcloud
	$.get('https://api.soundcloud.com/tracks/{{artist.track_id}}.json?client_id=d03ca49fb6764663d0992eadc69f8bf1', function(data) {
		
		$(".artist_name").text(data.user.username)
		$(".track_name").text(data.title)
		
		var artwork = data.artwork_url
		var artwork_src = "track"
	/* 		console.log(data) */
	/* 		console.log(artwork) */
		
		if (artwork == null){
			if (data.user.avatar_url.indexOf("default_avatar") == -1){
				artwork = data.user.avatar_url
				artwork_src = "avatar"
			}
		}
		
	/* 		console.log(artwork) */
		
		if (artwork == null){
			artwork = "/img/noartwork.jpg"
			artwork_src = "fallback"
		}else{
	/* 			console.log(artwork) */
			artwork = artwork.replace("large","t300x300")
	/* 			console.log(artwork) */
		}
		
		mixpanel.track("manage track loaded",{"artwork source":artwork_src})
		
		
		
		$('.artwork').css("background-image","url("+artwork+")")
		
	/* 		console.log(data) */
	/*
	  for (var key in data){
		  var track = data[key];
		  console.log(track.artwork_url)
		  $('div:.sc-player').append('<a href="'+track.permalink_url+'" class="sc-player"></a>')
	  }
	*/
	  
	});
	
	//start the autocomplete rolling
	var input = document.getElementById('city');
	var options = {
	  types: ['(cities)']
	};
	
	autocomplete = new google.maps.places.Autocomplete(input, options);
	
	//register the listeners for the place_changed event
	google.maps.event.addListener(autocomplete, 'place_changed', function() {
	  	var place = autocomplete.getPlace();
	  	
	  	//empty so there are no ghosts. boo!
	  	$("#locality").val("")
	  	$("#administrative_area_level_1").val("")
	  	$("#country").val("")
	  	$("#lat").val("")
	  	$("#lon").val("")
	  	
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
		  	
	  	})
	  	
	  	//grab the lat and lon
		$("#lat").val(place.geometry.location.Ya)
		$("#lon").val(place.geometry.location.Za)
	});

});