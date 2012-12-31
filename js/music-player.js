loadtracks = function(){
	
	//
	
	
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
	offset = -400*idx - 200
	$(".player-container").animate({"margin-left":offset},400);
	
	//fade out all controls
	$(".sc-player").not(player).children(".sc-controls").animate({opacity:0});
	//fade in the controls
	$(player).children(".sc-controls").animate({opacity:1});
	
	//check if on last track - time to refresh
	//do this 2 tracks before the end
	
	console.log(idx)
	console.log($(".sc-player").length)
	
	if (idx > $(".sc-player").length-3){
		console.log("loading!")
		loadtracks()
	}
};

bindevents = function(){
	
	//click to change track
	$('.sc-player').on("click",function(){
		changetrack(this)
	});
	
	//next button listeners
	$('.sc-next').on("click",function() { 
		console.log("clicked!")
		$(this).parent().parent().next().children('.sc-trackslist').children('.active').click()
	});
	
	/*
$(document).bind('onMediaTimeUpdate.scPlayer', function(event){
	  console.log(event.target, 'the track is at ' + event.position + ' out of ' + event.duration + ' which is ' + event.relative + ' of the total');
	});
*/
	
	/*
$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
	  console.log(event.target, 'it jumped to this track:', track);
	});
*/
	
	/*
$(document).bind('onPlayerPause.scPlayer', function(event){
	  console.log(event.target, 'it stopped!');
	});
*/
	
}

$(document).ready(function() {
	
	idx = 0
  
	//bind click events for players
	bindevents()
  
  
});