function calcpoke(){
	
	wide = $(window).width();
	
	if (wide < 500){
		wide = 500
	}
	
	poke = wide/2-250
	offset = -500*idx + poke
	$(".player-container").animate({"margin-left":offset},{duration:200,queue:false});
	$("#info-container").css("margin-left",poke)
	
	return poke
}

function setup_location_ui(location_enabled){
	
	if (location_enabled == true) {
    	
    	$("#location-select").show()
    	
	}
	
}

function setcoords(position){
     lat = position.coords.latitude;
     lon = position.coords.longitude;
     
     setup_location_ui(true)
     make_initial_request(true)
}

function geolocate(){

	if (navigator.geolocation) {
		navigator.geolocation.getCurrentPosition(setcoords);
	} else {
		error('Geo Location is not supported');
		setup_location_ui(false)
		make_initial_request(false)
	}

}

make_initial_request = function(location_enabled) {
		
	/*
if (location_enabled == true) {
    	
    	url = "/music/everything?geo_point="+lat+","+lon+"&radius="+$("#radius-slider").val()
    	
	} else {
    	
    	url = "/music/everything"
    	
	}
*/
	
	url = "/music/initialize"
	
	console.log(url)
	
	$.getJSON(url,function(data){
	    addtracks(data)
	    //first values
	    idx = 0
	    changetrackinfo($(".sc-player")[0])
	    $('.sc-controls').animate({opacity:1},200)
	    
/* 	    spinner.stop() */
	    $("#loading").hide()
	    
	    controllisteners()
    })
	
}

checkhttp = function(url){
	if (url.substring(0,1) == "@"){
		url = "http://www.twitter.com/" + url.substring(1)
	} else{
	
		if (url.substring(0,7) != "http://" && url.substring(0,8) != "https://"){
			url = "http://" + url
		}
	}
	
	
	
	return url
}

changetrackinfo = function(player){

	mixpanel.track("Track changed")
	
/* 	console.log($(player).children(".sc-info").children("h3").children("a").text()) */
	
	info = art[idx]
	console.log(info)
	
	url = 'http://api.soundcloud.com/tracks/'+info.track_id+'.json?client_id=d03ca49fb6764663d0992eadc69f8bf1'
	$.get(url,function(data){
		console.log(data)
		sc_url = data.permalink_url
		$('#scbtn').attr("href",sc_url)
		$(".info-track").text(data.title)
		
		//fade stuff in
		$("#info-row,#link-row").animate({opacity:1},{duration:200,queue:false});
	})
	
	
	
/* 	$(".info-track").text($(player).children(".sc-info").children("h3").children("a").text()) */
	console.log($(player).children(".sc-info").html())
/* 	console.log(art[0][idx].username) */
/* 	console.log(info.username) */
	$(".info-name").text(info.username)
	
	if (info.city != '' && info.city != 'None' && info.city != null){
		$(".info-city").text(info.city)
	} else{
		$(".info-city").text('Somewhere')
	}
	
	//empty the button container
	$('#link-row').empty()
	
	//append buttons as necessary
	if (info.bandcamp_url != '' && info.bandcamp_url != 'None' && info.bandcamp_url != null){
		url = checkhttp(info.bandcamp_url)
		$('#link-row').append('<p><a class="lead"  href="'+url+'" target="_blank"><img class="link-icon" src="/img/bandcamp.png">Download on Bandcamp</a></p>')
	}
	
	$('#link-row').append('<a class="lead"  id="scbtn" href="" target="_blank"><img class="link-icon" src="/img/soundcloud.png">Find on SoundCloud</a></p>')
	
	if (info.facebook_url != '' && info.facebook_url != 'None' && info.facebook_url != null){
		url = checkhttp(info.facebook_url)
		$('#link-row').append('<p><a class="lead"  href="'+url+'" target="_blank"><img class="link-icon" src="/img/facebook.png">Find on Facebook</a></p>')
	}
	
	if (info.twitter_url != '' && info.twitter_url != 'None' && info.twitter_url != null){
		url = checkhttp(info.twitter_url)
		$('#link-row').append('<p><a class="lead"  href="'+url+'" target="_blank"><img class="link-icon" src="/img/twitter.png">Follow on Twitter</a></p>')
	}
	
	if (info.myspace_url != '' && info.myspace_url != 'None' && info.myspace_url != null){
		url = checkhttp(info.myspace_url)
		$('#link-row').append('<p><a class="lead"  href="'+url+'" target="_blank"><img class="link-icon" src="/img/myspace.png">Find on Myspace</a></p>')
	}
	
	if (info.youtube_url != '' && info.youtube_url != 'None' && info.youtube_url != null){
		url = checkhttp(info.youtube_url)
		$('#link-row').append('<p><a class="lead"  href="'+url+'" target="_blank"><img class="link-icon" src="/img/youtube.png">Watch on Youtube</a></p>')
	}
	
	if (info.website_url != '' && info.website_url != 'None' && info.website_url != null){
		url = checkhttp(info.website_url)
		$('#link-row').append('<p><a class="lead"  href="'+url+'" target="_blank"><img class="link-icon" src="/img/website.png">Go to website</a></p>')
	}
	
	
	
	//go get the track info
	/*
url = 'http://api.soundcloud.com/tracks/'+info.track_id+'.json?client_id=d03ca49fb6764663d0992eadc69f8bf1'
	$.get(url,function(data){
		console.log(data)
		sc_url = data.permalink_url
		$('#scbtn').attr("href",sc_url)
	})
*/
	
	
	
	
}

bindoptions = function(){
	
	$("#expando-genre").collapse({toggle:false})
	$("#expando-radius").collapse({toggle:false})
	
	$("#genre").click(function(){
		$("#expando-genre").collapse('toggle')
		$("#expando-radius").collapse('hide')
		mixpanel.track("Genre dropdown link clicked")
	})
	
	$("#radius").click(function(){
		$("#expando-radius").collapse('toggle')
		$("#expando-genre").collapse('hide')
		mixpanel.track("Radius dropdown link clicked")
	})
	
}

flashhelp = function(){
	speed = 700
	
	$("#genre,#radius").css({"text-decoration":"underline"})
	
	$("#genre,#radius,.clickchange").pulse({opacity:1},{"pulses":2,"duration":1500,"returnDelay":1000},function(){
		$("#genre,#radius").css({"text-decoration":"underline"})
		$("#genre,#radius").animate({opacity:1})
	})
}

addtracks = function(data){
	
	console.log("loading tracks!")
	console.log(data)
	console.log(data.length)
	
	newlinks = []
	newdata = []
	
	//create and append html elements
	for (var i=0; i<data.length; i++){
		if (data[i].track_id != 'None' && data[i].track_id != null){
			console.log(data[i])
			
			newlinks.push('<a href="http://api.soundcloud.com/tracks/'+data[i].track_id+'" class="sc-player">some</a>')
/* 			newlinks.push('<a href="http://api.soundcloud.com/tracks/72232364" class="sc-player">http://api.soundcloud.com/tracks/72232364</a>') */
			
			newdata.push(data[i])
		}
		
	}
	
	console.log(newlinks)
	console.log(newdata)
	
	//add some links
	$('.player-container').append(newlinks)
	
	//add the data to the artists array
	art.push.apply(art,newdata)
	
	//increase the width of the player container to accomidate new players
	$('.player-container').css({width:500*$(".sc-player").length})
	
	
	console.log($("a.sc-player"))
	//covert these links into players
	$('a.sc-player').scPlayer();
	
	//rebind click events for players
	bindevents()
	
	
}

loadtracks = function(){
	
	if (latch == false){
		latch = true
		//go get more tracks
		$.getJSON('/music/gettracks',function(data){
			console.log(data)
			addtracks(data)
			latch = false
		})
	}
	
}

controllisteners = function(){
	//re-assign the next and prev listeners
	$("#btn-next").unbind().click(function(){
		$(".sc-player").eq(idx+1).children(".sc-artwork-list").click()
	})
	
	$("#btn-prev").unbind().click(function(){
		$(".sc-player").eq(idx-1).children(".sc-artwork-list").click()
	})
	
	curplay = $(".sc-player").eq(idx).children(".sc-controls").children(".sc-play")
	
	$("#btn-play").unbind().click(function(){
		$(curplay).click()
		$("#btn-play").hide()
		$("#btn-pause").show()
	})
	
	$("#btn-pause").unbind().click(function(){
		$(".sc-player").eq(idx).children(".sc-controls").children(".sc-pause").click()
		$("#btn-pause").hide()
		$("#btn-play").show()
	})
}

changetrack = function(player){
	//player is the track that was clicked on - the track to be played next
	console.log(player)
/* 	event.stopPropagation() */
	//show the play button on the current track
	$("#btn-play").hide()
	$("#btn-pause").show()
	
	//pause all currently playing tracks
	$('.sc-player.playing').children('.sc-controls').children('.sc-pause').click()
/* 	console.log($('player > a.sc-play')) */
	//play the next track
/* 	$('player > a.sc-play').click(); */
	$(player).children(".sc-controls").children(".sc-play").click()
	
	
	//slide the player
	idx = $(player).index()
	console.log(idx)
	console.log(poke)
	offset = -500*idx + poke
	$(".player-container").animate({"margin-left":offset},{duration:400,queue:false});
	
	//fade out all text info
	$("#info-row,#link-row").animate({opacity:0},{duration:100,queue:false});
	
	
/* 	$(".sc-player").not(player).children(".sc-controls").animate({opacity:0},{duration:400,queue:false}); */
	//fade in the controls
/* 	$(player).children(".sc-controls").animate({opacity:1},{duration:400,queue:false}); */
/* 	$(player).next().children(".sc-controls").animate({opacity:1},{duration:400,queue:false}); */
	
	if (idx!=0){
		$("#btn-prev").css({opacity:1})
	} else{
		$("#btn-prev").css({opacity:0.420})
	}
	
/*
	//all play buttons fire trackchanged except for the current one
	allelse = $('.sc-play').not(curplay)
	$(allelse).unbind().click(function(){
		console.log(this.parentNode.parentNode)
		changetrack(this.parentNode.parentNode)
	})
*/

	//change the track information
	changetrackinfo(player)
	//bind control listners
	controllisteners()
	
	
	if (idx > $(".sc-player").length-4){
		console.log("loading!")
		loadtracks()
	}
	
};

bindevents = function(){
	
	//click to change track
	$('.sc-artwork-list').on("click",function(e){
		console.log("changing track!")
/* 		console.log(this.parentNode) */
		changetrack(this.parentNode)
	});
	
	//next button listeners
	$('#next').on("click",function(e) { 
		console.log("clicked!")
		changetrack($('.player-container >')[idx+1])
/* 		elem = $(".sc-player")[idx+1] */
/* 		$(elem).children(".sc-controls").children(".sc-play").click() */
	});
	
	//next button listeners
	$('#prev').on("click",function(e) { 
		console.log("clicked!")
		changetrack($('.player-container >')[idx-1])
/* 		elem = $(".sc-player")[idx+1] */
/* 		$(elem).children(".sc-controls").children(".sc-play").click() */
	});
	
	$("#genre,#radius").hover(function(){
		$(".clickchange").animate({opacity:1},200)
	},function(){
		$(".clickchange").animate({opacity:0},200)
	})
	
	/*
$(document).bind('onMediaTimeUpdate.scPlayer', function(event){
	  console.log(event.target, 'the track is at ' + event.position + ' out of ' + event.duration + ' which is ' + event.relative + ' of the total');
	});
*/
	
/*
	$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
		
		console.log("track switch detected")
		player = $('.sc-player.playing')
		console.log(player)
		
		changetrack(player)
		
		
	});
*/
	
	/*
$(document).bind('onPlayerPause.scPlayer', function(event){
	  console.log(event.target, 'it stopped!');
	});
*/
	
}

$(document).ready(function() {
	
	//inites
	idx = 0
	latch = false
  
	//bind click events for players
	bindevents()
	
	//bind click events for options
	bindoptions()
	
	//flash the help text
	flashhelp()
  
  
});