$(document).ready(function() {
    $('#match-form').on('submit', function(e) {
        e.preventDefault();
        var formData = new FormData(this);
        $('#loader').show();
        $('#match-results').hide();

        $.ajax({
            url: '/match',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(data) {
                $('#loader').hide();
                $('#match-results').show();
                var resultsHtml = '';
                data.match_results.forEach(function(job) {
                    resultsHtml += '<div class="card mb-3">';
                    resultsHtml += '<div class="card-body">';
                    resultsHtml += '<h5 class="card-title">' + job.title + '</h5>';
                    resultsHtml += '<h6 class="card-subtitle mb-2 text-muted">' + job.company + ' - ' + job.location + '</h6>';
                    resultsHtml += '<p class="card-text"><strong>Deadline:</strong> ' + job.deadline + '</p>';
                    resultsHtml += '<p class="card-text">' + job.match_details + '</p>';
                    resultsHtml += '</div></div>';
                });
                $('#match-results').html(resultsHtml);
            },
            error: function(data) {
                $('#loader').hide();
                $('#match-results').show();
                $('#match-results').text('An error occurred: ' + data.responseJSON.error);
            }
        });
    });
});

