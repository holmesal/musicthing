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
	
	$(".info-track").text($(player).children(".sc-info").children("h3").children("a").text())
/* 	console.log(art[0][idx].username) */
/* 	console.log(info.username) */
	$(".info-name").text(info.username)
	
	if (info.city != '' && info.city != 'None' && info.city != null){
		$(".info-city").text(info.city)
	} else{
		$(".info-city").text('Somewhere')
	}
	
	//empty the button container
	$('.buttoncontainer').empty()
	
	//append buttons as necessary
	if (info.bandcamp_url != '' && info.bandcamp_url != 'None' && info.bandcamp_url != null){
		url = checkhttp(info.bandcamp_url)
		$('.buttoncontainer').append('<a href="'+url+'" target="_blank"><img class="ext-button" src="/img/bandcamp.png"></a>')
	}
	
	if (info.facebook_url != '' && info.facebook_url != 'None' && info.facebook_url != null){
		url = checkhttp(info.facebook_url)
		$('.buttoncontainer').append('<a href="'+url+'" target="_blank"><img class="ext-button" src="/img/facebook.png"></a>')
	}
	
	if (info.twitter_url != '' && info.twitter_url != 'None' && info.twitter_url != null){
		url = checkhttp(info.twitter_url)
		$('.buttoncontainer').append('<a href="'+url+'" target="_blank"><img class="ext-button" src="/img/twitter.png"></a>')
	}
	
	if (info.myspace_url != '' && info.myspace_url != 'None' && info.myspace_url != null){
		url = checkhttp(info.myspace_url)
		$('.buttoncontainer').append('<a href="'+url+'" target="_blank"><img class="ext-button" src="/img/myspace.png"></a>')
	}
	
	if (info.youtube_url != '' && info.youtube_url != 'None' && info.youtube_url != null){
		url = checkhttp(info.youtube_url)
		$('.buttoncontainer').append('<a href="'+url+'" target="_blank"><img class="ext-button" src="/img/youtube.png"></a>')
	}
	
	if (info.website_url != '' && info.website_url != 'None' && info.website_url != null){
		url = checkhttp(info.website_url)
		$('.buttoncontainer').append('<a href="'+url+'" target="_blank"><img class="ext-button" src="/img/website.png"></a>')
	}
	
	$('.buttoncontainer').append('<a id="scbtn" href="" target="_blank"><img class="ext-button" src="/img/soundcloud.png"></a>')
	
	//go get the link
	url = 'http://api.soundcloud.com/tracks/'+info.track_id+'.json?client_id=d03ca49fb6764663d0992eadc69f8bf1'
	$.get(url,function(data){
		sc_url = data.permalink_url
		$('#scbtn').attr("href",sc_url)
	})
	
	
	
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
		$("#genre,#radius").css({"text-decoration":"none"})
		$("#genre,#radius").animate({opacity:1})
	})
}

addtracks = function(data){
	
	console.log("loading tracks!")
	console.log(data)
	
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
	$('.player-container').css({width:400*$(".sc-player").length})
	
	
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

changetrack = function(player){
	//player is the track that was clicked on - the track to be played next
	console.log(player)
	
	//pause all currently playing tracks
	$('.sc-player.playing > a.sc-pause').click();
	//play the next track
	$('player > a.sc-play').click();
	
	
	//slide the player
	idx = $(player).index()
	console.log(idx)
	offset = -400*idx - 200
	$(".player-container").animate({"margin-left":offset},{duration:400,queue:false});
	
	//fade out all controls
	$(".sc-player").not(player).children(".sc-controls").animate({opacity:0},{duration:400,queue:false});
	//fade in the controls
	$(player).children(".sc-controls").animate({opacity:1},{duration:400,queue:false});
	$(player).next().children(".sc-controls").animate({opacity:1},{duration:400,queue:false});
	
	if (idx!=0){
		$(player).next().children(".sc-controls").animate({opacity:1},{duration:400,queue:false});
	}
	
	//change the track information
	changetrackinfo(player)
	
	//check if on last track - time to refresh
	//do this 2 tracks before the end
	
/* 	console.log(idx) */
/* 	console.log($(".sc-player").length) */
	
	if (idx > $(".sc-player").length-3){
		console.log("loading!")
		loadtracks()
	}
	
};

bindevents = function(){
	
	//click to change track
	$('.sc-player').on("click",function(e){
		console.log("changing track!")
		changetrack(this)
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
	
	/*
$(document).bind('onMediaTimeUpdate.scPlayer', function(event){
	  console.log(event.target, 'the track is at ' + event.position + ' out of ' + event.duration + ' which is ' + event.relative + ' of the total');
	});
*/
	
/*
	$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
		
		if (first_track == null){
			first_track = track
		}
		
		curtrack = track
		
		console.log(first_track)
		
		//fade out the track info
		$(".trackinfo").animate({opacity:0},200,function(){
			//change the track info
			changetrackinfo()
		});
		
		//fade in the track info
		$(".trackinfo").delay(300).animate({opacity:1},{duration:200,queue:true});
		
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