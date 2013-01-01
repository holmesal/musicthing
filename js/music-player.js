changetrackinfo = function(player){
	
/* 	console.log($(player).children(".sc-info").children("h3").children("a").text()) */
	
	$(".info-track").text($(player).children(".sc-info").children("h3").children("a").text())
	console.log(art[0][idx].username)
	console.log(art[idx].username)
	$(".info-name").text(art[0][idx].username)
/* 	$(".info-name").text(curtrack.user.username) */
/* 	$(".info-city").text(track.title) */
}

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
	art.push(newdata)
	
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
/* 	console.log(idx) */
	offset = -400*idx - 200
	$(".player-container").animate({"margin-left":offset},{duration:400,queue:false});
	
	//fade out all controls
	$(".sc-player").not(player).children(".sc-controls").animate({opacity:0},{duration:400,queue:false});
	//fade in the controls
	$(player).children(".sc-controls").animate({opacity:1},{duration:400,queue:false});
	
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
	$('.sc-next').on("click",function(e) { 
		console.log("clicked!")
		$(this).parent().parent().next('.sc-player').children(".sc-info").click()
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