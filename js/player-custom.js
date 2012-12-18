$(document).bind('onPlayerTrackSwitch.scPlayer', function(event, track){
/*   console.log(event.target, 'it jumped to this track:', track); */
	elem = $('a[href$='+track.permalink+']'.parent().parent())
	console.log(elem.parent().parent())
});