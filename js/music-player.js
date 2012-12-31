bindoptions = function(){
	
	$("#expando-genre").collapse({toggle:false})
	$("#expando-radius").collapse({toggle:false})
	
	$("#genre").click(function(){
		$("#expando-genre").collapse('toggle')
		$("#expando-radius").collapse('hide')
	})
	
	$("#radius").click(function(){
		$("#expando-radius").collapse('toggle')
		$("#expando-genre").collapse('hide')
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

addtracks = function(artists){
	
	newlinks = []
	newdata = []
	
	//create and append html elements
	for (var i=0; i<artists.length-1; i++){
		console.log(artists[i])
		
		newlinks.push('<a href="http://api.soundcloud.com/tracks/'+artists[i].track_id+'" class="sc-player"></a>')
		newdata.push(artists[i])
		
	}
	
	console.log(newlinks)
	console.log(newdata)
	
	//add some links
	$('.player-container').append(newlinks)
	
	//increase the width of the player container to accomidate new players
	$('.player-container').css({width:400*$(".sc-player").length})
	
	//covert these links into players
	$('a.sc-player').scPlayer();
	
	//rebind click events for players
	bindevents()
	
	
}

loadtracks = function(){
	
	//go get more tracks
	$.get('/music/gettracks',function(data){
		console.log(data)
		addtracks(data)
	})

/* 	addtracks(spoofart) */
	
/*
	//spoof some links
	links = ['<a href="http://api.soundcloud.com/tracks/71127918" class="sc-player">Forss</a>','<a href="http://soundcloud.com/matas/the-pendulum" class="sc-player">Forss</a>','<a href="http://soundcloud.com/matas/communion-of-coincidence-from-the-mountain-top" class="sc-player">My dub track</a>','<a href="http://soundcloud.com/matas/anadrakonic-waltz" class="sc-player">Pumpkins Track</a>','<a href="http://soundcloud.com/matas/frost-theme-0-1" class="sc-player">Oxxo</a>']
	
	//add some links
	$('.player-container').append(links)
	
	//increase the width of the player container to accomidate new players
	$('.player-container').css({width:400*$(".sc-player").length})
	
	//covert these links into players
	$('a.sc-player').scPlayer();
	
	//rebind click events for players
	bindevents()
*/
	
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
	
	//check if on last track - time to refresh
	//do this 2 tracks before the end
	
	console.log(idx)
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
	$('.sc-next').on("click",function(e) { 
		console.log("clicked!")
		$(this).parent().parent().next('.sc-player').children(".sc-info").click()
	});
	
	/*
$(document).bind('onMediaTimeUpdate.scPlayer', function(event){
	  console.log(event.target, 'the track is at ' + event.position + ' out of ' + event.duration + ' which is ' + event.relative + ' of the total');
	});
*/
	
	$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
		
		curtrack = track
	});
	
	/*
$(document).bind('onPlayerPause.scPlayer', function(event){
	  console.log(event.target, 'it stopped!');
	});
*/
	
}

$(document).ready(function() {
	
	//inites
	idx = 0
  
	//bind click events for players
	bindevents()
	
	//bind click events for options
	bindoptions()
	
	//flash the help text
	flashhelp()
  
  
});