$.get('https://api.soundcloud.com/users/4260804/tracks.json?client_id=d03ca49fb6764663d0992eadc69f8bf1', function(data) {
  console.log(data)
  for (var key in data){
	  var track = data[key];
	  console.log(track.artwork_url)
	  $('div:.sc-player').append('<a href="'+track.permalink_url+'" class="sc-player">My dub track</a>')
  }
  
  var head= document.getElementsByTagName('head')[0];
   var script= document.createElement('script');
   script.type= 'text/javascript';
   script.src= '/js/sc-player.js';
   head.appendChild(script);
  
});