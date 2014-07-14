$('#loading-example-btn').click(function () {
  var protocol = /^(https?|ftp):\/\//;
	var url = encodeURIComponent($('#url').val())


	$(location).attr('href', "/"+url);
});
